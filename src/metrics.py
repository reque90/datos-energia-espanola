"""
Cálculo de métricas a partir de data/processed/electricidad_horaria.csv.

Salidas en data/processed/:
- metricas_anuales.csv    (una fila por año)
- metricas_mensuales.csv  (una fila por año-mes)
- bateria_diaria.csv      (una fila por día: ingreso de una batería de 1 MW / 4 MWh)
- perfil_hora_mes.csv     (precio y solar medios por año, mes y hora -> mapa de calor)
"""

import pandas as pd

import config


def metricas_grupo(g: pd.DataFrame) -> pd.Series:
    """Métricas de precio y solar para un grupo de horas (un año o un mes)."""
    precio = g["precio_eur_mwh"]
    solar = g["solar_mwh"]

    # Precio capturado solar: media del precio ponderada por la producción solar
    con_solar = solar.notna() & precio.notna()
    energia_solar = solar[con_solar].sum()
    if energia_solar > 0:
        capturado = (precio[con_solar] * solar[con_solar]).sum() / energia_solar
        baseload_mismas_horas = precio[con_solar].mean()
        capture_rate = capturado / baseload_mismas_horas
        solar_gwh = energia_solar / 1000
    else:
        capturado = capture_rate = solar_gwh = float("nan")

    return pd.Series({
        "precio_baseload": precio.mean(),
        "precio_capturado_solar": capturado,
        "capture_rate": capture_rate,
        "pct_horas_cero_o_negativo": (precio <= 0).mean() * 100,
        "pct_horas_negativo": (precio < 0).mean() * 100,
        "solar_gwh": solar_gwh,
        "horas": len(g),
    })


def bateria_diaria(horario: pd.DataFrame) -> pd.DataFrame:
    """
    Arbitraje diario simplificado de una batería:
    - carga en las N horas más baratas del día y descarga en las N más caras (N = 4).
    - margen = ingresos de descarga - coste de carga (hay que comprar 1/eficiencia más energía).
    - si el margen es negativo, ese día la batería no opera (margen = 0).
    Limitación: no se exige que las horas de carga vayan antes que las de descarga.
    """
    n = config.BATERIA_HORAS
    potencia = config.BATERIA_POTENCIA_MW
    eficiencia = config.BATERIA_EFICIENCIA

    filas = []
    for fecha, g in horario.groupby("fecha"):
        precios = g["precio_eur_mwh"].dropna().sort_values()
        if len(precios) < 2 * n:
            continue
        carga = precios.head(n).mean()
        descarga = precios.tail(n).mean()
        margen = descarga * n * potencia - carga * n * potencia / eficiencia
        filas.append({
            "fecha": fecha,
            "anio": int(fecha[:4]),
            "mes": int(fecha[5:7]),
            "precio_carga": carga,
            "precio_descarga": descarga,
            "spread": descarga - carga,
            "margen_eur_por_mw": max(margen, 0.0) / potencia,
            "opera": margen > 0,
        })
    return pd.DataFrame(filas)


def main() -> None:
    horario = pd.read_csv(config.DATA_PROCESSED / "electricidad_horaria.csv")

    # --- Batería ---
    bateria = bateria_diaria(horario)
    bateria.round(4).to_csv(config.DATA_PROCESSED / "bateria_diaria.csv", index=False)

    # --- Métricas anuales ---
    anual = horario.groupby("anio").apply(metricas_grupo, include_groups=False).reset_index()
    anual["horas"] = anual["horas"].astype(int)
    anual["anio_completo"] = anual["horas"] >= 8760
    ingreso_anual = (bateria.groupby("anio")
                            .agg(ingreso_bateria_eur_por_mw=("margen_eur_por_mw", "sum"),
                                 dias_opera_bateria=("opera", "sum"))
                            .reset_index())
    anual = anual.merge(ingreso_anual, on="anio", how="left")
    anual.round(4).to_csv(config.DATA_PROCESSED / "metricas_anuales.csv", index=False)

    # --- Métricas mensuales ---
    mensual = horario.groupby(["anio", "mes"]).apply(metricas_grupo, include_groups=False).reset_index()
    mensual["horas"] = mensual["horas"].astype(int)
    # Primer día del mes como fecha, útil como eje temporal en Power BI
    mensual["fecha_mes"] = pd.to_datetime(dict(year=mensual["anio"], month=mensual["mes"], day=1)).dt.strftime("%Y-%m-%d")
    ingreso_mensual = (bateria.groupby(["anio", "mes"])
                              .agg(ingreso_bateria_eur_por_mw=("margen_eur_por_mw", "sum"),
                                   dias_opera_bateria=("opera", "sum"))
                              .reset_index())
    mensual = mensual.merge(ingreso_mensual, on=["anio", "mes"], how="left")
    mensual.round(4).to_csv(config.DATA_PROCESSED / "metricas_mensuales.csv", index=False)

    # --- Perfil hora x mes (mapa de calor) ---
    perfil = (horario.groupby(["anio", "mes", "hora"])
                     .agg(precio_medio=("precio_eur_mwh", "mean"),
                          solar_media_mwh=("solar_mwh", "mean"))
                     .reset_index())
    perfil.round(4).to_csv(config.DATA_PROCESSED / "perfil_hora_mes.csv", index=False)

    print(f"Métricas calculadas: {len(anual)} años, {len(mensual)} meses, {len(bateria)} días de batería")


if __name__ == "__main__":
    main()

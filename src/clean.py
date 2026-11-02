"""
Limpieza y preparación de los datos.

Entradas:  data/raw/omie/marginalpdbc_*      (precios de OMIE)
           data/raw/energy_charts/AAAA-MM.csv (solar y demanda de Energy-Charts)
           data/raw/redata/AAAA.csv           (solar diaria oficial de REE, para validar)
Salidas:   data/processed/precios_periodos.csv         (granularidad original de OMIE)
           data/processed/electricidad_horaria.csv     (una fila por hora, con solar y demanda)
           data/processed/validacion_solar_diaria.csv  (solar diaria Energy-Charts vs. REE)
           docs/calidad_datos.md                       (informe de calidad generado automáticamente)
"""

import pandas as pd

import config

ZONA = config.ZONA_HORARIA


# ---------------------------------------------------------------------------
# 1. Lectura de OMIE
# ---------------------------------------------------------------------------
def leer_fichero_omie(ruta) -> list[list]:
    """
    Lee un fichero marginalpdbc. Formato:
        MARGINALPDBC;                      <- cabecera
        2024;01;01;1;63.33;63.33;          <- año;mes;día;periodo;precio_PT;precio_ES;
        *                                  <- fin de fichero
    """
    filas = []
    texto = ruta.read_text(encoding="latin-1")
    for linea in texto.splitlines():
        partes = linea.strip().split(";")
        # Las líneas de datos tienen al menos 6 campos y empiezan por un año
        if len(partes) < 6 or not partes[0].isdigit():
            continue
        anio, mes, dia, periodo, precio_pt, precio_es = partes[:6]
        filas.append([anio, mes, dia, periodo, precio_pt, precio_es])
    return filas


def leer_omie() -> pd.DataFrame:
    """Lee todos los ficheros de OMIE en un único DataFrame con los tipos correctos."""
    # Puede haber varias versiones de un mismo día (marginalpdbc_AAAAMMDD.1, .2...).
    # Nos quedamos con la versión más alta, que es la corrección más reciente.
    ultima_version = {}
    for ruta in config.RAW_OMIE.glob("marginalpdbc_*.*"):
        dia, _, version = ruta.name.removeprefix("marginalpdbc_").partition(".")
        if len(dia) == 8 and version.isdigit():
            if dia not in ultima_version or int(version) > int(ultima_version[dia].suffix[1:]):
                ultima_version[dia] = ruta
    ficheros = [ultima_version[dia] for dia in sorted(ultima_version)]
    if not ficheros:
        raise FileNotFoundError("No hay ficheros de OMIE. Ejecuta antes download_omie.py")

    filas = []
    for ruta in ficheros:
        filas.extend(leer_fichero_omie(ruta))

    df = pd.DataFrame(filas, columns=["anio", "mes", "dia", "periodo", "precio_pt", "precio_es"])

    # Conversión de tipos (errors="coerce" convierte lo que no sea número en nulo)
    df["fecha"] = pd.to_datetime(
        dict(year=df["anio"].astype(int), month=df["mes"].astype(int), day=df["dia"].astype(int))
    )
    df["periodo"] = df["periodo"].astype(int)
    df["precio_pt"] = pd.to_numeric(df["precio_pt"].str.replace(",", "."), errors="coerce")
    df["precio_es"] = pd.to_numeric(df["precio_es"].str.replace(",", "."), errors="coerce")
    return df[["fecha", "periodo", "precio_es", "precio_pt"]]


# ---------------------------------------------------------------------------
# 2. Limpieza de los periodos de OMIE
# ---------------------------------------------------------------------------
def horas_del_dia(fechas: pd.Series) -> pd.Series:
    """
    Horas reales de cada día en hora local (23, 24 o 25).
    Se calcula restando la medianoche del día siguiente menos la de este día,
    ambas en hora de Madrid. Así se tienen en cuenta los cambios de hora.
    """
    medianoche = fechas.dt.tz_localize(ZONA)
    medianoche_siguiente = (fechas + pd.Timedelta(days=1)).dt.tz_localize(ZONA)
    return (medianoche_siguiente - medianoche).dt.total_seconds() / 3600


def limpiar_periodos(df: pd.DataFrame, calidad: dict) -> pd.DataFrame:
    """Filtra el periodo, elimina duplicados, calcula el inicio UTC de cada periodo y valida."""
    calidad["filas_leidas"] = len(df)

    # Filtrar el periodo de estudio
    df = df[(df["fecha"] >= config.FECHA_INICIO) & (df["fecha"] <= config.FECHA_FIN)].copy()

    # Duplicados por (fecha, periodo)
    calidad["duplicados"] = int(df.duplicated(["fecha", "periodo"]).sum())
    df = df.drop_duplicates(["fecha", "periodo"]).sort_values(["fecha", "periodo"])

    # Nulos en el precio de España
    calidad["precios_nulos"] = int(df["precio_es"].isna().sum())

    # Duración del periodo por día: 90 periodos o más => 15 minutos; si no, 60 minutos
    periodos_por_dia = df.groupby("fecha")["periodo"].transform("count")
    df["duracion_min"] = (periodos_por_dia >= 90).map({True: 15, False: 60})

    # Instante de inicio en UTC = medianoche local (pasada a UTC) + (periodo - 1) x duración
    medianoche_utc = df["fecha"].dt.tz_localize(ZONA).dt.tz_convert("UTC")
    desfase = pd.to_timedelta((df["periodo"] - 1) * df["duracion_min"], unit="min")
    df["inicio_utc"] = medianoche_utc + desfase

    # Validación: cada día debe tener (horas del día x 60 / duración) periodos
    resumen = df.groupby("fecha").agg(periodos=("periodo", "count"),
                                      duracion_min=("duracion_min", "first")).reset_index()
    resumen["horas_dia"] = horas_del_dia(resumen["fecha"])
    resumen["periodos_esperados"] = (resumen["horas_dia"] * 60 / resumen["duracion_min"]).astype(int)
    incorrectos = resumen[resumen["periodos"] != resumen["periodos_esperados"]]

    todas_las_fechas = pd.date_range(config.FECHA_INICIO, config.FECHA_FIN, freq="D")
    faltan = todas_las_fechas.difference(resumen["fecha"])

    calidad["dias"] = len(resumen)
    calidad["dias_esperados"] = len(todas_las_fechas)
    calidad["dias_faltantes"] = [f"{d:%Y-%m-%d}" for d in faltan]
    calidad["dias_23h"] = int((resumen["horas_dia"] == 23).sum())
    calidad["dias_25h"] = int((resumen["horas_dia"] == 25).sum())
    calidad["dias_15min"] = int((resumen["duracion_min"] == 15).sum())
    calidad["primer_dia_15min"] = (
        f"{resumen.loc[resumen['duracion_min'] == 15, 'fecha'].min():%Y-%m-%d}"
        if calidad["dias_15min"] else "-"
    )
    calidad["dias_periodos_incorrectos"] = [
        f"{r.fecha:%Y-%m-%d} ({r.periodos} de {r.periodos_esperados})" for r in incorrectos.itertuples()
    ]
    calidad["filas_periodos"] = len(df)
    return df


# ---------------------------------------------------------------------------
# 3. Paso a resolución horaria y columnas de hora local
# ---------------------------------------------------------------------------
def a_horario(df: pd.DataFrame) -> pd.DataFrame:
    """Media de los periodos (cuartos de hora o horas) dentro de cada hora UTC."""
    df = df.copy()
    df["hora_utc"] = df["inicio_utc"].dt.floor("h")
    horario = (df.groupby("hora_utc")
                 .agg(precio_eur_mwh=("precio_es", "mean"),
                      num_periodos=("precio_es", "size"))
                 .reset_index())
    return horario


def anadir_hora_local(df: pd.DataFrame) -> pd.DataFrame:
    """Añade columnas de calendario en hora de Madrid."""
    local = df["hora_utc"].dt.tz_convert(ZONA)
    df["hora_local"] = local.dt.strftime("%Y-%m-%d %H:%M")
    df["fecha"] = local.dt.strftime("%Y-%m-%d")
    df["anio"] = local.dt.year
    df["mes"] = local.dt.month
    df["hora"] = local.dt.hour
    df["dia_semana"] = local.dt.day_of_week + 1        # 1 = lunes ... 7 = domingo
    # La 02:00 de octubre aparece dos veces: marcamos la segunda
    df["hora_repetida"] = df["hora_local"].duplicated(keep="first")
    df["precio_cero_o_negativo"] = df["precio_eur_mwh"] <= 0
    return df


# ---------------------------------------------------------------------------
# 4. Energy-Charts: solar y demanda
# ---------------------------------------------------------------------------
def leer_energy_charts(calidad: dict) -> pd.DataFrame:
    """
    Lee todos los CSV mensuales de Energy-Charts y los deja en una fila por hora UTC.

    Los datos vienen en MW cada 60 min (2019) o cada 15 min (años recientes).
    La media de la potencia (MW) durante una hora es la energía de esa hora (MWh),
    así que basta con hacer la media de los periodos de cada hora UTC.
    """
    ficheros = sorted(config.RAW_ENERGY_CHARTS.glob("*.csv"))
    if not ficheros:
        raise FileNotFoundError("No hay ficheros de Energy-Charts. Ejecuta antes download_energy_charts.py")
    df = pd.concat([pd.read_csv(f) for f in ficheros], ignore_index=True)
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)

    # Duplicados de instante (p. ej. si dos meses se solapan)
    calidad["ec_filas"] = len(df)
    calidad["ec_duplicados"] = int(df.duplicated("datetime_utc").sum())
    df = df.drop_duplicates("datetime_utc").sort_values("datetime_utc")

    # Periodos sin dato (null en la API)
    calidad["ec_nulos_solar"] = int(df["solar_mw"].isna().sum())
    calidad["ec_nulos_demanda"] = int(df["demanda_mw"].isna().sum())

    df["hora_utc"] = df["datetime_utc"].dt.floor("h")
    return (df.groupby("hora_utc")
              .agg(solar_mwh=("solar_mw", "mean"), demanda_mwh=("demanda_mw", "mean"))
              .reset_index())


def unir_solar_demanda(horario: pd.DataFrame, calidad: dict) -> pd.DataFrame:
    """Une solar y demanda a la tabla horaria de precios (left join por hora UTC)."""
    horario = horario.merge(leer_energy_charts(calidad), on="hora_utc", how="left")
    for columna in ["solar_mwh", "demanda_mwh"]:
        calidad[f"cobertura_{columna}"] = horario[columna].notna().mean() * 100

    # Generación solar negativa (consumo auxiliar nocturno) => 0
    negativos = horario["solar_mwh"] < 0
    calidad["solar_negativos_a_cero"] = int(negativos.sum())
    horario.loc[negativos, "solar_mwh"] = 0.0
    return horario


def validar_solar_con_ree(horario: pd.DataFrame, calidad: dict) -> None:
    """
    Compara la solar diaria de Energy-Charts (suma de las horas de cada día local)
    con el dato diario oficial de REE (REData, fotovoltaica + termosolar, Península).

    Salida: data/processed/validacion_solar_diaria.csv y un resumen anual en calidad.
    """
    ficheros = sorted(config.RAW_REDATA.glob("*.csv"))
    if not ficheros:
        calidad["validacion_anual"] = None
        return
    ree = pd.concat([pd.read_csv(f) for f in ficheros], ignore_index=True)
    ree["solar_ree_mwh"] = ree["solar_fv_mwh"] + ree["solar_termica_mwh"]

    diaria = (horario.groupby("fecha")["solar_mwh"].sum(min_count=1)
                     .rename("solar_energy_charts_mwh").reset_index())
    diaria = diaria.merge(ree, on="fecha", how="inner").dropna()
    diaria["diferencia_pct"] = (diaria["solar_energy_charts_mwh"] / diaria["solar_ree_mwh"] - 1) * 100
    diaria["cuota_termosolar_pct"] = diaria["solar_termica_mwh"] / diaria["solar_ree_mwh"] * 100

    columnas = ["fecha", "solar_energy_charts_mwh", "solar_fv_mwh", "solar_termica_mwh",
                "solar_ree_mwh", "diferencia_pct", "cuota_termosolar_pct"]
    diaria[columnas].round(4).to_csv(config.DATA_PROCESSED / "validacion_solar_diaria.csv", index=False)

    # Resumen anual (solo días con dato en las dos fuentes)
    diaria["anio"] = diaria["fecha"].str[:4]
    diaria["diferencia_abs_pct"] = diaria["diferencia_pct"].abs()
    anual = diaria.groupby("anio").agg(
        ec_gwh=("solar_energy_charts_mwh", "sum"),
        ree_gwh=("solar_ree_mwh", "sum"),
        termica_gwh=("solar_termica_mwh", "sum"),
        mediana_dif_abs_pct=("diferencia_abs_pct", "median"),
    )
    anual[["ec_gwh", "ree_gwh", "termica_gwh"]] /= 1000
    anual["diferencia_anual_pct"] = (anual["ec_gwh"] / anual["ree_gwh"] - 1) * 100
    anual["cuota_termosolar_pct"] = anual["termica_gwh"] / anual["ree_gwh"] * 100
    calidad["validacion_anual"] = anual.reset_index()
    calidad["validacion_dias"] = len(diaria)


# ---------------------------------------------------------------------------
# 5. Informe de calidad
# ---------------------------------------------------------------------------
def escribir_informe(calidad: dict, horario: pd.DataFrame) -> None:
    precios = horario["precio_eur_mwh"]

    def lista(valores, maximo=30):
        if not valores:
            return "ninguno"
        texto = ", ".join(valores[:maximo])
        return texto + (f" … (+{len(valores) - maximo} más)" if len(valores) > maximo else "")

    lineas = [
        "# Informe de calidad de datos",
        "",
        "_Generado automáticamente por `src/clean.py`. No editar a mano._",
        "",
        f"Periodo de estudio: **{config.FECHA_INICIO}** a **{config.FECHA_FIN}** (hora de Madrid).",
        "",
        "## Precios de OMIE (zona España)",
        "",
        "| Indicador | Valor |",
        "|---|---|",
        f"| Filas leídas (todos los ficheros) | {calidad['filas_leidas']:,} |",
        f"| Filas en el periodo (granularidad original) | {calidad['filas_periodos']:,} |",
        f"| Filas horarias | {len(horario):,} |",
        f"| Días con datos / esperados | {calidad['dias']:,} / {calidad['dias_esperados']:,} |",
        f"| Duplicados (fecha, periodo) eliminados | {calidad['duplicados']} |",
        f"| Precios nulos | {calidad['precios_nulos']} |",
        f"| Días de 23 h (cambio a horario de verano) | {calidad['dias_23h']} |",
        f"| Días de 25 h (cambio a horario de invierno) | {calidad['dias_25h']} |",
        f"| Días con periodos de 15 min | {calidad['dias_15min']} (desde {calidad['primer_dia_15min']}) |",
        f"| Días con nº de periodos incorrecto | {len(calidad['dias_periodos_incorrectos'])} |",
        f"| Precio mínimo (€/MWh, horario) | {precios.min():.2f} |",
        f"| Precio máximo (€/MWh, horario) | {precios.max():.2f} |",
        f"| Precio medio (€/MWh, horario) | {precios.mean():.2f} |",
        f"| % horas con precio ≤ 0 € | {(precios <= 0).mean() * 100:.2f} % |",
        "",
        f"**Días que faltan:** {lista(calidad['dias_faltantes'])}",
        "",
        f"**Días con periodos incorrectos:** {lista(calidad['dias_periodos_incorrectos'])}",
        "",
        "## Solar y demanda (Energy-Charts)",
        "",
        "| Indicador | Valor |",
        "|---|---|",
        f"| Filas leídas (granularidad original: 60 min en 2019, 15 min en años recientes) | {calidad['ec_filas']:,} |",
        f"| Duplicados de instante eliminados | {calidad['ec_duplicados']} |",
        f"| Periodos sin dato de solar | {calidad['ec_nulos_solar']} |",
        f"| Periodos sin dato de demanda | {calidad['ec_nulos_demanda']} |",
        f"| Cobertura solar (% de horas con dato) | {calidad['cobertura_solar_mwh']:.2f} % |",
        f"| Cobertura demanda (% de horas con dato) | {calidad['cobertura_demanda_mwh']:.2f} % |",
        f"| Valores de solar negativos puestos a 0 | {calidad['solar_negativos_a_cero']} |",
        "",
        "La serie «Solar» de Energy-Charts es **fotovoltaica + termosolar** juntas.",
        "",
        "## Validación de la solar contra REE (REData, dato diario oficial)",
        "",
    ]
    anual = calidad["validacion_anual"]
    if anual is None:
        lineas += ["> ⚠️ No hay datos de REData. Ejecuta `download_redata.py` para generar la validación.", ""]
    else:
        lineas += [
            "Se suma la solar horaria de Energy-Charts de cada día (hora de Madrid) y se compara con la",
            "generación diaria oficial de REE en la Península (fotovoltaica + solar térmica, porque",
            "Energy-Charts da las dos juntas). Diferencia = (Energy-Charts / REE − 1) × 100.",
            f"Días comparados: {calidad['validacion_dias']:,}. "
            "Detalle diario en `data/processed/validacion_solar_diaria.csv`.",
            "",
            "| Año | Energy-Charts (GWh) | REE (GWh) | Diferencia anual | Mediana dif. diaria (abs) | Cuota termosolar |",
            "|---|---|---|---|---|---|",
        ]
        for r in anual.itertuples():
            lineas.append(f"| {r.anio} | {r.ec_gwh:,.0f} | {r.ree_gwh:,.0f} | {r.diferencia_anual_pct:+.2f} % "
                          f"| {r.mediana_dif_abs_pct:.2f} % | {r.cuota_termosolar_pct:.1f} % |")
        lineas.append("")

    config.DOCS.mkdir(parents=True, exist_ok=True)
    (config.DOCS / "calidad_datos.md").write_text("\n".join(lineas), encoding="utf-8")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main() -> None:
    calidad = {}
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("Leyendo OMIE...")
    periodos = limpiar_periodos(leer_omie(), calidad)

    # Salida 1: precios en granularidad original
    salida_periodos = periodos.assign(
        inicio_utc=periodos["inicio_utc"].dt.strftime("%Y-%m-%d %H:%M"),
        fecha=periodos["fecha"].dt.strftime("%Y-%m-%d"),
    )[["fecha", "periodo", "duracion_min", "inicio_utc", "precio_es", "precio_pt"]]
    salida_periodos.to_csv(config.DATA_PROCESSED / "precios_periodos.csv", index=False)

    print("Pasando a resolución horaria...")
    horario = anadir_hora_local(a_horario(periodos))
    horario = unir_solar_demanda(horario, calidad)
    validar_solar_con_ree(horario, calidad)

    # Salida 2: tabla horaria (hora UTC en texto, sin zona, para Power BI)
    horario["hora_utc"] = horario["hora_utc"].dt.strftime("%Y-%m-%d %H:%M")
    columnas = ["hora_utc", "hora_local", "fecha", "anio", "mes", "hora", "dia_semana",
                "hora_repetida", "precio_eur_mwh", "precio_cero_o_negativo",
                "solar_mwh", "demanda_mwh", "num_periodos"]
    horario[columnas].round(4).to_csv(config.DATA_PROCESSED / "electricidad_horaria.csv", index=False)

    escribir_informe(calidad, horario)
    print(f"Limpieza terminada: {len(horario):,} horas. Informe en docs/calidad_datos.md")


if __name__ == "__main__":
    main()

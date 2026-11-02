"""
Descarga de generación solar y demanda de España desde Energy-Charts (Fraunhofer ISE).

- API pública, sin token: https://api.energy-charts.info/public_power
- Series: "Solar" (fotovoltaica + termosolar, MW) y "Load" (demanda, MW).
- Resolución: 60 min en 2019 y 15 min en los años recientes.
- Se descarga mes a mes y cada mes se guarda en data/raw/energy_charts/AAAA-MM.csv
  con las columnas datetime_utc, solar_mw y demanda_mw.
  Los meses ya descargados no se vuelven a pedir.
- La API limita las peticiones (429 Too Many Requests): se hace una pausa entre meses
  y, si aun así responde 429 o un error 5xx, se reintenta esperando cada vez más.
"""

import time

import pandas as pd
import requests

import config

REINTENTOS = 5
ESPERA_INICIAL_SEGUNDOS = 15


def pedir_con_reintentos(sesion: requests.Session, url: str, parametros: dict) -> dict:
    """
    Hace un GET y devuelve el JSON. Si la respuesta es 429 o 5xx, reintenta hasta
    REINTENTOS veces esperando 15 s, 30 s, 60 s... Otros errores se lanzan directamente.
    """
    espera = ESPERA_INICIAL_SEGUNDOS
    for intento in range(REINTENTOS + 1):
        respuesta = sesion.get(url, params=parametros, timeout=120)
        reintentable = respuesta.status_code == 429 or respuesta.status_code >= 500
        if not reintentable or intento == REINTENTOS:
            respuesta.raise_for_status()
            return respuesta.json()
        print(f"  Respuesta {respuesta.status_code}: reintento {intento + 1}/{REINTENTOS} en {espera} s")
        time.sleep(espera)
        espera *= 2


def descargar_mes(mes: pd.Timestamp, sesion: requests.Session) -> pd.DataFrame:
    """
    Descarga un mes completo. Las fechas start y end se interpretan en hora local,
    así que pidiendo del día 1 al último día del mes llega el mes entero (también
    en los meses con cambio de hora).
    """
    ultimo_dia = mes + pd.offsets.MonthEnd(0)
    parametros = {
        "country": config.ENERGY_CHARTS_PAIS,
        "start": f"{mes:%Y-%m-%d}",
        "end": f"{ultimo_dia:%Y-%m-%d}",
    }
    datos = pedir_con_reintentos(sesion, config.ENERGY_CHARTS_URL, parametros)

    # "unix_seconds" es el inicio de cada periodo en UTC
    df = pd.DataFrame({
        "datetime_utc": pd.to_datetime(datos["unix_seconds"], unit="s", utc=True)
                          .strftime("%Y-%m-%d %H:%M"),
    })

    # "production_types" es una lista de series {"name": ..., "data": [...]}
    series = {s["name"]: s["data"] for s in datos["production_types"]}
    for nombre_api, columna in config.ENERGY_CHARTS_SERIES.items():
        if nombre_api not in series:
            raise ValueError(f"La respuesta de Energy-Charts de {mes:%Y-%m} no trae la serie "
                             f"'{nombre_api}'. Series recibidas: {sorted(series)}")
        df[columna] = series[nombre_api]   # puede haber algún null suelto -> NaN
    return df


def main() -> None:
    config.RAW_ENERGY_CHARTS.mkdir(parents=True, exist_ok=True)
    sesion = requests.Session()

    # Lista de meses del periodo de estudio
    meses = pd.date_range(config.FECHA_INICIO, config.FECHA_FIN, freq="MS")

    for mes in meses:
        destino = config.RAW_ENERGY_CHARTS / f"{mes:%Y-%m}.csv"
        if destino.exists():
            continue
        df = descargar_mes(mes, sesion)
        df.to_csv(destino, index=False)
        print(f"  {mes:%Y-%m}: {len(df)} filas")
        time.sleep(config.ENERGY_CHARTS_PAUSA_SEGUNDOS)


if __name__ == "__main__":
    main()

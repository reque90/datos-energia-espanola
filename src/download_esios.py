"""
Descarga de indicadores de ESIOS (Red Eléctrica): generación solar fotovoltaica y demanda.

- Necesita un token personal en el fichero .env (ESIOS_TOKEN=...).
- Si no hay token, avisa y termina sin error: el resto del proyecto sigue funcionando
  pero sin las métricas que dependen de la solar.
- Se descarga mes a mes y cada mes se guarda en data/raw/esios/<nombre>_AAAA-MM.csv.
  Los meses ya descargados no se vuelven a pedir.
"""

import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

import config


def leer_token() -> str | None:
    """Lee el token de ESIOS del fichero .env (o de las variables de entorno)."""
    load_dotenv(config.RAIZ / ".env")
    token = os.getenv("ESIOS_TOKEN", "").strip()
    return token or None


def descargar_mes(id_indicador: int, inicio: pd.Timestamp, fin: pd.Timestamp,
                  token: str, sesion: requests.Session) -> pd.DataFrame:
    """Descarga un indicador entre dos instantes (con zona horaria) en resolución horaria."""
    cabeceras = {
        "x-api-key": token,
        "Accept": "application/json; application/vnd.esios-api-v1+json",
        "Content-Type": "application/json",
    }
    parametros = {
        "start_date": inicio.isoformat(),
        "end_date": fin.isoformat(),
        "time_trunc": "hour",
        "time_agg": "average",
    }
    url = config.ESIOS_URL.format(id=id_indicador)
    respuesta = sesion.get(url, headers=cabeceras, params=parametros, timeout=120)
    respuesta.raise_for_status()
    valores = respuesta.json()["indicator"]["values"]

    df = pd.DataFrame(valores)
    if df.empty:
        return pd.DataFrame(columns=["datetime_utc", "value", "geo_id", "geo_name"])
    df = df[["datetime_utc", "value", "geo_id", "geo_name"]]

    # Si vienen varias zonas, nos quedamos con la Península
    if df["geo_name"].nunique() > 1:
        df = df[df["geo_name"] == config.ESIOS_ZONA_PREFERIDA]
    return df


def main() -> bool:
    """Devuelve True si hay datos de ESIOS disponibles, False si se ha saltado."""
    token = leer_token()
    if token is None:
        print("AVISO: no hay ESIOS_TOKEN en .env -> se omite la descarga de solar y demanda.")
        print("       El análisis de precios y batería funciona igual; la parte solar quedará vacía.")
        return False

    config.RAW_ESIOS.mkdir(parents=True, exist_ok=True)
    sesion = requests.Session()
    zona = config.ZONA_HORARIA

    # Lista de meses del periodo de estudio
    meses = pd.date_range(config.FECHA_INICIO, config.FECHA_FIN, freq="MS")

    for nombre, id_indicador in config.ESIOS_INDICADORES.items():
        print(f"Indicador {id_indicador} ({nombre})")
        for mes in meses:
            destino = config.RAW_ESIOS / f"{nombre}_{mes:%Y-%m}.csv"
            if destino.exists():
                continue
            inicio = mes.tz_localize(zona)
            fin = (mes + pd.offsets.MonthBegin(1)).tz_localize(zona) - pd.Timedelta(seconds=1)
            try:
                df = descargar_mes(id_indicador, inicio, fin, token, sesion)
            except requests.HTTPError as error:
                print(f"  Error en {mes:%Y-%m}: {error}")
                continue
            df.to_csv(destino, index=False)
            print(f"  {mes:%Y-%m}: {len(df)} filas")
            time.sleep(config.ESIOS_PAUSA_SEGUNDOS)

    return True


if __name__ == "__main__":
    main()

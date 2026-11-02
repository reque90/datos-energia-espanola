"""
Descarga de la generación solar diaria oficial de Red Eléctrica (REData), para validar.

- API pública, sin token: https://apidatos.ree.es
- Generación diaria del sistema peninsular por tecnología. Se guardan la solar
  fotovoltaica (id 1458) y la solar térmica (id 1459), en MWh.
- Se descarga año a año (la API admite un año entero en una petición) y cada año se
  guarda en data/raw/redata/AAAA.csv con las columnas fecha, solar_fv_mwh y
  solar_termica_mwh. Los años ya descargados no se vuelven a pedir.
- REData no tiene dato horario por tecnología: solo sirve para comprobar que la solar
  horaria de Energy-Charts suma lo mismo cada día (ver clean.py).
"""

import time

import pandas as pd
import requests

import config
from download_energy_charts import pedir_con_reintentos


def descargar_anio(inicio: pd.Timestamp, fin: pd.Timestamp, sesion: requests.Session) -> pd.DataFrame:
    """Descarga la solar diaria entre dos fechas (incluidas) y la deja en una fila por día."""
    parametros = {
        **config.REDATA_PARAMS,
        "start_date": f"{inicio:%Y-%m-%d}T00:00",
        "end_date": f"{fin:%Y-%m-%d}T23:59",
    }
    datos = pedir_con_reintentos(sesion, config.REDATA_URL, parametros)

    # "included" es una lista de tecnologías con sus valores diarios
    tecnologias = {t["id"]: t["attributes"]["values"] for t in datos["included"]}
    df = pd.DataFrame({"fecha": pd.date_range(inicio, fin, freq="D").strftime("%Y-%m-%d")})
    for id_tecnologia, columna in config.REDATA_SERIES.items():
        if id_tecnologia not in tecnologias:
            raise ValueError(f"La respuesta de REData de {inicio:%Y} no trae la tecnología "
                             f"'{id_tecnologia}' ({columna}).")
        # La fecha son los 10 primeros caracteres de "datetime" (AAAA-MM-DD, hora local)
        valores = {v["datetime"][:10]: v["value"] for v in tecnologias[id_tecnologia]}
        df[columna] = df["fecha"].map(valores)
    return df


def main() -> None:
    config.RAW_REDATA.mkdir(parents=True, exist_ok=True)
    sesion = requests.Session()
    fecha_inicio = pd.Timestamp(config.FECHA_INICIO)
    fecha_fin = pd.Timestamp(config.FECHA_FIN)

    for anio in range(fecha_inicio.year, fecha_fin.year + 1):
        destino = config.RAW_REDATA / f"{anio}.csv"
        if destino.exists():
            continue
        # El primer y el último año se recortan al periodo de estudio
        inicio = max(pd.Timestamp(f"{anio}-01-01"), fecha_inicio)
        fin = min(pd.Timestamp(f"{anio}-12-31"), fecha_fin)
        df = descargar_anio(inicio, fin, sesion)
        df.to_csv(destino, index=False)
        print(f"  {anio}: {len(df)} días")
        time.sleep(config.REDATA_PAUSA_SEGUNDOS)


if __name__ == "__main__":
    main()

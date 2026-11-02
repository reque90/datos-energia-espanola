"""
Descarga de los precios del mercado diario de OMIE (ficheros marginalpdbc).

Estrategia:
1. Hasta 2022 se intenta descargar el zip anual (marginalpdbc_AAAA.zip) y se
   extraen los ficheros diarios.
2. Para cualquier día que todavía falte (todos los de 2023 en adelante, o los
   que no vinieran en el zip) se descarga el fichero diario marginalpdbc_AAAAMMDD.1.
3. Lo que ya está en disco no se vuelve a descargar.

Nota: OMIE publica a veces versiones corregidas de un día (.2, .3...). El zip anual
puede traer solo la versión corregida; clean.py usa siempre la versión más alta.
"""

import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

import config


def nombre_fichero_diario(fecha: pd.Timestamp) -> str:
    """Nombre del fichero diario de OMIE (versión 1), p. ej. marginalpdbc_20230101.1"""
    return f"marginalpdbc_{fecha:%Y%m%d}.1"


def dia_en_disco(fecha: pd.Timestamp) -> bool:
    """True si ya tenemos alguna versión (.1, .2, ...) del fichero de ese día."""
    return any(config.RAW_OMIE.glob(f"marginalpdbc_{fecha:%Y%m%d}.*"))


def descargar(nombre: str, sesion: requests.Session, reintentos: int = 5) -> bytes | None:
    """Descarga un fichero de OMIE. Devuelve None si no existe (404).

    Si el servidor da un error temporal (5xx o fallo de conexión) se reintenta
    esperando cada vez un poco más (5 s, 10 s, 20 s...).
    """
    url = config.OMIE_URL.format(nombre=nombre)
    for intento in range(reintentos):
        try:
            respuesta = sesion.get(url, timeout=60)
        except requests.ConnectionError:
            respuesta = None
        time.sleep(config.OMIE_PAUSA_SEGUNDOS)
        if respuesta is not None and respuesta.status_code < 500:
            break
        espera = 5 * 2 ** intento
        print(f"  Error temporal en {nombre}, reintento en {espera} s")
        time.sleep(espera)
    else:
        raise RuntimeError(f"OMIE no responde tras {reintentos} intentos: {nombre}")

    if respuesta.status_code == 404:
        return None
    respuesta.raise_for_status()
    # Si el fichero no existe, a veces OMIE devuelve una página HTML en lugar de 404
    if respuesta.content.lstrip()[:1] == b"<":
        return None
    return respuesta.content


def descargar_zip_anual(anio: int, sesion: requests.Session) -> int:
    """Descarga el zip de un año y guarda sus ficheros diarios. Devuelve cuántos guardó."""
    contenido = descargar(f"marginalpdbc_{anio}.zip", sesion)
    if contenido is None:
        print(f"  No hay zip anual para {anio}")
        return 0

    guardados = 0
    with zipfile.ZipFile(io.BytesIO(contenido)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # Por seguridad usamos solo el nombre del fichero, nunca la ruta interna del zip
            nombre = Path(info.filename).name
            if not nombre.startswith("marginalpdbc_"):
                continue
            destino = config.RAW_OMIE / nombre
            if not destino.exists():
                destino.write_bytes(zf.read(info))
                guardados += 1
    print(f"  Zip {anio}: {guardados} ficheros nuevos")
    return guardados


def main() -> None:
    config.RAW_OMIE.mkdir(parents=True, exist_ok=True)
    fechas = pd.date_range(config.FECHA_INICIO, config.FECHA_FIN, freq="D")
    sesion = requests.Session()

    # 1) Zips anuales: solo si a ese año le falta algún día en disco
    for anio in sorted(set(fechas.year)):
        if anio > config.OMIE_ULTIMO_ANIO_CON_ZIP:
            continue
        dias_anio = fechas[fechas.year == anio]
        faltan = [f for f in dias_anio if not dia_en_disco(f)]
        if faltan:
            print(f"Descargando zip anual de {anio} (faltan {len(faltan)} días)")
            descargar_zip_anual(anio, sesion)

    # 2) Ficheros diarios para los días que sigan faltando
    faltan = [f for f in fechas if not dia_en_disco(f)]
    print(f"Días a descargar uno a uno: {len(faltan)}")
    no_encontrados = []
    for i, fecha in enumerate(faltan, start=1):
        nombre = nombre_fichero_diario(fecha)
        contenido = descargar(nombre, sesion)
        if contenido is not None:
            (config.RAW_OMIE / nombre).write_bytes(contenido)
        else:
            # Algunos días solo existen como versión corregida (.2, .3...),
            # y no siempre son consecutivas. Probamos de la .2 a la .5.
            encontrado = False
            for version in range(2, 6):
                nombre_version = nombre[:-1] + str(version)
                contenido = descargar(nombre_version, sesion)
                if contenido is not None:
                    (config.RAW_OMIE / nombre_version).write_bytes(contenido)
                    encontrado = True
            if not encontrado:
                no_encontrados.append(nombre)
        if i % 100 == 0:
            print(f"  {i}/{len(faltan)} descargados")

    total = sum(dia_en_disco(f) for f in fechas)
    print(f"OMIE listo: {total} de {len(fechas)} días en disco")
    if no_encontrados:
        print(f"  Aviso: {len(no_encontrados)} ficheros no existen en OMIE: {no_encontrados[:10]}")


if __name__ == "__main__":
    main()

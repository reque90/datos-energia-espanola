"""
Configuración central del proyecto.

Aquí están todas las rutas, el periodo de estudio, las URL y parámetros de las
fuentes (OMIE, Energy-Charts y REData; todas públicas y sin token) y los supuestos
de la batería. Si hay que cambiar algo, se cambia aquí y el resto de scripts
lo recogen automáticamente.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
# Carpeta raíz del proyecto (la carpeta que contiene a src/)
RAIZ = Path(__file__).resolve().parent.parent

DATA_RAW = RAIZ / "data" / "raw"
DATA_PROCESSED = RAIZ / "data" / "processed"
DOCS = RAIZ / "docs"

RAW_OMIE = DATA_RAW / "omie"      # ficheros diarios marginalpdbc_AAAAMMDD.1
RAW_ENERGY_CHARTS = DATA_RAW / "energy_charts"   # un CSV por mes: solar y demanda
RAW_REDATA = DATA_RAW / "redata"                 # un CSV por año: solar diaria oficial de REE

# ---------------------------------------------------------------------------
# Periodo de estudio (fechas fijas para que el resultado sea reproducible)
# ---------------------------------------------------------------------------
FECHA_INICIO = "2019-01-01"
FECHA_FIN = "2026-10-31"   # incluida

ZONA_HORARIA = "Europe/Madrid"

# ---------------------------------------------------------------------------
# OMIE (precios del mercado diario)
# ---------------------------------------------------------------------------
OMIE_URL = "https://www.omie.es/es/file-download?parents%5B0%5D=marginalpdbc&filename={nombre}"
OMIE_ULTIMO_ANIO_CON_ZIP = 2022   # hasta este año existe el zip anual
OMIE_PAUSA_SEGUNDOS = 0.2         # pausa entre peticiones para no saturar el servidor

# ---------------------------------------------------------------------------
# Energy-Charts (Fraunhofer ISE) – solar y demanda (sin token)
# ---------------------------------------------------------------------------
ENERGY_CHARTS_URL = "https://api.energy-charts.info/public_power"
ENERGY_CHARTS_PAIS = "es"
ENERGY_CHARTS_SERIES = {"Solar": "solar_mw", "Load": "demanda_mw"}   # nombre en la API -> columna
ENERGY_CHARTS_PAUSA_SEGUNDOS = 3   # la API devuelve 429 si se le pide demasiado rápido

# ---------------------------------------------------------------------------
# REData (Red Eléctrica) – solar diaria oficial peninsular, para validar (sin token)
# ---------------------------------------------------------------------------
REDATA_URL = "https://apidatos.ree.es/es/datos/generacion/estructura-generacion"
REDATA_PARAMS = {"time_trunc": "day", "geo_trunc": "electric_system",
                 "geo_limit": "peninsular", "geo_ids": "8741"}
REDATA_SERIES = {"1458": "solar_fv_mwh", "1459": "solar_termica_mwh"}   # id de tecnología -> columna
REDATA_PAUSA_SEGUNDOS = 1

# ---------------------------------------------------------------------------
# Supuestos de la batería
# ---------------------------------------------------------------------------
BATERIA_POTENCIA_MW = 1.0
BATERIA_ENERGIA_MWH = 4.0
BATERIA_HORAS = int(BATERIA_ENERGIA_MWH / BATERIA_POTENCIA_MW)   # 4 horas de carga/descarga
BATERIA_EFICIENCIA = 0.88   # eficiencia de ida y vuelta (round-trip)

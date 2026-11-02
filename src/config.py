"""
Configuración central del proyecto.

Aquí están todas las rutas, el periodo de estudio, los IDs de los indicadores
de ESIOS y los supuestos de la batería. Si hay que cambiar algo, se cambia aquí
y el resto de scripts lo recogen automáticamente.
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
RAW_ESIOS = DATA_RAW / "esios"    # un CSV por indicador y mes

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
# ESIOS (Red Eléctrica) – IDs de indicadores (VERIFICAR en https://www.esios.ree.es)
# ---------------------------------------------------------------------------
ESIOS_URL = "https://api.esios.ree.es/indicators/{id}"
ESIOS_INDICADORES = {
    "solar_fv_mw": 1295,   # Generación T.Real solar fotovoltaica (MW)
    "demanda_mw": 1293,    # Demanda real (MW)
}
ESIOS_ZONA_PREFERIDA = "Península"
ESIOS_PAUSA_SEGUNDOS = 0.5

# ---------------------------------------------------------------------------
# Supuestos de la batería
# ---------------------------------------------------------------------------
BATERIA_POTENCIA_MW = 1.0
BATERIA_ENERGIA_MWH = 4.0
BATERIA_HORAS = int(BATERIA_ENERGIA_MWH / BATERIA_POTENCIA_MW)   # 4 horas de carga/descarga
BATERIA_EFICIENCIA = 0.88   # eficiencia de ida y vuelta (round-trip)

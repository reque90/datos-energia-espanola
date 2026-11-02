# ¿Está la solar canibalizando su propio precio? — Mercado eléctrico español

Proyecto de la asignatura **Visualization and Enterprise Reporting**.

## Pregunta de negocio

> **¿Está la energía solar canibalizando su propio precio, y cuál es el caso de negocio de las baterías?**

Cuanta más solar hay instalada, más se hunde el precio en las horas de sol, y la solar
termina vendiendo su energía más barata que la media (*efecto canibalización*).
Esas mismas diferencias de precio entre horas son la oportunidad de negocio de las
baterías: cargar barato al mediodía y vender caro por la tarde-noche.

## Flujo de datos

```
 FUENTES (públicas, sin token)   PYTHON (src/)                          CSV                         POWER BI
┌──────────────────┐     ┌──────────────────────────┐
│ OMIE             │────▶│ download_omie.py         │──┐
│ precios          │     └──────────────────────────┘  │
└──────────────────┘                                   │   ┌──────────┐    ┌────────────┐    ┌────────────────────────┐    ┌───────────┐
┌──────────────────┐     ┌──────────────────────────┐  ├──▶│ clean.py │───▶│ metrics.py │───▶│ data/processed/*.csv   │───▶│ Dashboard │
│ Energy-Charts    │────▶│ download_energy_charts.py│──┤   └──────────┘    └────────────┘    └────────────────────────┘    └───────────┘
│ solar, demanda   │     └──────────────────────────┘  │        │
└──────────────────┘                                   │        ├──▶ data/processed/validacion_solar_diaria.csv
┌──────────────────┐     ┌──────────────────────────┐  │        └──▶ docs/calidad_datos.md
│ REE REData       │────▶│ download_redata.py       │──┘
│ solar diaria     │     └──────────────────────────┘    (REData solo se usa para validar la solar)
│ (validación)     │
└──────────────────┘
                         run_all.py ejecuta todo en orden
```

## Estructura del repositorio

```
├── src/
│   ├── config.py                  # rutas, periodo de estudio, URL de las fuentes, supuestos de la batería
│   ├── download_omie.py           # descarga precios del mercado diario (OMIE)
│   ├── download_energy_charts.py  # descarga solar y demanda (Energy-Charts)
│   ├── download_redata.py         # descarga la solar diaria oficial de REE (validación)
│   ├── clean.py                   # limpieza, paso a horario, validación, informe de calidad
│   ├── metrics.py                 # métricas anuales, mensuales, batería y perfil hora×mes
│   └── run_all.py                 # ejecuta todo en orden
├── data/
│   ├── raw/                       # datos en bruto (NO se suben a git)
│   └── processed/                 # CSV limpios para Power BI (sí se suben)
├── docs/
│   ├── calidad_datos.md           # informe de calidad (generado automáticamente)
│   ├── decisiones.md              # decisiones de limpieza y análisis
│   └── fuentes.md                 # fuentes, licencias y citas
├── requirements.txt
└── README.md
```

## Instalación y ejecución en PyCharm

1. **Clonar el repositorio** y abrir la carpeta en PyCharm.
2. **Crear el entorno virtual**: *Settings → Project → Python Interpreter → Add Interpreter →
   Virtualenv Environment → New*, con Python 3.12 y ubicación `.venv`.
   (Desde terminal: `python -m venv .venv`).
3. **Instalar dependencias** en la terminal de PyCharm (que ya activa el `.venv`):
   ```
   pip install -r requirements.txt
   ```
4. **Ejecutar**: clic derecho en `src/run_all.py` → *Run 'run_all'*.
   (Desde terminal: `cd src && python run_all.py`).

Todas las fuentes son públicas: no hace falta registrarse ni pedir ningún token.

La primera ejecución tarda varios minutos (unos 1.400 ficheros diarios de OMIE a partir de 2023
y un mes por petición de Energy-Charts, con pausas para respetar su límite de peticiones).
Las siguientes son rápidas porque no se vuelve a descargar lo que ya está en disco.

## CSV generados (data/processed/)

| Fichero | Granularidad | Uso en el dashboard |
|---|---|---|
| `precios_periodos.csv` | Periodo original de OMIE (1 h hasta 30/09/2025, 15 min después) | Trazabilidad y detalle; comprobar el cambio a cuartos de hora |
| `electricidad_horaria.csv` | 1 fila por hora | Tabla de hechos principal: series temporales, filtros por fecha/hora, horas con precio ≤ 0 |
| `metricas_anuales.csv` | 1 fila por año | Tarjetas KPI y gráfico de evolución del *capture rate* y del ingreso de la batería |
| `metricas_mensuales.csv` | 1 fila por año-mes | Línea temporal de precio baseload vs. capturado solar; estacionalidad |
| `bateria_diaria.csv` | 1 fila por día | Distribución del spread diario y del margen de la batería |
| `perfil_hora_mes.csv` | Año × mes × hora | Mapa de calor hora × mes del precio y de la producción solar ("curva de pato") |
| `validacion_solar_diaria.csv` | 1 fila por día | Control de calidad: solar diaria de Energy-Charts frente al dato oficial de REE (diferencia % y cuota de termosolar) |

### ⚠️ Importar en Power BI

Los CSV usan **punto decimal** y coma como separador. Al importar en Power BI Desktop:
*Obtener datos → Texto/CSV → Transformar datos* y en el paso *Tipo cambiado* usar
**Cambiar tipo → Usar configuración regional → Inglés (Estados Unidos)**
(o bien *Archivo → Opciones → Configuración regional* del archivo = Inglés (EE. UU.)).
Si no, los decimales se leerán mal (p. ej. 63.33 → 6333).

## Definición de las métricas

| Métrica | Definición |
|---|---|
| `precio_baseload` | Media simple del precio horario (€/MWh) |
| `precio_capturado_solar` | Σ(precio × solar) / Σ(solar): precio medio que cobra la solar |
| `capture_rate` | precio capturado solar / precio baseload de las mismas horas. < 1 indica canibalización |
| `pct_horas_cero_o_negativo` | % de horas con precio ≤ 0 €/MWh |
| `pct_horas_negativo` | % de horas con precio < 0 €/MWh |
| `solar_gwh` | Generación solar total, fotovoltaica + termosolar (GWh) |
| `horas` / `anio_completo` | Horas con dato; el año es completo si tiene ≥ 8.760 horas |
| `precio_carga` / `precio_descarga` | Media de las 4 horas más baratas / más caras del día |
| `spread` | precio_descarga − precio_carga |
| `margen_eur_por_mw` | descarga × 4 − carga × 4 / 0,88; mínimo 0 (si no compensa, no opera) |
| `ingreso_bateria_eur_por_mw` | Suma de los márgenes diarios en el año o mes (€/MW) |

Supuestos de la batería: 1 MW / 4 MWh, eficiencia de ida y vuelta 0,88, un ciclo al día
(ver [docs/decisiones.md](docs/decisiones.md)).

## Equipo

| Rol | Responsabilidades | Nombre |
|---|---|---|
| Datos | Descarga, limpieza y métricas en Python | |
| Visualización | Diseño del dashboard en Power BI | |
| Documentación | README, decisiones, fuentes y presentación | |

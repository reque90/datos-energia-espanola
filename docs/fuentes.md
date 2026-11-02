# Fuentes de datos

Todas las fuentes del proyecto son **públicas y se descargan sin registro ni token**.

## 1. OMIE — Precios del mercado diario

- **Qué:** precio marginal del mercado diario (ficheros `marginalpdbc`), zonas España y Portugal.
- **Web:** https://www.omie.es/es/file-access-list
- **Descarga:** `https://www.omie.es/es/file-download?parents%5B0%5D=marginalpdbc&filename=<fichero>`
  (zip anual hasta 2022, ficheros diarios desde 2023).
- **Granularidad:** horaria hasta el 30/09/2025 y cuartohoraria desde el 01/10/2025.
- **Licencia / uso:** información pública publicada por OMIE. Su aviso legal permite el uso
  de la información citando la fuente; revisar las condiciones vigentes en https://www.omie.es/es/aviso-legal.
- **Cita:** OMIE – Operador del Mercado Ibérico de Energía, Polo Español. *Precios del mercado diario
  (marginalpdbc)*, 2019-2026. Consultado en noviembre de 2026, https://www.omie.es.

## 2. Energy-Charts (Fraunhofer ISE) — Solar y demanda

- **Qué:** generación eléctrica neta pública de España por tecnología. Se usan las series
  `Solar` (fotovoltaica + termosolar juntas, MW) y `Load` (demanda, MW).
- **Web:** https://energy-charts.info
- **API:** `https://api.energy-charts.info/public_power?country=es&start=AAAA-MM-DD&end=AAAA-MM-DD`
  (pública, sin token). Las fechas se interpretan en hora local y la respuesta trae el inicio
  de cada periodo en UTC (`unix_seconds`). Limita las peticiones (responde 429 si se va rápido).
- **Granularidad:** 60 min en 2019 y 15 min en los años recientes. Se agrega a horas en `clean.py`.
- **Origen de los datos:** Energy-Charts recopila los datos de la plataforma de transparencia de
  ENTSO-E y de los operadores del sistema (en España, Red Eléctrica).
- **Licencia / uso:** uso libre para fines no comerciales y periodísticos citando
  «Energy-Charts / Fraunhofer ISE», según https://energy-charts.info/llms.txt.
- **Cita:** Energy-Charts / Fraunhofer ISE. *Public net electricity generation, Spain*, 2019-2026.
  Consultado en noviembre de 2026, https://energy-charts.info.

## 3. Red Eléctrica (REE) — REData

- **Qué:** generación diaria por tecnología del sistema peninsular. Se usan la solar
  fotovoltaica (id 1458) y la solar térmica (id 1459), en MWh.
- **Web:** https://www.ree.es/es/datos/generacion
- **API:** `https://apidatos.ree.es/es/datos/generacion/estructura-generacion`
  con `time_trunc=day`, `geo_trunc=electric_system`, `geo_limit=peninsular`, `geo_ids=8741`
  (pública, sin token; admite un año entero por petición).
- **Para qué se usa:** solo para **validar** la solar de Energy-Charts día a día
  (ver `docs/calidad_datos.md`). No tiene dato horario por tecnología, así que no se usa en las métricas.
- **Licencia / uso:** datos de reutilización libre citando la fuente, según las condiciones de uso
  de REE (https://www.ree.es/es/aviso-legal — revisar versión vigente).
- **Cita:** Red Eléctrica de España. *REData – Estructura de la generación, sistema peninsular,
  solar fotovoltaica y solar térmica*, 2019-2026. Consultado en noviembre de 2026, https://www.ree.es/es/datos.

## Posibles fuentes adicionales

| Fuente | Dato | Para qué serviría |
|---|---|---|
| **MIBGAS** (https://www.mibgas.es) | Precio del gas natural en el mercado ibérico (PVB) | Explicar los precios altos de 2021-2022: el gas marca el precio en las horas sin solar |
| **Precio del CO₂** (EU ETS, p. ej. SENDECO2 o EEX) | €/t de derechos de emisión | Segundo factor de coste de los ciclos combinados |
| **REE – potencia instalada** (REData, https://www.ree.es/es/datos/generacion/potencia-instalada) | MW de solar FV instalados por año | Relacionar el *capture rate* con el crecimiento de la potencia solar |
| **Open-Meteo** (https://open-meteo.com) / **PVGIS** (https://re.jrc.ec.europa.eu/pvg_tools/) | Irradiación solar horaria | Separar el efecto del clima (años más soleados) del efecto de la potencia instalada |

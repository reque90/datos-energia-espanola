# Fuentes de datos

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

## 2. Red Eléctrica (REE) — ESIOS

- **Qué:** indicador 1295 (generación en tiempo real solar fotovoltaica, MW) e indicador 1293
  (demanda real, MW).
- **API:** `https://api.esios.ree.es/indicators/{id}` (requiere token personal, gratuito,
  solicitándolo a consultasios@ree.es).
- **Licencia / uso:** los datos de ESIOS son de reutilización libre citando la fuente, según
  las condiciones de uso de REE (https://www.esios.ree.es/es/pagina/condiciones-de-uso — revisar versión vigente).
- **Cita:** Red Eléctrica de España. *ESIOS – Sistema de Información del Operador del Sistema,
  indicadores 1293 y 1295*, 2019-2026. Consultado en noviembre de 2026, https://www.esios.ree.es.

## Posibles fuentes adicionales

| Fuente | Dato | Para qué serviría |
|---|---|---|
| **MIBGAS** (https://www.mibgas.es) | Precio del gas natural en el mercado ibérico (PVB) | Explicar los precios altos de 2021-2022: el gas marca el precio en las horas sin solar |
| **Precio del CO₂** (EU ETS, p. ej. SENDECO2 o EEX) | €/t de derechos de emisión | Segundo factor de coste de los ciclos combinados |
| **REE – potencia instalada** (REData, https://www.ree.es/es/datos/generacion/potencia-instalada) | MW de solar FV instalados por año | Relacionar el *capture rate* con el crecimiento de la potencia solar |
| **Open-Meteo** (https://open-meteo.com) / **PVGIS** (https://re.jrc.ec.europa.eu/pvg_tools/) | Irradiación solar horaria | Separar el efecto del clima (años más soleados) del efecto de la potencia instalada |

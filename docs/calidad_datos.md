# Informe de calidad de datos

_Generado automáticamente por `src/clean.py`. No editar a mano._

Periodo de estudio: **2019-01-01** a **2026-10-31** (hora de Madrid).

## Precios de OMIE (zona España)

| Indicador | Valor |
|---|---|
| Filas leídas (todos los ficheros) | 97,179 |
| Filas en el periodo (granularidad original) | 97,179 |
| Filas horarias | 68,664 |
| Días con datos / esperados | 2,861 / 2,861 |
| Duplicados (fecha, periodo) eliminados | 0 |
| Precios nulos | 0 |
| Días de 23 h (cambio a horario de verano) | 8 |
| Días de 25 h (cambio a horario de invierno) | 8 |
| Días con periodos de 15 min | 396 (desde 2025-10-01) |
| Días con nº de periodos incorrecto | 0 |
| Precio mínimo (€/MWh, horario) | -15.00 |
| Precio máximo (€/MWh, horario) | 700.00 |
| Precio medio (€/MWh, horario) | 82.46 |
| % horas con precio ≤ 0 € | 3.83 % |

**Días que faltan:** ninguno

**Días con periodos incorrectos:** ninguno

## Solar y demanda (ESIOS)

| Indicador | Valor |
|---|---|
| Cobertura solar (% de horas con dato) | 0.00 % |
| Cobertura demanda (% de horas con dato) | 0.00 % |
| Valores de solar negativos puestos a 0 | 0 |

> ⚠️ No hay datos de ESIOS (falta `ESIOS_TOKEN` en `.env`). Las métricas de precio capturado solar quedan vacías.

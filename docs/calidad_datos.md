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

## Solar y demanda (Energy-Charts)

| Indicador | Valor |
|---|---|
| Filas leídas (granularidad original: 60 min en 2019, 15 min en años recientes) | 169,464 |
| Duplicados de instante eliminados | 0 |
| Periodos sin dato de solar | 17 |
| Periodos sin dato de demanda | 147 |
| Cobertura solar (% de horas con dato) | 99.99 % |
| Cobertura demanda (% de horas con dato) | 99.95 % |
| Valores de solar negativos puestos a 0 | 0 |

La serie «Solar» de Energy-Charts es **fotovoltaica + termosolar** juntas.

## Validación de la solar contra REE (REData, dato diario oficial)

Se suma la solar horaria de Energy-Charts de cada día (hora de Madrid) y se compara con la
generación diaria oficial de REE en la Península (fotovoltaica + solar térmica, porque
Energy-Charts da las dos juntas). Diferencia = (Energy-Charts / REE − 1) × 100.
Días comparados: 2,858. Detalle diario en `data/processed/validacion_solar_diaria.csv`.

| Año | Energy-Charts (GWh) | REE (GWh) | Diferencia anual | Mediana dif. diaria (abs) | Cuota termosolar |
|---|---|---|---|---|---|
| 2019 | 14,402 | 14,000 | +2.87 % | 2.52 % | 36.9 % |
| 2020 | 20,031 | 19,463 | +2.92 % | 2.69 % | 23.3 % |
| 2021 | 25,354 | 25,236 | +0.47 % | 1.02 % | 18.6 % |
| 2022 | 31,092 | 31,445 | -1.12 % | 1.42 % | 13.1 % |
| 2023 | 40,433 | 41,412 | -2.37 % | 2.85 % | 11.3 % |
| 2024 | 47,319 | 47,813 | -1.03 % | 1.21 % | 8.6 % |
| 2025 | 52,524 | 52,981 | -0.86 % | 1.21 % | 6.9 % |
| 2026 | 57,063 | 56,588 | +0.84 % | 1.74 % | 6.9 % |

# Decisiones de limpieza y análisis

| # | Decisión | Justificación |
|---|---|---|
| 1 | Usar el precio de la **zona España** (6.ª columna de `marginalpdbc`) | El estudio es del mercado español. Se comprobó comparando con el precio spot publicado por REE. El precio de Portugal se conserva en `precios_periodos.csv` solo como referencia. |
| 2 | Trabajar internamente en **UTC** y añadir la hora local después | En hora local hay días de 23 h y de 25 h; en UTC todas las horas son únicas y consecutivas, lo que evita duplicados y huecos al unir OMIE con ESIOS. |
| 3 | Inicio de cada periodo = medianoche local en UTC + (periodo − 1) × duración | Numerar a partir de la medianoche (que nunca coincide con un cambio de hora) sitúa bien todos los periodos, incluidos los días de 23 y 25 h. |
| 4 | Duración del periodo detectada por día (≥ 90 periodos ⇒ 15 min; si no, 60 min) | Desde el 01/10/2025 OMIE publica en cuartos de hora. Detectarlo por día evita depender de una fecha fija. |
| 5 | Validar los periodos de cada día contra las horas reales del día | Las horas del día se calculan con la medianoche del día siguiente (no sumando 24 h), por lo que salen 23, 24 o 25. Así se detectan ficheros incompletos. |
| 6 | **Agregar los cuartos de hora a hora** con la media por hora UTC | Permite una serie homogénea 2019-2026 y cruzarla con ESIOS (horario). La media de 4 cuartos equivale al precio de la energía de una hora con perfil plano. |
| 7 | Eliminar **duplicados** por (fecha, periodo) | Evita contar dos veces un periodo si un fichero se descarga repetido o se solapa con el zip anual. |
| 8 | Indicador solar **1295** (generación en tiempo real solar fotovoltaica, Península) | Es la medida observada de producción FV. No incluye solar térmica, que tiene otro perfil (almacenamiento en sales). Pendiente de verificar el ID en ESIOS. |
| 9 | Media horaria en MW = MWh | Con `time_agg=average` y `time_trunc=hour`, la potencia media durante una hora es la energía producida en esa hora. |
| 10 | Valores de **generación negativos → 0** (y se cuentan) | De noche las plantas consumen un poco de la red (servicios auxiliares) y ESIOS lo muestra como generación negativa. No es producción vendida y distorsionaría el precio capturado. |
| 11 | Unión con ESIOS mediante **left join** sobre la hora UTC | Los precios son la tabla base; si falta un dato de solar, la hora se conserva con solar vacía. La cobertura se informa en `calidad_datos.md`. |
| 12 | `capture_rate` calculado contra el baseload **de las mismas horas** con dato solar | Si faltan horas de solar, comparar con el baseload de todas las horas sesgaría la ratio. |
| 13 | Año completo si tiene **≥ 8.760 horas** | 2026 llega solo hasta el 31/10; hay que marcarlo para no compararlo directamente con años completos (sobre todo en sumas como GWh o ingreso de la batería). |
| 14 | Batería de **1 MW / 4 MWh**, eficiencia **0,88**, **un ciclo al día** | Configuración típica de los proyectos actuales de almacenamiento (4 h de duración, ion-litio). Resultados expresados por MW para escalarlos. |
| 15 | Carga en las 4 horas más baratas y descarga en las 4 más caras; margen = descarga × 4 − carga × 4 / 0,88, mínimo 0 | Para entregar 4 MWh hay que comprar 4 / 0,88 MWh. Si el margen sale negativo el operador no cicla ese día. |
| 16 | **Limitación:** no se exige que la carga vaya antes que la descarga | Simplificación. Si las horas caras van antes que las baratas el ingreso está sobrestimado. En la práctica el patrón típico (barato a mediodía, caro por la tarde-noche) cumple el orden, pero el resultado debe leerse como un **techo** del arbitraje en el mercado diario. Tampoco se incluyen servicios de ajuste, degradación ni peajes. |
| 17 | Usar la **versión más alta** de cada fichero diario de OMIE (`.1`, `.2`, `.3`…) | OMIE republica algunos días corregidos. En este periodo, 4 días solo existen como versión corregida (07/01/2020, 28/05/2023, 30/10/2025 y 27/11/2025). Si falta la `.1`, se prueban de la `.2` a la `.5`. |
| 18 | Fecha final fija (31/10/2026) | Reproducibilidad: cualquier persona que ejecute el código obtiene los mismos resultados. |

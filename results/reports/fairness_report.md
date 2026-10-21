# Auditoria por subgrupos de la regresion de referencia

## Alcance

Se audita LR_base, el mismo procedimiento de regresion logistica de las entregas
anteriores. Se reutilizan sus 3.539 predicciones fuera de entrenamiento (OOF)
verificadas, sin reentrenar ni cambiar el ranking. Esta auditoria no selecciona
un modelo final. La reserva de 885 casos no participa.

La seleccion conserva el 20% redondeado hacia arriba dentro de cada fold,
no el 20% de cada subgrupo. Edad conserva los intervalos del EDA. Nacionalidad
mantiene cada codigo, sin fusionar grupos despues de observar sus resultados.
Beca y deuda son atributos de auditoria retrospectiva, no predictores.

## Definiciones

- Tasa de seleccion: priorizados / total del grupo.
- Cobertura: abandonos priorizados / abandonos reales del grupo.
- FPR del ranking: priorizados sin abandono registrado / casos sin abandono registrado.
- Fraccion de error de la lista: priorizados sin abandono registrado / priorizados.
- FPR del clasificador: predicciones de clase Dropout incorrectas / casos sin abandono registrado.

Los dos ultimos indicadores y todos los conteos se incluyen en el CSV.
FPR del ranking y del clasificador son decisiones diferentes. Enrolled se
considera no abandono **al corte del dataset**, no exito definitivo; por eso
se separan los seleccionados Enrolled y Graduate. No se interpreta priorizar
a un estudiante Enrolled como una ayuda necesariamente innecesaria.

## Resultado global y comparacion aleatoria

Se priorizan 710 de 3539 estudiantes y se detectan
452 de 1137 abandonos: cobertura agrupada
**39.7537%**. El 39.7527%
publicado anteriormente es la **media no ponderada de cinco folds**. Son
agregaciones distintas de las mismas predicciones, no resultados contradictorios.

Un ranking uniforme aleatorio con el mismo cupo por fold detectaria en esperanza
228.11 abandonos, cobertura
20.0622%. La cobertura observada equivale a
1.98 veces esa esperanza.
Esto no es una prueba de significacion ni evidencia de reduccion causal del abandono.

## Como interpretar los intervalos

Se presentan intervalos marginales de Wilson al 95%, calculados con el numerador
y denominador propios de cada tasa. Un denominador cero es **no estimable**, no
0%. El CSV marca denominadores menores de 30 como advertencia descriptiva, no
como un umbral de significacion. No se publican filas individuales nuevas.

Estos intervalos binomiales son aproximaciones descriptivas: el cupo fijo induce
dependencia y los modelos de los folds comparten entrenamiento. No incorporan
la variabilidad del ajuste ni corrigen comparaciones multiples. Su solapamiento
no prueba igualdad y su separacion no demuestra discriminacion causal.

## Hallazgos que requieren revision

La cobertura en menores de 20 anos es 13.46% [10.18; 17.58],
frente a 76.04% [69.53; 81.53] en estudiantes de 35 o mas.
El sistema deja fuera a 283 de los
327 abandonos del grupo mas joven. La mayor cobertura del grupo
de mayor edad viene acompanada de una FPR del ranking de
46.39% [38.97; 53.97]; detectar mas no implica ausencia de errores.

En necesidades especiales, codigo 1, solo hay 41 casos y
13 abandonos. Se detectan 3,
con cobertura 23.08% [8.18; 50.26]. La incertidumbre impide
extraer conclusiones firmes sobre este grupo. Las tablas de genero y beca
tambien muestran coberturas distintas; merecen seguimiento, no una declaracion
automatica de equidad. Beca no interviene como predictor en este modelo.

## Total

| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |
|---|---:|---:|---:|---|---|---|
| Todos | 3539 | 710 | 452/1137 | 20.06% [18.78; 21.41] | 39.75% [36.95; 42.63] | 10.74% [9.56; 12.04] |

## Genero (codigo)

| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |
|---|---:|---:|---:|---|---|---|
| 1 | 1241 | 433 | 285/556 | 34.89% [32.29; 37.59] | 51.26% [47.11; 55.39] | 21.61% [18.69; 24.84] |
| 0 | 2298 | 277 | 167/581 | 12.05% [10.79; 13.45] | 28.74% [25.21; 32.55] | 6.41% [5.34; 7.66] |

## Edad

| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |
|---|---:|---:|---:|---|---|---|
| 20-24 | 1056 | 146 | 84/308 | 13.83% [11.87; 16.04] | 27.27% [22.60; 32.50] | 8.29% [6.52; 10.48] |
| 35 o mas | 358 | 223 | 146/192 | 62.29% [57.16; 67.16] | 76.04% [69.53; 81.53] | 46.39% [38.97; 53.97] |
| Menos de 20 | 1579 | 80 | 44/327 | 5.07% [4.09; 6.26] | 13.46% [10.18; 17.58] | 2.88% [2.08; 3.95] |
| 25-34 | 546 | 261 | 178/310 | 47.80% [43.64; 51.99] | 57.42% [51.86; 62.80] | 35.17% [29.36; 41.45] |

## Nacionalidad (codigo)

| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |
|---|---:|---:|---:|---|---|---|
| 1 | 3453 | 696 | 446/1114 | 20.16% [18.85; 21.53] | 40.04% [37.20; 42.94] | 10.69% [9.50; 12.01] |
| 26 | 12 | 0 | 0/1 | 0.00% [0.00; 24.25] | 0.00% [0.00; 79.35] | 0.00% [0.00; 25.88] |
| 22 | 10 | 2 | 1/4 | 20.00% [5.67; 50.98] | 25.00% [4.56; 69.94] | 16.67% [3.01; 56.35] |
| 41 | 26 | 3 | 2/7 | 11.54% [4.00; 28.98] | 28.57% [8.22; 64.11] | 5.26% [0.94; 24.64] |
| 6 | 13 | 3 | 1/4 | 23.08% [8.18; 50.26] | 25.00% [4.56; 69.94] | 22.22% [6.32; 54.74] |
| 21 | 2 | 0 | 0/1 | 0.00% [0.00; 65.76] | 0.00% [0.00; 79.35] | 0.00% [0.00; 79.35] |
| 24 | 3 | 1 | 0/1 | 33.33% [6.15; 79.23] | 0.00% [0.00; 79.35] | 50.00% [9.45; 90.55] |
| 62 | 2 | 0 | 0/0 | 0.00% [0.00; 65.76] | No estimable | 0.00% [0.00; 65.76] |
| 11 | 3 | 0 | 0/0 | 0.00% [0.00; 56.15] | No estimable | 0.00% [0.00; 56.15] |
| 103 | 2 | 1 | 0/1 | 50.00% [9.45; 90.55] | 0.00% [0.00; 79.35] | 100.00% [20.65; 100.00] |
| 105 | 2 | 0 | 0/1 | 0.00% [0.00; 65.76] | 0.00% [0.00; 79.35] | 0.00% [0.00; 79.35] |
| 101 | 2 | 1 | 1/1 | 50.00% [9.45; 90.55] | 100.00% [20.65; 100.00] | 0.00% [0.00; 79.35] |
| 100 | 3 | 2 | 1/2 | 66.67% [20.77; 93.85] | 50.00% [9.45; 90.55] | 100.00% [20.65; 100.00] |
| 32 | 1 | 0 | 0/0 | 0.00% [0.00; 79.35] | No estimable | 0.00% [0.00; 79.35] |
| 14 | 1 | 0 | 0/0 | 0.00% [0.00; 79.35] | No estimable | 0.00% [0.00; 79.35] |
| 25 | 1 | 1 | 0/0 | 100.00% [20.65; 100.00] | No estimable | 100.00% [20.65; 100.00] |
| 13 | 1 | 0 | 0/0 | 0.00% [0.00; 79.35] | No estimable | 0.00% [0.00; 79.35] |
| 108 | 1 | 0 | 0/0 | 0.00% [0.00; 79.35] | No estimable | 0.00% [0.00; 79.35] |
| 2 | 1 | 0 | 0/0 | 0.00% [0.00; 79.35] | No estimable | 0.00% [0.00; 79.35] |

## Necesidades especiales (codigo)

| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |
|---|---:|---:|---:|---|---|---|
| 0 | 3498 | 705 | 449/1124 | 20.15% [18.86; 21.52] | 39.95% [37.12; 42.84] | 10.78% [9.60; 12.10] |
| 1 | 41 | 5 | 3/13 | 12.20% [5.32; 25.54] | 23.08% [8.18; 50.26] | 7.14% [1.98; 22.65] |

## Beca (codigo; solo auditoria)

| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |
|---|---:|---:|---:|---|---|---|
| 0 | 2645 | 647 | 425/1022 | 24.46% [22.86; 26.14] | 41.59% [38.60; 44.63] | 13.68% [12.09; 15.44] |
| 1 | 894 | 63 | 27/115 | 7.05% [5.55; 8.91] | 23.48% [16.67; 32.00] | 4.62% [3.36; 6.33] |

## Deuda (codigo; solo auditoria)

| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |
|---|---:|---:|---:|---|---|---|
| 0 | 3150 | 596 | 359/888 | 18.92% [17.59; 20.33] | 40.43% [37.25; 43.69] | 10.48% [9.28; 11.81] |
| 1 | 389 | 114 | 93/249 | 29.31% [25.00; 34.01] | 37.35% [31.58; 43.51] | 15.00% [10.03; 21.84] |

## Uso responsable de los resultados

Una tasa de seleccion distinta no basta para afirmar trato injusto: se debe
considerar prevalencia, cobertura, errores, tamano del grupo y contexto. Los
grupos pequenos requieren especial cautela; cero detecciones no significa
ausencia de riesgo. No se deben fijar cuotas ni excluir grupos a partir de
estas tablas. Los codigos conservan la nomenclatura del dataset original.

El resultado respalda revisar el prototipo antes de cualquier uso institucional,
mantener revision humana y ofrecer acceso voluntario al apoyo fuera del ranking.
No demuestra equidad, eficacia de una intervencion ni validez en Ecuador.

## Reproduccion

Ejecutar `python -m src.fairness`. [Conteos y tasas](../metrics/fairness_subgroups.csv)
y [evidencia JSON](../metrics/fairness_results.json) se generan desde las mismas
predicciones verificadas. El procedimiento conserva el modelo y los resultados
historicos; no modifica hiperparametros a partir de la auditoria.

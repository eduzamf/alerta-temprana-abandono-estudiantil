# Seleccion del modelo para el prototipo

## Decision basada en desarrollo

Se selecciona **LR_base**, regresion logistica con C=1, ponderacion balanced,
max_iter=3000 y semilla 42. Conserva las 18 variables de matricula, imputacion
aprendida en entrenamiento, escalado numerico y codificacion one-hot sin
agrupacion. No agrega interacciones ni calibracion posterior.

La decision se fija antes de evaluar las 885 observaciones de reserva. Los
resultados siguientes son medias de los cinco folds de desarrollo, no prueba.

| Alternativa | F1 macro validacion | Brecha F1 entrenamiento-validacion | Cobertura 20% |
|---|---:|---:|---:|
| LR original | 0,51584 | 0,05902 | 39,75% |
| LR cuadratica, ajuste anidado | 0,51777 | 0,05152 | 40,28% |
| RF original | 0,51996 | 0,26061 | 39,14% |
| RF regularizado, ajuste anidado | 0,51792 | 0,09892 | 39,67% |

## Justificacion y compromisos

RF original obtiene el mayor F1 observado, pero su ventaja de aproximadamente
0,0041 sobre LR viene acompanada de una brecha de sobreajuste mucho mayor.
Regularizar RF reduce esa brecha sin mejorar su F1 medio. LR cuadratica agrega
terminos numericos y una busqueda de C para una diferencia de F1 de 0,00193.
No se ha demostrado que estas pequenas diferencias sean estadisticamente
concluyentes; tampoco se ha probado equivalencia entre modelos.

Se prioriza la menor complejidad de LR original, su trazabilidad con las
entregas anteriores y la evidencia ya disponible de subgrupos y robustez.
Esto es una decision de ingenieria posterior a las comparaciones en desarrollo,
no una regla de equivalencia preestablecida ni una victoria en todas las metricas.
No se atribuye a RF o LR cuadratica la auditoria realizada solo sobre LR original.

La seleccion no elimina sus limitaciones: sesgo alto o informacion limitada,
coberturas desiguales por grupo y deterioro ante entradas desplazadas. No se
alcanzo la meta F1 de 0,60 en validacion. Las puntuaciones no estan calibradas;
la interfaz debera presentarlas como puntuaciones de priorizacion, no como
probabilidades clinicas o certezas individuales.

## Entrenamiento del artefacto

Una vez registrada la decision, se ajusta un unico pipeline con las 3.539 filas
de desarrollo. La reserva queda excluida de imputacion, escalado, aprendizaje
de categorias y clasificacion. El pipeline se serializa junto a metadatos,
versiones, lista de variables, indices de entrenamiento y huellas SHA-256.

Se comprobara que cargar el artefacto conserva sus predicciones y que su
contrato coincide con la configuracion fijada. Estas verificaciones tecnicas
no son una medicion de rendimiento en prueba. No se mezclaran metricas de
entrenamiento del artefacto con las medias de validacion anteriores.

## Protocolo fijado para la prueba final

Se evaluara exclusivamente este artefacto sobre las 885 filas del manifiesto
historico, conservando el orden de train_test_split con semilla 42.
La clase predicha usa el clasificador sin ajuste de umbrales. El ranking usa
la puntuacion Dropout y selecciona ceil(0,20*n), con desempate estable segun
el orden historico. No se reajustara ningun componente con la reserva.

Se reportaran F1 macro, accuracy, log-loss, metricas por clase, matriz de
confusion y cobertura de abandono en el 20% priorizado, junto con conteos.
El criterio principal es F1 macro >= 0,60. Se informara si se cumple o no,
sin cambiar el objetivo despues de conocer el resultado.

La comparacion aleatoria usara la esperanza de cobertura k/n del mismo cupo.
No se probaran otros candidatos en la reserva para escoger el mejor ni se
ajustara C, calibracion, variables o umbrales despues de observarla. Recalcular
metricas desde predicciones guardadas sera auditoria, no otra seleccion.
La prueba mide generalizacion interna en esta particion aleatoria, no validez
temporal, causal ni transferencia institucional a Ecuador.

## Evidencia

El artefacto se entreno y verifico con las 3.539 filas de desarrollo, sin
advertencias de entrenamiento. La serializacion conserva exactamente las
predicciones. [Modelo y metadatos](../models/README.md). Esta comprobacion no
incluye evaluar la reserva ni demostrar la meta de F1.

- [Modelos base](../results/reports/baseline_report.md)
- [Optimizacion anidada](optimizacion.md)
- [Subgrupos de LR](../results/reports/fairness_report.md)
- [Robustez de LR](robustez.md)
- [Configuracion fijada](../config/final_model.json)

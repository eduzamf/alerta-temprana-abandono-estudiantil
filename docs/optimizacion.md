# Optimizacion y validacion

## Protocolo definido antes de ejecutar

Configuracion: [config/optimization.json](../config/optimization.json), version
2026-10-21-v1. Se conservan las 18 variables, los cinco folds historicos y la
reserva final de 885 filas. No se usan datos de la reserva en estos experimentos.

El diagnostico de referencia identifica sobreajuste en Random Forest y sesgo
alto o senal limitada en la regresion. Se comparan dos estrategias:

| Estrategia | Hipotesis | Configuraciones |
|---|---|---|
| RF regularizado | Limitar capacidad puede reducir la brecha de sobreajuste | 100/200 arboles; profundidad 4/8/16; hoja minima 5/15/30: 18 combinaciones |
| LR cuadratica | Relaciones no lineales e interacciones numericas pueden reducir el sesgo | Grado 2 en cuatro variables numericas; C=0,1/1/10: 3 combinaciones |

La expansion cuadratica conserva las cuatro variables numericas, agrega sus
cuadrados y seis interacciones (14 terminos). No multiplica codigos nominales.
La imputacion precede a la expansion y el escalado se ajusta despues. Las
categorias conservan one-hot sin agrupacion. Ambas estrategias usan ponderacion
balanced y semilla 42. LR conserva max_iter=3000 y se registran advertencias.

Dentro de cada fold externo se crean tres folds estratificados internos con
semilla 142 + numero de fold. Cada candidato se ajusta con todo su pipeline en
entrenamiento interno, sin reutilizar transformaciones aprendidas globalmente.

Seleccion interna: mayor F1 macro medio, luego mayor cobertura al 20% si hay
empate exacto. En un empate restante, RF prefiere menos arboles, menor profundidad
y mayor hoja minima; LR prefiere menor C. El ganador se reajusta con todo el
entrenamiento externo y se evalua una vez en su validacion externa.

Las medias externas se comparan con los modelos base sobre los mismos folds.
Se publican F1 de entrenamiento/validacion, brecha, cobertura y cambios por fold.
La desviacion estandar no es un intervalo de confianza y los folds no son
experimentos independientes. La comparacion de familias es exploratoria; la
configuracion final y la evaluacion de prueba se reservan para una fase posterior.

La sensibilidad se describira con resultados internos: curvas por parametro,
PDP de un modelo auxiliar del rendimiento, importancia de sus parametros e
interaccion profundidad-hoja. No se utilizaran resultados externos para volver
a elegir rangos en esta ejecucion. El modelo auxiliar no predice abandono.

Estado inicial del protocolo: resultados pendientes. Las pruebas de estres,
calibracion, equidad, seleccion definitiva y evaluacion de reserva no forman
parte de esta ejecucion y siguen pendientes.

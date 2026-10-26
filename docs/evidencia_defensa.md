# Evidencia para la defensa tecnica

## Importancia de variables y prevencion de fuga

La [auditoria por permutacion](../results/reports/feature_importance.md) responde
a importancia de entradas, no de hiperparametros. Modalidad de ingreso y
carrera encabezan la caida media de F1 macro: 0,07044 y 0,06390. Edad, ocupacion
materna y nota de admision siguen con diferencias pequenas entre ellas.

La asociacion con trayectorias de acceso y contexto de carrera es plausible,
pero no se realizo una validacion de esas explicaciones con especialistas.
No debe afirmarse que estas variables causen abandono ni que su importancia
se transfiera a Ecuador. Los factores correlacionados pueden repartir la
importancia; permutar puede crear perfiles poco plausibles.

Las particiones y folds son los historicos. Imputacion, escalado y codificacion
se ajustan solo en el entrenamiento de cada fold. Se excluyen variables
posteriores a la matricula y no se usaron resultados de prueba para seleccionar
configuraciones. Esta auditoria posterior no modifica las variables elegidas.

## Caso de fallo predictivo real

El registro publico con indice de origen **3439** tiene etiqueta real Dropout,
pero la prediccion final guardada es Enrolled y queda fuera del cupo del 20%.
Sus puntuaciones son Dropout 0,23322, Enrolled 0,40968 y Graduate 0,35710.
La clase estimada sigue la mayor puntuacion; ninguna garantiza un desenlace.

Fuente: [predicciones finales guardadas](../results/metrics/final_test_predictions.csv).
Seleccion del ejemplo: primer registro, en el orden guardado, con abandono
real, clase distinta de abandono y fuera del cupo. No se vuelve a ejecutar
inferencia ni se ajusta el modelo para corregir este ejemplo.

Esto muestra un falso negativo de clasificacion y una omision del ranking.
No se conoce la causa individual del abandono: los patrones aprendidos con
variables de ingreso no separan perfectamente las trayectorias. No se atribuye
el fallo a un atributo concreto sin un analisis que lo respalde. Tampoco se
inventa una historia personal. El indice del dataset no es el codigo CASO
que la interfaz asigna por posicion dentro de cada archivo cargado.

## Optimizacion: mejora y deterioro

| Modelo | F1 macro base en validacion | Variante, validacion externa anidada | Diferencia aproximada |
|---|---:|---:|---:|
| LR | 0,51584 | 0,51777 | +0,00193 |
| RF | 0,51996 | 0,51792 | -0,00204 |

El mayor peso descriptivo en la superficie de hiperparametros de RF corresponde
a min_samples_leaf (0,583). No es importancia de variables del estudiante ni
un efecto causal. Reducir sobreajuste no implica automaticamente mejorar F1.
Ver [metodo, dispersion y resultados completos](optimizacion.md).

## Error de entrada frente a error predictivo

Un CSV rechazado por carrera desconocida demuestra validacion de entradas,
no demuestra un error de prediccion del modelo. Para la interfaz se usan los
[ejemplos de demostracion](../data/examples/README.md). Para discutir fallos
predictivos se usa evidencia etiquetada, como el caso anterior.

La prueba final conserva F1 macro 0,49366 y cobertura 114/284; no se cambian
esas cifras para presentar el proyecto. La ausencia de sobreajuste grande en
LR tampoco prueba validez local, temporal ni eficacia de una intervencion.

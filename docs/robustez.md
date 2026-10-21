# Robustez de la regresion de referencia

## Protocolo previo a la ejecucion

Se conserva LR_base, las 18 variables y los cinco folds historicos de desarrollo.
Las 885 filas de prueba no intervienen. Se utiliza el mismo modelo de referencia
que en la auditoria por subgrupos, sin elegir parametros con estos resultados.

Tolerancias exploratorias: caida absoluta de F1 macro no mayor de 0,03 y de
cobertura al 20% no mayor de 0,05 respecto al escenario limpio comparable.
Ambos limites deben cumplirse. Son criterios de este experimento, no requisitos
institucionales validados ni pruebas de significacion. No se ajustaran despues
de observar resultados. Se reportaran medias y peores diferencias por fold.

| Escenario | Intervencion |
|---|---|
| clean | Validacion original; reproduce la referencia historica |
| missing10 | Ocultar al azar el 10% esperado de celdas predictoras |
| missing30 | Ocultar al azar el 30% esperado de celdas predictoras |
| grade_noise | Ruido normal en las dos notas, SD=0,2 por SD del entrenamiento; recorte a 0-200 |
| grades_absent | Ausencia completa de ambas notas en validacion |
| course_unseen | Sustituir Course por un codigo sintetico ausente del entrenamiento |
| grade_shift | Restar 20 puntos a ambas notas de validacion, con recorte a 0-200 |
| dropout50 | Submuestra con todos los Dropout y igual numero de otros casos, sin reemplazo |
| train_under35 | Reentrenar exclusivamente con menores de 35 del entrenamiento; validar en el fold original |

missing10, missing30, grade_noise y dropout50 usan tres semillas (71, 172, 273)
sumadas al numero de fold. Los demas escenarios son deterministas. Primero se
promedian repeticiones dentro de fold y luego los cinco folds con igual peso.
Las repeticiones no son nuevas muestras independientes.

Salvo train_under35, el pipeline se ajusta una vez por fold y se congela antes
de alterar la validacion. La imputacion, escalado y categorias no se reajustan.
train_under35 es un experimento de cambio de composicion del entrenamiento,
separado de la perturbacion de entradas. No equivale a una validacion temporal.

dropout50 cambia composicion y prevalencia de la evaluacion: su diferencia con
clean no aisla deterioro del clasificador. Las tolerancias se marcaran como
no aplicables en ese escenario; se reportan metricas y conteos descriptivos.
Los errores se calculan con las etiquetas originales, nunca modificadas.
Ninguna perturbacion simula completamente otra universidad o Ecuador.

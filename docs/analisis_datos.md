# Analisis de datos

Estado: integridad y particiones verificadas; EDA y graficos pendientes de integrar.

## Integridad y particiones

La auditoria reproduce las particiones historicas: 3.539 filas de desarrollo y 885 de reserva. Los cinco folds de validacion contienen 708, 708, 708, 708 y 707 filas. No se han evaluado modelos en la reserva.

En desarrollo hay 1.767 casos Graduate, 1.137 Dropout y 635 Enrolled. No se detectaron celdas nulas ni filas exactamente duplicadas en desarrollo; esto no descarta otros problemas de calidad. Enrolled es un estado no resuelto.

- [Fuente, licencia y reglas de uso](../data/README.md).
- [Evidencia generada por la auditoria](../results/metrics/data_audit.json).

Se mantienen los 18 predictores de matricula. Se excluyen resultados semestrales y seis variables de temporalidad no confirmada. El preprocesamiento estadistico se ajustara exclusivamente dentro de cada entrenamiento; no se ha ajustado ninguna transformacion en esta auditoria.

## Contenido requerido
- Fuente, licencia, dimensiones y diccionario de variables.
- Estadisticas descriptivas y al menos 5-6 graficos relevantes.
- Patrones, correlaciones, valores atipicos y desbalance.
- Justificacion del preprocesamiento.
- Disponibilidad temporal de las variables y prevencion de fuga.
- Particiones, identificadores y huella del archivo fuente.

La reserva final no se utilizara para explorar, ajustar ni seleccionar modelos.

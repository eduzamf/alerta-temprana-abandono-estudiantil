# Artefacto de la regresion logistica

`student_support_v1.joblib` contiene el pipeline completo: imputacion,
escalado, one-hot y clasificador LR_base. Se entrena exclusivamente con las
3.539 filas de desarrollo. `student_support_v1.json` registra configuracion,
versiones, indices, huellas y comprobacion de serializacion.

La seleccion se justifica en [la decision tecnica](../docs/seleccion_modelo.md).
El artefacto no es un sistema institucional validado. Sus puntuaciones no
estan calibradas y requiere los controles de entrada descritos en robustez.

Para entrenar si no existe o verificar si ya existe:
`python -m src.finalize`. La funcion de entrenamiento rechaza sobrescribir
un artefacto congelado. Verificar no evalua la reserva.

Solo cargar artefactos de procedencia confiable: joblib puede ejecutar codigo
al deserializar. La huella detecta cambios accidentales, no autentica un archivo
si un tercero sustituye tambien sus metadatos. Usar las versiones registradas
en requirements.txt.

# Casos para demostrar la interfaz

Los tres archivos parten de las mismas 40 filas publicas de desarrollo usadas
por la muestra de la aplicacion. No contienen Target ni identificadores.
Conservan la licencia y atribucion del [dataset UCI](../README.md).

1. 01_lote_valido.csv: sin alteraciones, 40 casos y 8 priorizados.
2. 02_nota_vacia.csv: se vacia Admission grade del primer registro. La aplicacion
   acepta el lote, informa una celda faltante e imputa con el pipeline entrenado.
3. 03_carrera_invalida.csv: se cambia Course del primer registro por 999999.
   La aplicacion rechaza el lote y no genera resultados exportables.

Las dos alteraciones son deliberadas para probar la interfaz, no datos
observados ni nuevos experimentos de rendimiento. No usar estos archivos para
recalcular F1. Generacion reproducible: python -m src.demo_cases.
Tambien se descargan desde Datos de entrada en la aplicacion.

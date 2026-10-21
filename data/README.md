# Datos y atribucion

## Fuente y licencia

Realinho, V., Vieira Martins, M., Machado, J., & Baptista, L. (2021).
*Predict Students' Dropout and Academic Success* [Dataset]. UCI Machine Learning Repository.
https://doi.org/10.24432/C5MC89

- [Fuente oficial y diccionario](https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success)
- [Licencia CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Fuente consultada: 20 de octubre de 2026.

La licencia permite compartir y adaptar con atribucion. No implica respaldo de los autores al prototipo ni sustituye la licencia del codigo.

## Archivos

`raw/data.csv` conserva los bytes usados en las entregas previas: 4.424 filas, 36 predictores y Target, separador `;`. No se editaron valores ni encabezados. El cargador elimina espacios marginales de encabezados solo en memoria; mantiene nombres originales, incluido `Nacionality`.

`processed/particiones.csv` es el manifiesto del proyecto, no una particion proporcionada por UCI. `row_index` es la posicion original base cero, no un identificador personal. La particion estratificada con semilla 42 conserva 3.539 filas de desarrollo y 885 de reserva. Los cinco folds estratificados de desarrollo usan tambien semilla 42. `cv_fold=-1` identifica la reserva.

Huellas SHA-256:

```text
raw/data.csv
3ef126de5cefff26eb11fbb4237f1a1401cb64b488e2f1d598c23cedeb4c45ae
processed/particiones.csv
421699f3d13e2f4d0096ed829ac971ee29ee7f694d300730df08414c2d39da14
```

`.gitattributes` evita conversiones de saltos de linea en ambos archivos.

## Uso durante el desarrollo

```python
from src.data_processing import FEATURES, load_development

development, folds = load_development()
X = development[FEATURES]
y = development["Target"]
```

La lista explicita contiene 18 predictores de matricula. Se excluyen los 12 indicadores semestrales y seis variables de temporalidad no confirmada: deuda, pagos al dia, beca y los tres indicadores economicos. El frame conserva columnas adicionales para auditoria; no pasarlo completo al modelo. Beca y deuda pueden estudiarse retrospectivamente sin convertirlas en predictores.

Se mantiene el orden historico de desarrollo para preservar los desempates de rankings. Las etiquetas originales solo se usan para verificar la particion historica; no se calculan predicciones, rendimiento ni estadisticas de variables de la reserva. El cargador es una barrera de procedimiento, no control de acceso: el CSV publico contiene todas las filas. La evaluacion de la reserva se realizara despues de fijar modelo y protocolo.

Enrolled es un estado no resuelto al corte de observacion, no graduacion ni abandono confirmado. Los datos de una institucion portuguesa no demuestran validez local en Ecuador.

## Privacidad

No agregar registros reales de estudiantes ni identificadores directos. El caracter publico del dataset no elimina riesgos de reidentificacion o discriminacion. `data/private/` esta excluida de Git, pero no constituye un sistema de seguridad. No utilizar la reserva final como ejemplos de la interfaz.

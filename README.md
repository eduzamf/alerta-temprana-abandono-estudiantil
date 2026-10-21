# Alerta temprana de abandono estudiantil

Prototipo académico de inteligencia artificial para identificar estudiantes que podrían necesitar apoyo para continuar sus estudios, usando información disponible al momento de la matrícula.

**Autor:** Carlos Zambrano Figueroa. **Grupo:** 11, trabajo individual.

**Estado:** datos, EDA, preprocesamiento y modelos base reproducidos. Todavía no hay una aplicación ejecutable ni un modelo final seleccionado. La optimización y la documentación restante están en desarrollo.

## Contenido

- [Problema y alcance](#problema-y-alcance)
- [Estructura](#estructura)
- [Documentación](#documentación)
- [Datos y resultados](#datos-y-resultados)
- [Instalación y pruebas](#instalación-y-pruebas)
- [Licencias](#licencias)
- [Videos](#videos)

## Problema y alcance

El proyecto busca apoyar la revisión humana y la oferta de acompañamiento académico voluntario. No determina sanciones, admisiones ni acceso a beneficios. Su eficacia para reducir el abandono y su validez en instituciones de Ecuador no están demostradas.

## Estructura

```text
docs/                 Documentación técnica y manual
data/raw/             Datos originales autorizados
data/processed/       Datos derivados reproducibles
notebooks/            Exploración, preparación, modelado y evaluación
src/                  Código modular del sistema
models/               Modelos entrenados y registro de versiones
app/assets/           Interfaz y recursos visuales
tests/                Pruebas unitarias
results/figures/       Gráficos generados
results/metrics/       Métricas verificables
results/reports/       Reportes derivados
```

Los archivos `.gitkeep` permiten registrar carpetas inicialmente vacías. La carga, el EDA, el preprocesamiento y los modelos base están implementados, con 44 pruebas automatizadas. Los notebooks 01, 02 y 03 están ejecutados; la optimización, evaluación final e interfaz siguen pendientes.

## Documentación

- [Planificación](docs/planificacion.md)
- [Análisis de datos](docs/analisis_datos.md)
- [Arquitectura](docs/arquitectura.md)
- [Optimización](docs/optimizacion.md)
- [Consideraciones éticas](docs/consideraciones_eticas.md)
- [Manual de usuario](docs/manual_usuario.md)

## Datos y resultados

Dataset incorporado: *Predict Students' Dropout and Academic Success*, UCI, bajo CC BY 4.0. [Fuente, atribución, particiones y reglas de uso](data/README.md).

La auditoría confirma 4.424 filas: 3.539 de desarrollo y 885 de reserva; se conservan los cinco folds históricos y las 18 variables predictoras. [Auditoría reproducible](results/metrics/data_audit.json). Estos conteos no son métricas de rendimiento.

El [análisis exploratorio](docs/analisis_datos.md) incluye siete figuras y tablas sobre clases, distribuciones, valores atípicos, correlaciones, categorías y subgrupos. Utiliza únicamente desarrollo. La representación demográfica no se presenta como una evaluación de equidad del modelo.

Los modelos base reproducen los resultados históricos: F1 macro medio de 0,51584 para regresión logística y 0,51996 para Random Forest, frente a 0,22201 de Dummy prior. Son cifras de validación, no de prueba final. [Resultados, cobertura, diagnóstico y gráficos](results/reports/baseline_report.md). La reserva permanece sin evaluar; no se ha seleccionado el modelo final.

## Instalación y pruebas

La auditoría se verificó con Python 3.11.8 y las versiones de `requirements.txt`. Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.data_processing
.\.venv\Scripts\python.exe -m src.eda
.\.venv\Scripts\python.exe -m src.preprocessing_audit
.\.venv\Scripts\python.exe -m src.train
.\.venv\Scripts\python.exe -m src.verify
.\.venv\Scripts\python.exe -m src.baseline_report
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En otros sistemas usar `.venv/bin/python`. La auditoría genera `results/metrics/data_audit.json`. El EDA genera `results/metrics/eda.json`, siete figuras y `docs/analisis_datos.md`; editar la plantilla en `src/eda.py` si se modifica esa documentación. La auditoría de preprocesamiento genera `results/metrics/preprocessing_audit.json`. El entrenamiento guarda predicciones OOF, registros y métricas en `results/metrics/baseline_*`; el reporte y sus tres gráficos se generan con `src.baseline_report`. Las 44 pruebas cubren datos, transformaciones, métricas y contratos de modelos; no certifican todavía la interfaz ni la validez institucional. Las pruebas de resultados guardados requieren esos archivos, incluidos en el repositorio o regenerados con `src.train`.

Para ejecutar un notebook sin una interfaz Jupyter, desde la raíz del repositorio (cambiar el nombre por `02_preprocesamiento.ipynb` o `03_modelado.ipynb` para los siguientes):

```powershell
.\.venv\Scripts\python.exe -c "import nbformat; from nbclient import NotebookClient; p='notebooks/01_exploracion.ipynb'; n=nbformat.read(p, as_version=4); NotebookClient(n, timeout=180, kernel_name='python3').execute(); nbformat.write(n,p)"
```

No cargar datos personales reales ni credenciales en este repositorio público.

## Licencias

La licencia del código está pendiente de decisión del autor; no se concede aquí una licencia de reutilización. Se incorporará `LICENSE` cuando se elija. Los datos tienen una licencia independiente, que se documentará con su atribución.

## Videos

- Pitch de máximo 5 minutos: pendiente.
- Respuestas a las preguntas de la profesora: pendiente.

Los enlaces se agregarán cuando existan las grabaciones reales.

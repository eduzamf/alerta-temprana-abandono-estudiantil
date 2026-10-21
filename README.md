# Alerta temprana de abandono estudiantil

Prototipo académico de inteligencia artificial para identificar estudiantes que podrían necesitar apoyo para continuar sus estudios, usando información disponible al momento de la matrícula.

**Autor:** Carlos Zambrano Figueroa. **Grupo:** 11, trabajo individual.

**Estado:** regresión logística seleccionada y entrenada con desarrollo, con artefacto verificable. Se incluyen experimentos, optimización, subgrupos y robustez. La reserva final no se ha evaluado; el prototipo no constituye una aplicación institucional validada.

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

Los archivos `.gitkeep` permiten registrar carpetas inicialmente vacías. Los experimentos y el artefacto seleccionado están implementados, con 70 pruebas automatizadas. Los notebooks 01 a 04 están ejecutados; la evaluación final e interfaz no forman parte de esta versión.

## Documentación

- [Planificación](docs/planificacion.md)
- [Análisis de datos](docs/analisis_datos.md)
- [Arquitectura](docs/arquitectura.md)
- [Optimización](docs/optimizacion.md)
- [Robustez](docs/robustez.md)
- [Selección del modelo y protocolo final](docs/seleccion_modelo.md)
- [Consideraciones éticas](docs/consideraciones_eticas.md)
- [Manual de usuario](docs/manual_usuario.md)

## Datos y resultados

Dataset incorporado: *Predict Students' Dropout and Academic Success*, UCI, bajo CC BY 4.0. [Fuente, atribución, particiones y reglas de uso](data/README.md).

La auditoría confirma 4.424 filas: 3.539 de desarrollo y 885 de reserva; se conservan los cinco folds históricos y las 18 variables predictoras. [Auditoría reproducible](results/metrics/data_audit.json). Estos conteos no son métricas de rendimiento.

El [análisis exploratorio](docs/analisis_datos.md) incluye siete figuras y tablas sobre clases, distribuciones, valores atípicos, correlaciones, categorías y subgrupos. Utiliza únicamente desarrollo. La representación demográfica no se presenta como una evaluación de equidad del modelo.

Los modelos base reproducen los resultados históricos: F1 macro medio de 0,51584 para regresión logística y 0,51996 para Random Forest, frente a 0,22201 de Dummy prior. Son cifras de validación, no de prueba final. [Resultados, cobertura, diagnóstico y gráficos](results/reports/baseline_report.md). La reserva permanece sin evaluar. Se seleccionó LR original por el compromiso documentado entre complejidad, rendimiento y trazabilidad; no por obtener el mayor F1.

El [artefacto entrenado](models/README.md) conserva el pipeline completo y metadatos verificables. Se ajustó exclusivamente con las 3.539 filas de desarrollo; sus puntuaciones no están calibradas.

## Instalación y pruebas

Las [pruebas de robustez](docs/robustez.md) incluyen nueve escenarios y 85 evaluaciones de validación. La regresión excede la tolerancia de caída de F1 al ocultar cerca del 30% de las celdas, usar carreras desconocidas o desplazar las notas. No se modificaron las tolerancias después de observar resultados.

La [auditoría por subgrupos](results/reports/fairness_report.md) analiza la regresión original con conteos e intervalos de Wilson. Incluye género, edad, nacionalidad, necesidades especiales, beca y deuda. No certifica equidad ni modifica el modelo. Los conteos agrupados se distinguen de las medias históricas por fold.

La [optimización anidada](docs/optimizacion.md) limita el sobreajuste de Random Forest y evalúa relaciones cuadráticas en la regresión. Sus F1 de validación son 0,51792 y 0,51777, respectivamente: no alcanzan 0,60 ni demuestran una mejora concluyente frente a las bases. Se verifican 7.078 predicciones externas; la reserva sigue sin evaluar.

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
.\.venv\Scripts\python.exe -m src.optimize
.\.venv\Scripts\python.exe -c "from src.optimize import verify; print(verify())"
.\.venv\Scripts\python.exe -m src.optimization_report
.\.venv\Scripts\python.exe -m src.fairness
.\.venv\Scripts\python.exe -m src.stress
.\.venv\Scripts\python.exe -m src.finalize
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En otros sistemas usar `.venv/bin/python`. La auditoría genera `results/metrics/data_audit.json`. El EDA genera `results/metrics/eda.json`, siete figuras y `docs/analisis_datos.md`; editar la plantilla en `src/eda.py` si se modifica esa documentación. La auditoría de preprocesamiento genera `results/metrics/preprocessing_audit.json`. El entrenamiento guarda predicciones OOF, registros y métricas en `results/metrics/baseline_*`; el reporte y sus tres gráficos se generan con `src.baseline_report`.

La optimización genera `results/metrics/optimization_*`; `src.optimization_report` genera cinco figuras y la sección de resultados de `docs/optimizacion.md`. La auditoría genera `results/metrics/fairness_*` y su reporte. La robustez genera `results/metrics/stress_*`, un gráfico y los resultados en `docs/robustez.md`. Las 70 pruebas cubren también el artefacto congelado; no certifican la interfaz ni la validez institucional. Los resultados están incluidos o se regeneran con `src.train`, `src.optimize`, `src.fairness` y `src.stress`. `src.finalize` entrena si no hay artefacto y verifica el existente sin sobrescribirlo.

Para ejecutar un notebook sin una interfaz Jupyter, desde la raíz del repositorio (cambiar el nombre por `02_preprocesamiento.ipynb`, `03_modelado.ipynb` o `04_optimizacion.ipynb` para los siguientes). El notebook 04 verifica resultados guardados por defecto; permite repetir la búsqueda con `RETRAIN=True`:

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

# Alerta temprana de abandono estudiantil

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB)
[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-526340)](LICENSE)
![Modalidad local](https://img.shields.io/badge/Demo-local-555555)

Prototipo académico de inteligencia artificial para identificar estudiantes que podrían necesitar apoyo para continuar sus estudios, usando información disponible al momento de la matrícula.

**Autor:** Carlos Zambrano Figueroa. **Grupo:** 11, trabajo individual.

## Aplicación local

Con las dependencias instaladas, ejecutar desde la raíz:

```powershell
python -m app.app --port 5057
```

Abrir http://127.0.0.1:5057. La muestra inicial contiene 40 registros públicos
de desarrollo. Permite cargar CSV, revisar casos y descargar el ranking.
No guarda archivos cargados y no debe recibir datos personales reales.
[Manual, requisitos de entrada y capturas](docs/manual_usuario.md).

**Estado:** regresión logística entrenada y evaluada en los 885 casos de prueba final. F1 macro: **0,49366**; meta de 0,60 **no alcanzada**. Se incluyen experimentos, optimización, subgrupos y robustez. El prototipo no constituye una aplicación institucional validada.

## Contenido

- [Problema y alcance](#problema-y-alcance)
- [Estructura](#estructura)
- [Documentación](#documentación)
- [Datos y resultados](#datos-y-resultados)
- [Metodologia](#metodologia)
- [Interfaz](#interfaz)
- [Etica y limitaciones](#etica-y-limitaciones)
- [Instalación y pruebas](#instalación-y-pruebas)
- [Autor y contribuciones](#autor-y-contribuciones)
- [Licencias](#licencias)
- [Referencias](#referencias)
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

Los experimentos, el artefacto, la evaluación final y la aplicación local están implementados, con 93 pruebas Python y un recorrido automatizado de navegador. Los cinco notebooks están ejecutados. La interfaz usa el modelo fijo, sin entrenar con los archivos cargados.

## Documentación

- [Planificación](docs/planificacion.md)
- [Análisis de datos](docs/analisis_datos.md)
- [Arquitectura](docs/arquitectura.md)
- [Optimización](docs/optimizacion.md)
- [Robustez](docs/robustez.md)
- [Selección del modelo y protocolo final](docs/seleccion_modelo.md)
- [Evaluación final](docs/evaluacion_final.md)
- [Consideraciones éticas](docs/consideraciones_eticas.md)
- [Manual de usuario](docs/manual_usuario.md)
- [Verificacion desde una copia limpia](docs/verificacion_tecnica.md)
- [Despliegue remoto y controles](docs/despliegue.md)

## Datos y resultados

Dataset incorporado: *Predict Students' Dropout and Academic Success*, UCI, bajo CC BY 4.0. [Fuente, atribución, particiones y reglas de uso](data/README.md).

La auditoría confirma 4.424 filas: 3.539 de desarrollo y 885 de reserva; se conservan los cinco folds históricos y las 18 variables predictoras. [Auditoría reproducible](results/metrics/data_audit.json). Estos conteos no son métricas de rendimiento.

El [análisis exploratorio](docs/analisis_datos.md) incluye siete figuras y tablas sobre clases, distribuciones, valores atípicos, correlaciones, categorías y subgrupos. Utiliza únicamente desarrollo. La representación demográfica no se presenta como una evaluación de equidad del modelo.

Los modelos base reproducen los resultados históricos: F1 macro medio de 0,51584 para regresión logística y 0,51996 para Random Forest, frente a 0,22201 de Dummy prior. Son cifras de validación, no de prueba final. [Resultados, cobertura, diagnóstico y gráficos](results/reports/baseline_report.md). Se seleccionó LR original por el compromiso documentado entre complejidad, rendimiento y trazabilidad; no por obtener el mayor F1.

En la [prueba final](docs/evaluacion_final.md), LR obtiene F1 macro 0,49366 y accuracy 0,52881. El ranking prioriza 177 casos e incluye 114 de 284 abandonos (40,14%). Se conservan 170 abandonos fuera del cupo. No se ajustó el modelo después de observar el resultado. Los documentos de experimentos anteriores describen el estado de la reserva en esas etapas; sus métricas siguen siendo de desarrollo.

El [artefacto entrenado](models/README.md) conserva el pipeline completo y metadatos verificables. Se ajustó exclusivamente con las 3.539 filas de desarrollo; sus puntuaciones no están calibradas.

## Instalación y pruebas

Requisitos de uso: Python 3.11, CPU y navegador actualizado. No se requiere
GPU ni Node para ejecutar la app. Windows fue el entorno comprobado; las
instrucciones POSIX se ofrecen como equivalencia, no como prueba en Linux.
Para la demo basta instalar requirements.txt y ejecutar app.app; no hace falta
repetir todas las busquedas. La evaluacion guardada no se usa para reajustar.

```powershell
git clone https://github.com/eduzamf/alerta-temprana-abandono-estudiantil.git
cd alerta-temprana-abandono-estudiantil
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.app --port 5057
```

Las [pruebas de robustez](docs/robustez.md) incluyen nueve escenarios y 85 evaluaciones de validación. La regresión excede la tolerancia de caída de F1 al ocultar cerca del 30% de las celdas, usar carreras desconocidas o desplazar las notas. No se modificaron las tolerancias después de observar resultados.

La [auditoría por subgrupos](results/reports/fairness_report.md) analiza la regresión original con conteos e intervalos de Wilson. Incluye género, edad, nacionalidad, necesidades especiales, beca y deuda. No certifica equidad ni modifica el modelo. Los conteos agrupados se distinguen de las medias históricas por fold.

La [optimización anidada](docs/optimizacion.md) limita el sobreajuste de Random Forest y evalúa relaciones cuadráticas en la regresión. Sus F1 de validación son 0,51792 y 0,51777, respectivamente: no alcanzan 0,60 ni demuestran una mejora concluyente frente a las bases. Se verifican 7.078 predicciones externas a los entrenamientos de cada fold; la reserva no intervino en esa optimización.

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
.\.venv\Scripts\python.exe -m src.final_evaluation
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En otros sistemas usar `.venv/bin/python`. La auditoría genera `results/metrics/data_audit.json`. El EDA genera `results/metrics/eda.json`, siete figuras y `docs/analisis_datos.md`; editar la plantilla en `src/eda.py` si se modifica esa documentación. La auditoría de preprocesamiento genera `results/metrics/preprocessing_audit.json`. El entrenamiento guarda predicciones OOF, registros y métricas en `results/metrics/baseline_*`; el reporte y sus tres gráficos se generan con `src.baseline_report`.

La optimización genera `results/metrics/optimization_*`; `src.optimization_report` genera cinco figuras y la sección de resultados de `docs/optimizacion.md`. La auditoría genera `results/metrics/fairness_*` y su reporte. La robustez genera `results/metrics/stress_*`, un gráfico y los resultados en `docs/robustez.md`. Las 93 pruebas cubren también el artefacto, la evaluación final y los controles de la aplicación; no certifican seguridad ni validez institucional. Los resultados de desarrollo se regeneran con `src.train`, `src.optimize`, `src.fairness` y `src.stress`. `src.finalize` verifica el modelo existente sin sobrescribirlo. `src.final_evaluation` verifica la prueba guardada; no vuelve a predecir si ya existe.

Los [tres casos de demostración](data/examples/README.md) permiten mostrar un lote
válido, una nota ausente admitida con advertencia y un código inválido rechazado.
Se regeneran con `python -m src.demo_cases` y se descargan desde la aplicación.

Para las pruebas opcionales de navegador, instalar Node, Chrome y las dependencias
de desarrollo con `npm install`; iniciar el servidor y ejecutar `npm run test:browser`.
Node y Playwright no se requieren para el uso normal de la aplicación.

Para ejecutar un notebook sin una interfaz Jupyter, desde la raíz del repositorio, cambiar el nombre por cualquiera de los cinco notebooks. El 04 verifica resultados guardados por defecto; el 05 verifica la prueba final sin volver a inferir ni entrenar:

```powershell
.\.venv\Scripts\python.exe -c "import nbformat; from nbclient import NotebookClient; p='notebooks/01_exploracion.ipynb'; n=nbformat.read(p, as_version=4); NotebookClient(n, timeout=180, kernel_name='python3').execute(); nbformat.write(n,p)"
```

No cargar datos personales reales ni credenciales en este repositorio público.

## Licencias

El codigo y la documentacion original se publican bajo [MIT](LICENSE), sin
garantia. Los datos UCI conservan [CC BY 4.0 y su atribucion](data/README.md);
MIT no sustituye esa licencia ni la de dependencias. Los iconos Lucide
conservan [su licencia](app/assets/lucide-LICENSE.txt). La licencia de
reutilizacion no certifica aptitud del sistema para decisiones educativas.

## Metodologia

Se excluyen variables semestrales y de temporalidad incierta. Cada fold aprende
imputacion mediana/moda, escalado de cuatro variables numericas y one-hot de
14 categorias. Se comparan Dummy, LR y RF; la optimizacion usa tres folds
internos dentro de cinco externos. RF reduce capacidad y LR incorpora
terminos cuadraticos. Ninguna variante demuestra una mejora concluyente:
se conserva LR original por complejidad, trazabilidad y evidencia disponible.

| Modelo | Evaluacion | F1 macro | Cobertura al 20% |
|---|---|---:|---:|
| Dummy prior | Media de validacion | 0,22201 | Ver reporte de referencias |
| LR original | Media de validacion | 0,51584 | 39,75% |
| RF original | Media de validacion | 0,51996 | 39,14% |
| LR cuadratica | Validacion externa anidada | 0,51777 | 40,28% |
| RF regularizado | Validacion externa anidada | 0,51792 | 39,67% |
| LR original congelada | Prueba final, 885 casos | **0,49366** | **40,14%** |

Las comparaciones entre candidatos corresponden a desarrollo; no se evaluaron
todos en prueba para escoger al ganador. F1 macro pondera por igual las tres
clases. La cobertura mide abandonos recuperados en el cupo, no eficacia de apoyo.
La meta F1 0,60 no se alcanza. La accuracy final es 0,52881.

## Interfaz

![Aplicacion local con ranking](docs/images/app_desktop.png)

Cargar muestra UCI muestra 40 casos publicos de desarrollo y prioriza ocho.
Datos de entrada ofrece plantilla y ejemplos. Analizar CSV valida y aplica el
modelo fijo; la flecha abre clase estimada, puntuaciones y entradas. Descargar
exporta el ranking completo. Evidencia del modelo presenta las metricas finales.
Ver [manual con capturas y errores](docs/manual_usuario.md).

La aplicacion se ejecuta en http://127.0.0.1:5057 en el equipo que la instala.
No hay un servicio publico alojado: localhost no es un enlace para otros equipos.
El evaluador puede clonar el repositorio y ejecutar la demo local documentada.

## Etica y limitaciones

Uso academico con datos publicos/sinteticos, revision humana y apoyo voluntario.
No usar para sanciones, admisiones o asignacion automatica de beneficios.
Se rechazan identificadores adicionales y no se guardan los lotes en el servidor.
La auditoria muestra coberturas desiguales; no se certifica equidad, calibracion,
transferencia a Ecuador ni cumplimiento juridico institucional.
Ver [riesgos, controles, LOPDP y monitoreo propuesto](docs/consideraciones_eticas.md).

## Autor y contribuciones

Carlos Zambrano Figueroa, Grupo 11, modalidad individual: definicion del alcance,
decisiones metodologicas, analisis, integracion y revision de la entrega.
Se emplearon herramientas de IA como apoyo en programacion, redaccion y
verificacion. Las metricas proceden de ejecuciones y predicciones conservadas,
no de estimaciones generadas. El apoyo no sustituye la responsabilidad
academica del autor ni constituye revision por expertos educativos.

## Referencias

- Realinho, Vieira Martins, Machado y Baptista (2021). [Dataset UCI 697](https://doi.org/10.24432/C5MC89).
- [scikit-learn: documentacion oficial](https://scikit-learn.org/stable/). Version utilizada: 1.6.1.
- [Flask: documentacion oficial](https://flask.palletsprojects.com/). Version utilizada: 3.1.2.
- [Lucide y atribucion de recursos](app/assets/THIRD_PARTY.md).
- Agradecimiento a la docente por la retroalimentacion metodologica y etica.
  Su evaluacion academica no implica aval institucional de uso.

## Videos

La entrega audiovisual comprende el pitch (maximo cinco minutos) y las
respuestas a preguntas asignadas por la profesora. Las grabaciones y sus
enlaces se incorporaran tras su realizacion; no forman parte de esta version
tecnica ni se presentan enlaces ficticios.

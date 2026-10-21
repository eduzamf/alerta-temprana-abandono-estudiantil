# Alerta temprana de abandono estudiantil

Prototipo académico de inteligencia artificial para identificar estudiantes que podrían necesitar apoyo para continuar sus estudios, usando información disponible al momento de la matrícula.

**Autor:** Carlos Zambrano Figueroa. **Grupo:** 11, trabajo individual.

**Estado:** datos y particiones históricas incorporados y verificados. Todavía no hay una aplicación ejecutable ni un modelo final incorporado. La documentación restante está en desarrollo.

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

Los archivos `.gitkeep` permiten registrar carpetas inicialmente vacías. El cargador de datos y sus ocho pruebas están implementados; los demás módulos y pruebas siguen pendientes. Los notebooks contienen únicamente orientación inicial.

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

Los resultados históricos se integrarán después de verificar sus archivos de origen y particiones. No se publican cifras finales todavía. Se distinguirán validación, optimización y prueba final, preservando esta última hasta fijar el protocolo.

## Instalación y pruebas

La auditoría se verificó con Python 3.11.8 y las versiones de `requirements.txt`. Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.data_processing
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En otros sistemas usar `.venv/bin/python`. La auditoría genera `results/metrics/data_audit.json`. Las ocho pruebas comprueban datos y particiones; no certifican todavía modelos ni interfaz. Las dependencias de la aplicación se incorporarán cuando se implemente y verifique.

No cargar datos personales reales ni credenciales en este repositorio público.

## Licencias

La licencia del código está pendiente de decisión del autor; no se concede aquí una licencia de reutilización. Se incorporará `LICENSE` cuando se elija. Los datos tienen una licencia independiente, que se documentará con su atribución.

## Videos

- Pitch de máximo 5 minutos: pendiente.
- Respuestas a las preguntas de la profesora: pendiente.

Los enlaces se agregarán cuando existan las grabaciones reales.

# Verificacion de la version tecnica

Fecha: 21/10/2026. Responsable del proyecto: Carlos Zambrano Figueroa, Grupo 11.

## Procedimiento y resultado

Se clono el commit 6a406e0 en un directorio temporal independiente, sin enlaces
duros de Git, y se creo un entorno virtual nuevo con Python 3.11.8, sin
heredar paquetes globales. Se instalaron las dependencias de requirements.txt.
La comprobacion corresponde a Windows, no a todos los sistemas operativos.

| Comprobacion | Resultado |
|---|---|
| Instalacion desde requirements.txt | Completada |
| pip check | Sin dependencias incompatibles |
| unittest discover -s tests | 93 pruebas aprobadas |
| src.release_audit | Archivos requeridos presentes; enlaces locales resueltos; cinco notebooks con celdas ejecutadas y sin errores guardados |
| src.final_evaluation.verify() | 885 casos verificados desde predicciones guardadas; sin reajuste |
| Aplicacion de la copia limpia | Arranque local en puerto alternativo 5058 |
| Recorrido Playwright/Chrome | Muestra, CSV valido, faltantes, rechazo, filtros, paginacion, detalle, descarga y evidencia aprobados |
| Adaptacion de pantallas | Sin desbordamiento de pagina en las vistas comprobadas a 320, 390, 768, 1280 y 1440 px |
| Integridad del modelo | Huella identica a la evaluacion final |

La inspeccion de notebooks comprueba salidas guardadas, no una nueva ejecucion
integral de los cinco experimentos. No se repitio la busqueda de hiperparametros
ni se sustituyeron resultados cientificos. Los recursos de Playwright y Chrome
procedieron de las herramientas locales; no son dependencias para usar la app.

Huella del artefacto:

```text
028b9d7071eaa9549b2cfb64f177f34d2aaf5aeb645eb1f7b4af63b746d8c5f1
```

Las modificaciones posteriores a ese commit en este cierre documentan esta
verificacion y la enlazan; no cambian la inferencia ni el entrenamiento.

## Repeticion sin entrenar

Tras instalar las dependencias, desde la raiz:

```text
python -m pip check
python -m unittest discover -s tests
python -m src.release_audit
python -c "from src.final_evaluation import verify; print(verify())"
python -m app.app --port 5057
```

En otra terminal, con Node y Chrome instalados:

```text
npm install
npm run test:browser
```

El test de navegador usa APP_URL cuando se proporciona una direccion distinta.
La medicion de latencia se documenta en el [manual](manual_usuario.md) y puede
repetirse con python -m src.benchmark_app usando solo filas de desarrollo.

## Limites de la verificacion

Estas pruebas no certifican seguridad productiva, accesibilidad integral,
equidad, validez en Ecuador ni cumplimiento juridico. No se realizaron
ensayos de carga concurrente ni evaluacion de usabilidad con tutores.
En esta verificacion del 21/10 la aplicacion era local. El 22/10 se incorporo
el [despliegue publico y su verificacion independiente](despliegue.md).
Los conteos anteriores corresponden a la version historica de esta prueba.

La version tecnica no incluye videos. El pitch y las respuestas asignadas
son entregables adicionales cuyos enlaces deben incorporarse al README
cuando existan las grabaciones reales.

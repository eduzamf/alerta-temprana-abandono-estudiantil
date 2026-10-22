# Planificacion y balance del proyecto

**Autor:** Carlos Zambrano Figueroa. **Grupo:** 11. Modalidad individual.
**Periodo:** seis semanas; cierre del modulo comunicado: 25/10/2026.
**Corte de consolidacion:** 21/10/2026; no sustituye el plazo de los videos.

## Problema, relevancia y usuarios

Los equipos de tutoria y bienestar pueden tener menos capacidad de revision
que estudiantes que necesitan acompanamiento. Se explora si los datos disponibles
al matricularse permiten ordenar una lista limitada para revision humana.
Los usuarios previstos son tutores y responsables de bienestar: no hay una
institucion cliente, adopcion ni utilidad educativa demostradas.

La opcion educativa se eligio frente a revision preventiva de edificios y
anticipacion de contaminacion del aire. La disponibilidad de datos tabulares,
etiquetas y un protocolo reproducible redujo el riesgo de anotacion en seis
semanas. La matriz inicial otorgo 4,55/5 a educacion: es viabilidad, no rendimiento.

## Objetivo SMART y criterios de aceptacion

Desarrollar durante seis semanas un prototipo local que, con 18 variables de
matricula del dataset UCI 697, clasifique tres estados academicos y priorice el
20% de un lote para revision de apoyo. Comparar modelos con cinco folds de
desarrollo y evaluar una configuracion congelada en la reserva. Conservar
las metas originales F1 macro >= 0,60 y cobertura >= 35% en el cupo del 20%,
documentando resultados y limites aunque no se alcancen.

| Criterio | Evidencia | Resultado |
|---|---|---|
| F1 macro >= 0,60 | Prueba final, 885 casos: 0,49366 | No alcanzado |
| Cobertura >= 35% al priorizar 20% | 114/284 abandonos: 40,14%; 177 priorizados | Alcanzado solo en esta particion |
| Entradas disponibles al ingreso | Lista explicita de 18 variables y pruebas de exclusion | Implementado |
| Trazabilidad | Particiones, configuraciones, huellas, notebooks y verificadores | Implementado |
| Prototipo local | CSV, controles, puntuaciones, ranking y exportacion | Implementado |
| Latencia | Meta inicial: mediana <= 5 s por 1.000 registros, diez repeticiones con modelo cargado | Medicion en el manual |
| Utilidad educativa | Uso con tutores y efecto de intervenciones | No demostrados |

La cobertura no es una reduccion causal del abandono. El F1 final no reemplaza
ni reescribe el F1 de validacion 0,51584.

## Alcance y cambios frente al plan

Incluye datos publicos portugueses, EDA, preprocesamiento por fold, Dummy,
LR/RF, optimizacion anidada, subgrupos, robustez, artefacto fijo y demo Flask.
Excluye datos privados, operacion institucional, sanciones, admisiones,
asignacion automatica de beneficios y eficacia causal.

Flask sustituyo a Streamlit conservando inicialmente el despliegue local previsto.
El 22/10/2026, por indicacion docente, se incorporo la demo publica en Render
Free. Se verifico su inferencia sin cambiar el modelo, las particiones ni las
metas SMART. Este cambio no implica operacion institucional.
Ver [despliegue remoto](despliegue.md).
Se priorizaron LR y RF con sus variantes. HistGradientBoosting, la regla de
nota de admision, la ablacion de atributos personales y los cupos 10/30%
propuestos inicialmente no se presentan como experimentos realizados.
La rejilla final de RF tuvo 18 combinaciones, frente al limite orientativo
inicial de ocho por familia: se documento antes de ejecutarla, con validacion
anidada, sin ampliarla despues de observar la reserva.

## Cronograma planificado frente a evidencia real

El Anexo F inicial organizo cuatro sprints. Las semanas describen la secuencia
del curso, no fechas inferidas a partir de archivos. Los commits consolidan
trabajo previo: no demuestran la fecha de ejecucion de todas las actividades.

| Fase | Plan original | Evidencia al 21/10/2026 | Desviacion o limite |
|---|---|---|---|
| S1-S2 | Alcance, datos y referencias | SMART y ficha tecnica; manifiesto, EDA y modelos base reproducidos | Sin registro fiable de horas reales |
| S3 | Diagnostico y ajuste | Curvas y diagnostico de sesgo/sobreajuste | El primer ajuste no trataba RF; corregido en optimizacion posterior |
| S4-S5 | Etica, sensibilidad e interfaz | Workshop, auditoria Wilson, robustez, optimizacion y app integradas en Git el 21/10 | Sin validacion por usuarios educativos |
| S6 | Modelo fijo, prueba y documentacion | Seleccion, artefacto y prueba en commits consecutivos del 21/10; documentacion consolidada | Videos como entrega audiovisual separada |

La estimacion inicial fue 90 horas base y 18 de reserva, no horas trabajadas
certificadas. No se calcula ahorro ni desviacion de esfuerzo sin registros.

## Recursos y responsabilidades

Carlos asume el alcance, la interpretacion, las decisiones y la revision de la
entrega individual. Se utilizaron herramientas de IA como apoyo en programacion,
documentacion y verificacion. Su asistencia no constituye validacion educativa
ni reemplaza la comprobacion de resultados y fuentes.

Datos: UCI 697, 4.424 registros, con 3.539 de desarrollo y 885 de prueba.
Hardware: CPU del equipo personal, sin GPU requerida.
Software: Python 3.11, pandas, scikit-learn, Flask y Git; versiones en
requirements.txt. Node/Playwright son opcionales para pruebas del navegador.
No se declara presupuesto aprobado ni costo institucional medido.

## Riesgos y mitigaciones

| Riesgo | Control aplicado | Limite residual |
|---|---|---|
| Fuga temporal | Excluir indicadores semestrales y temporalidad incierta | Verificar disponibilidad de entradas en cada institucion |
| Sobreajuste | Pipeline por fold, busqueda anidada, reserva final | Una institucion y particion aleatoria |
| Bajo rendimiento | Referencias y metas incumplidas visibles | F1 0,60 no alcanzado |
| Cobertura desigual | Conteos y Wilson por subgrupo | Auditar no equivale a corregir inequidad |
| Entradas incompatibles | Validar esquema, categorias, rangos y faltantes | No detecta diferencias semanticas |
| Alcance excesivo | Demo local, reducir opcionales | Sin operacion institucional |

## Reconciliacion del checklist SMART inicial

El checklist separado reportaba 26,23/31 excluyendo N/A del denominador;
el informe inicial indicaba 27,17/31. No se usan ambos como un mismo resultado.
Con N/A = 0, Parcial = 0,5 y todas las casillas en el denominador, la
reconstruccion del checklist separado es:

| Dimension | Calculo con maximo de plantilla | Puntaje |
|---|---|---:|
| Especifico | 5/5 x 5 | 5,00 |
| Medible | 5/8 x 7 | 4,38 |
| Alcanzable | 8,5/11 x 7 | 5,41 |
| Relevante | 7/10 x 7 | 4,90 |
| Temporal | 10/11 x 5 | 4,55 |
| Total sin redondeo intermedio | 24,229545.../31 | **24,23/31, amarillo** |

Es una reconciliacion retrospectiva coherente con la observacion docente,
no una nueva calificacion ni una modificacion de archivos ya entregados.

## Evidencia de consulta

Se contrastaron el Checklist SMART de la opcion 2 y el Anexo F del cronograma
entregados en Semana 1, junto con los comentarios docentes de semanas 1, 3 y 4.
Las metas no se cambiaron tras observar resultados. Ver
[seleccion](seleccion_modelo.md), [evaluacion](evaluacion_final.md) y
[etica](consideraciones_eticas.md).

# Consideraciones eticas

Esta seccion distingue la auditoria empirica del modelo de las salvaguardas
propuestas para un eventual uso institucional.

## Uso previsto y limites
Apoyo academico voluntario con revision humana. No usar para sanciones, exclusion, admision ni asignacion automatica de beneficios. No cargar datos personales reales en una demostracion publica.

## Auditoria empirica

La [auditoria por subgrupos](../results/reports/fairness_report.md) usa las
predicciones OOF de la regresion logistica original. Incluye genero, edad,
nacionalidad, necesidades especiales, beca y deuda, sin incorporar estas dos
ultimas variables como predictores. Conserva el cupo del ranking por fold,
sin aplicar cuotas distintas por grupo.

Se publican conteos, tasa de seleccion, cobertura, falsos positivos del ranking
y del clasificador, e intervalos marginales de Wilson al 95%. Se distingue
Enrolled de Graduate entre los seleccionados sin abandono registrado.
La comparacion aleatoria mantiene el mismo cupo y se calcula en esperanza;
no demuestra eficacia causal de una intervencion.

Las diferencias de cobertura por edad y genero requieren revision contextual.
Las estimaciones de nacionalidades poco frecuentes y necesidades especiales
tienen alta incertidumbre. Los intervalos no corrigen comparaciones multiples
ni reflejan toda la dependencia entre casos y modelos. No se certifica equidad.

## Salvaguardas propuestas

Las [pruebas de robustez](robustez.md) muestran deterioro de F1 ante ausencia
extensa de datos, carreras desconocidas y desplazamiento de notas. Validar
esquema, categorias y escalas es necesario antes de ofrecer una puntuacion;
que el pipeline acepte una entrada no significa que esa entrada sea fiable.
La aplicacion local ya rechaza categorias no vistas y filas con mas del 20%
de faltantes, comprueba rangos y muestra advertencias. Estos controles no prueban
equidad ni equivalencia de escalas entre instituciones.

Mantener una via abierta de solicitud de apoyo fuera del ranking, revision
humana y derecho a cuestionar la priorizacion ante una persona distinta del
decisor. Estas son propuestas de gobernanza; no mecanismos institucionales
implementados por este repositorio.

Los datos proceden de una institucion portuguesa. No se ha demostrado
transferibilidad a Ecuador ni que una oferta de apoyo reduzca el abandono.
Una menor cobertura en un grupo puede dejar necesidades sin atender; una mayor
seleccion puede aumentar exposicion a etiquetado. La comunicacion debe evitar
tratar una puntuacion como un diagnostico personal.

## Alcance normativo

Esta auditoria estadistica no constituye una evaluacion juridica ni certifica
cumplimiento de la LOPDP. Cualquier despliegue con datos personales requiere
documentar base de legitimacion, finalidad, minimizacion, seguridad, derechos
y responsabilidades institucionales con evidencia verificable.

Las probabilidades del modelo no deben presentarse como certezas ni como riesgos calibrados sin evaluacion especifica.

## Impacto social y grupos afectados

El beneficio potencial es ordenar la revision de casos cuando la capacidad de
acompanamiento es limitada. No se ha medido ahorro de tiempo, permanencia
estudiantil ni eficacia del apoyo. La comparacion aleatoria aporta contexto
predictivo, no evidencia causal: en desarrollo, la cobertura agrupada es
39,7537% frente a 20,0622% esperado con el mismo cupo por fold.

| Grupo | Poder o voz en un uso futuro | Beneficio posible y riesgo |
|---|---|---|
| Estudiantes priorizados | Participacion voluntaria y posibilidad de cuestionar | Acceso a revision; estigmatizacion |
| Estudiantes fuera del cupo | Necesitan solicitud abierta independiente | Pueden quedar invisibilizados |
| Tutores y bienestar | Revisan el contexto y deciden el ofrecimiento | Mejor organizacion; dependencia excesiva del ranking |
| Autoridades universitarias | Deciden recursos y usos permitidos | Posible desvio a admision o sanciones |
| Equipo tecnico | Controla version y calidad de entradas | Responsabilidad por errores y cambios no trazables |
| Responsables de privacidad y representantes estudiantiles | Supervisan datos y cuestionan procedimientos | Ausencia de representacion en una adopcion apresurada |

Ninguno de estos grupos ha validado institucionalmente el prototipo.

## Sesgos y resultados de equidad

Los datos de una institucion portuguesa no representan a estudiantes de
Guayaquil. Hay sesgo de seleccion institucional, diferencias de edad y
representacion muy limitada de ciertas nacionalidades. Enrolled es un estado
no resuelto al corte, no un resultado definitivo de exito.

| Indicador OOF de desarrollo | Resultado e IC Wilson 95% | Lectura |
|---|---|---|
| Cobertura en menores de 20 | 44/327; 13,46% [10,18; 17,58] | 283 abandonos quedan fuera |
| Cobertura en 35 o mas | 146/192; 76,04% [69,53; 81,53] | Mayor cobertura, no ausencia de error |
| FPR ranking en 35 o mas | 46,39% [38,97; 53,97] | Mayor seleccion de personas sin abandono registrado |
| Cobertura en genero codigo 1 | 285/556; 51,26% [47,11; 55,39] | Diferencia descriptiva frente al codigo 0 |
| Cobertura en genero codigo 0 | 167/581; 28,74% [25,21; 32,55] | No se ha demostrado paridad |
| Necesidades especiales codigo 1 | 3/13; 23,08% [8,18; 50,26] | Intervalo amplio; solo 41 integrantes |

El reporte enlazado contiene tambien nacionalidad, beca y deuda, tasas de
seleccion y falsos positivos, con sus denominadores. Un denominador cero
produce una tasa no estimable. Los intervalos son descriptivos y marginales,
sin correccion por comparaciones multiples; no eliminan la dependencia entre
folds ni prueban discriminacion causal. La auditoria utiliza el mismo
procedimiento LR original, no predicciones de prueba final por subgrupo.

Genero, edad y otras variables personales permanecen en la lista historica
de predictores. No se afirma que excluir beca y deuda elimine los sesgos:
pueden persistir asociaciones mediante otras entradas. No se implementaron
cuotas por grupo ni se evaluo una ablacion de atributos personales. La
mitigacion efectiva de diferencias requeriria otro estudio en desarrollo
y una nueva evaluacion independiente, no optimizacion sobre la reserva usada.

## Registro de riesgos y controles

La probabilidad es una valoracion cualitativa del escenario, no una tasa
estimada de incidentes. La efectividad distingue controles comprobados de
medidas propuestas; no se asigna el mismo nivel a todas.

| ID | Riesgo, severidad y probabilidad | Control, responsable y momento | Efectividad y evidencia |
|---|---|---|---|
| R1 | Necesidades fuera del cupo; alta, alta | Via abierta y revision humana; bienestar, antes de cualquier piloto | Propuesta, no medida. La demo advierte el limite; en prueba quedan 170/284 abandonos fuera |
| R2 | Cobertura desigual; alta, alta | Auditoria por subgrupos; Carlos en desarrollo, responsable institucional por cohorte futura | Alta para visibilizar diferencias, no demostrada para reducirlas |
| R3 | Datos incompatibles; alta, media | Validar esquema, categorias y rangos antes de inferir; aplicacion | Alta para errores cubiertos por pruebas; limitada ante valores plausibles con significado distinto |
| R4 | Filtracion o reidentificacion; alta, media | Datos publicos/sinteticos, limites de carga, sin persistencia de lotes; operador en cada uso | Parcial: controles implementados, sin auditoria externa; exportaciones dependen del usuario |
| R5 | Uso sancionador o etiquetado; alta, media | Advertencias, revision humana y prohibicion de usos en el alcance; institucion antes de adoptar | Baja como barrera tecnica: el codigo abierto puede modificarse; requiere gobernanza |
| R6 | Interpretar puntuaciones como certezas; alta, media | Explicar escala, clases y resultados; interfaz y manual | Implementado; comprension por usuarios finales no medida |

No se publican listas nominales de estudiantes. El ranking no decide ni
ejecuta contactos, ayudas o sanciones. Las salvaguardas organizativas exigen
responsables y procedimientos reales antes de un piloto.

## Transparencia y explicabilidad

La regresion logistica es un modelo lineal en las variables transformadas;
sus coeficientes son inspeccionables, pero dependen de escalas, codificacion,
correlaciones y ponderacion de clases. No demuestran causas de abandono.
La interfaz muestra entradas, imputaciones, tres puntuaciones, clase estimada
y cupo. Esto permite revisar el contexto, pero no es una explicacion local
de contribuciones: no se han implementado SHAP, LIME ni razones individualizadas.

Los PDP y el ranking de importancia de optimizacion explican la sensibilidad
de **hiperparametros**, no la importancia de atributos de un estudiante.
Los valores no calibrados tampoco representan porcentajes comprobados de
riesgo individual. No se infiere confianza a partir de la altura de una barra.

## Matriz normativa: alcance y estado verificable

Referencia: [LOPDP, Registro Oficial 459, 26/05/2021](https://www.gob.ec/sites/default/files/regulations/2025-01/01%20Ley%20Org%C3%A1nica%20de%20Protecci%C3%B3n%20de%20Datos%20Personales.pdf).
Es una correspondencia tecnica orientativa, no una opinion juridica ni
certificacion. Una adopcion requeriria revision profesional de la ley,
reglamento y [normativa de la SPDP](https://www.spdp.gob.ec/marco-normativo/).

| Articulo | Exigencia resumida | Evidencia actual y brecha para un piloto |
|---|---|---|
| 7 | Contar con una base de legitimacion aplicable | Fuente publica y licencia documentadas; no existe base institucional documentada para nuevos estudiantes. Una licencia no la sustituye |
| 10 | Finalidad, minimizacion, proporcionalidad y responsabilidad demostrable | 18 entradas y exclusiones trazables; no se ha acreditado necesidad institucional de todos los atributos personales |
| 12 | Informar fines, base legal, conservacion, responsables, derechos y transferencias | Avisos de demo y manual; no existe aviso integral ni responsable universitario designado |
| 20 | Garantias frente a decisiones unica o parcialmente automatizadas que afecten derechos, incluida impugnacion | No se ejecutan decisiones institucionales; falta un canal real de reclamacion y revision independiente |
| 25-26 | Proteccion especial y restricciones al tratamiento sensible, con excepciones reguladas | Necesidades especiales requieren examen especifico; no se autoriza incorporar registros privados por el hecho de ser un proyecto academico |
| 37 | Seguridad y evaluacion continua de medidas | Controles locales y pruebas; sin autenticacion institucional, auditoria externa ni respuesta operativa a incidentes |
| 39 | Proteccion desde el diseno y por defecto | Sin almacenamiento de lotes; exportacion voluntaria. No protege archivos exportados ni garantiza anonimato |
| 40-42 | Analisis de riesgos y evaluacion previa de impacto cuando corresponda por alto riesgo | Registro R1-R6 tecnico; no es una evaluacion formal de impacto aprobada |

No se declara cumplimiento global de LOPDP ni de GDPR. La procedencia
portuguesa del dataset tampoco acredita cumplimiento de una futura operacion
en Ecuador. La demo no es un sistema de gestion de derechos de titulares.

## Responsabilidad, monitoreo y actualizacion

Carlos responde por el mantenimiento tecnico del prototipo academico y la
trazabilidad de lo reportado. No se le atribuye autoridad sobre decisiones
universitarias. Ante un fallo local: detener el analisis, conservar solo el
mensaje y datos sinteticos para reproducirlo, registrar la incidencia y
verificar la correccion antes de usar nuevamente el prototipo.

Para un eventual piloto, la institucion deberia designar un responsable de
tratamiento, un encargado tecnico y un equipo de bienestar con revision
independiente de apelaciones. Una persona distinta del decisor inicial
deberia examinar el reclamo. No hay actualmente tal servicio ni compromisos
de terceros.

| Momento futuro | Comprobacion | Accion propuesta |
|---|---|---|
| Antes de cada lote | Esquema, codigos, escalas y origen autorizado | Rechazar incompatibilidades; no imputar codigos inventados |
| Por cohorte con resultados observables | F1, cobertura, seleccion y FPR por grupo con intervalos | Revisar diferencias y denominadores pequenos; no declarar equidad por falta de precision |
| Ante incidente o cambio de escala | Integridad del modelo y entradas | Suspender el uso y evaluar la causa con el responsable |
| Antes de una nueva version | Evaluacion independiente, revision etica y pruebas | Nueva version documentada; nunca ajustar sobre la reserva ya utilizada |

La app implementa solo las comprobaciones locales descritas; no incluye un
monitor institucional, registro de apelaciones o decisiones automatizadas.

## Reflexion y limites de uso

El aprendizaje central es que un mejor ordenamiento promedio puede coexistir
con importantes necesidades desatendidas y diferencias entre grupos. El
ranking de prueba recupera 40,14% de abandonos, pero no identifica a todos ni
cumple F1 0,60. Por ello, la lista sirve para una demostracion de revision,
no para restringir oportunidades. La auditoria hizo visibles diferencias
que una sola metrica global ocultaba.

No usar el sistema para seleccionar admisiones, retirar becas, sancionar,
diagnosticar capacidades, clasificar personas con datos incompatibles o
atribuir efectos causales. Tampoco transferirlo a Guayaquil sin validacion
local, analisis juridico y participacion de los grupos afectados.

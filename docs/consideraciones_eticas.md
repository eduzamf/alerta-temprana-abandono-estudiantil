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

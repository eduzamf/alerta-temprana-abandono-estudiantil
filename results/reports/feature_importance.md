# Importancia descriptiva de variables

Auditoria posterior al cierre del modelo, sobre desarrollo solamente.
Se reconstruye LR original en los cinco folds historicos y se verifica
que sus clases predichas coincidan con las guardadas. En cada validacion
se permuta una columna original diez veces y se mide la caida de F1 macro.
Las categorias se permutan antes del one-hot, no indicador por indicador.
No se altera el artefacto desplegado ni se vuelve a evaluar la reserva.

| Variable | Caida media F1 macro | DE descriptiva |
|---|---:|---:|
| Application mode | 0.07044 | 0.01924 |
| Course | 0.06390 | 0.01882 |
| Age at enrollment | 0.01457 | 0.01008 |
| Mother's occupation | 0.01416 | 0.00893 |
| Admission grade | 0.01375 | 0.00795 |
| Gender | 0.00966 | 0.01135 |
| Mother's qualification | 0.00846 | 0.01237 |
| Father's occupation | 0.00805 | 0.01646 |
| Application order | 0.00719 | 0.00676 |
| Previous qualification | 0.00598 | 0.01132 |
| Father's qualification | 0.00271 | 0.00896 |
| Previous qualification (grade) | 0.00144 | 0.00645 |
| Daytime/evening attendance | 0.00110 | 0.00676 |
| Displaced | 0.00006 | 0.00376 |
| Marital status | -0.00015 | 0.00542 |
| International | -0.00015 | 0.00264 |
| Nacionality | -0.00056 | 0.00276 |
| Educational special needs | -0.00064 | 0.00210 |

## Interpretacion y limites

Una caida positiva indica dependencia predictiva bajo este procedimiento.
Un valor cercano a cero o negativo no demuestra que una variable carezca
de relevancia educativa. La correlacion puede repartir o esconder importancia
y las permutaciones pueden crear combinaciones poco plausibles.
La desviacion estandar no es un intervalo de confianza ni prueba de significacion.
No son causas de abandono, explicaciones individuales ni razones para sancionar.
Tampoco son importancias de hiperparametros: esas se documentan por separado.

[Resultados completos](../metrics/feature_importance.json).
Reproduccion: `python -m src.feature_importance`.

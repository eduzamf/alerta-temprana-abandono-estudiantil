"""Generate baseline charts and interpretation from verified saved predictions."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data_processing import LABELS, ROOT
from .model import BASELINES
from .verify import verify

NAMES = {"Dummy_prior": "Referencia prior", "LR_base": "Regresion logistica",
         "RF_base": "Random Forest"}
FIGURES = ["baseline_01_f1.png", "baseline_02_cobertura.png", "baseline_03_confusion.png"]


def save(fig, filename):
    fig.text(.5, .015, "Validacion de desarrollo | Reserva final sin evaluar",
             ha="center", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0, .11, 1, .93))
    fig.savefig(ROOT / "results/figures" / filename, dpi=150, facecolor="white")
    plt.close(fig)


def run():
    verify()
    report = json.loads((ROOT / "results/metrics/baseline_results.json").read_text())
    summary = report["summary"]
    (ROOT / "results/figures").mkdir(parents=True, exist_ok=True)
    x = np.arange(len(BASELINES))
    fig, ax = plt.subplots(figsize=(10, 6))
    for offset, split, color, label in [
        (-.19, "train", "#516d83", "Entrenamiento"),
        (.19, "val", "#23877c", "Validacion"),
    ]:
        values = [summary[n][f"{split}_f1_macro"] for n in BASELINES]
        sd = [summary[n][f"{split}_f1_macro_sd"] for n in BASELINES]
        bars = ax.bar(x + offset, values, .36, color=color, label=label, yerr=sd, capsize=4)
        ax.bar_label(bars, fmt="%.3f", padding=10)
    ax.axhline(.60, color="#bc414a", linestyle="--", label="Meta: 0,60")
    ax.set_xticks(x, [NAMES[n] for n in BASELINES])
    ax.set_ylim(0, 1)
    ax.set_ylabel("F1 macro")
    ax.legend(loc="upper left")
    fig.suptitle("Media de cinco folds; barras de error = desviacion estandar, no IC")
    save(fig, FIGURES[0])

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(x, [100 * summary[n]["val_recall20"] for n in BASELINES],
                  color=["#88949a", "#23877c", "#bc414a"],
                  yerr=[100 * summary[n]["val_recall20_sd"] for n in BASELINES], capsize=4)
    ax.bar_label(bars, fmt="%.2f%%", padding=12)
    ax.axhline(100 * report["random_ranking_expected_coverage"],
               linestyle="--", color="#202020", label="Seleccion aleatoria: cobertura esperada")
    ax.set_xticks(x, [NAMES[n] for n in BASELINES])
    ax.set_ylim(0, 55)
    ax.set_ylabel("Abandonos cubiertos (%)")
    ax.legend(loc="upper left")
    fig.suptitle("Cobertura al priorizar el 20% | Media y SD de cinco folds")
    ax.text(.5, -.13, "La referencia prior tiene empates: su ranking no aprende de las variables.",
            transform=ax.transAxes, ha="center", fontsize=9)
    save(fig, FIGURES[1])

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    for ax, name in zip(axes, BASELINES):
        matrix = np.array(report["pooled_oof"][name]["confusion_matrix"])
        ax.imshow(matrix, cmap="Blues", vmin=0, vmax=1767)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, str(matrix[i, j]), ha="center", va="center",
                        color="white" if matrix[i, j] > 900 else "black")
        ax.set_xticks(range(3), LABELS, rotation=25)
        ax.set_yticks(range(3), LABELS)
        ax.set_xlabel("Prediccion")
        ax.set_ylabel("Clase real")
        ax.set_title(NAMES[name])
    fig.suptitle("Matrices de confusion OOF agrupadas: 3539 predicciones por modelo")
    save(fig, FIGURES[2])

    rows = "\n".join(
        f"| {NAMES[n]} | {summary[n]['train_f1_macro']:.5f} | "
        f"{summary[n]['val_f1_macro']:.5f} | {summary[n]['val_f1_macro_sd']:.5f} | "
        f"{summary[n]['gap_f1']:.5f} | {100*summary[n]['val_recall20']:.2f}% |"
        for n in BASELINES
    )
    lr, rf = summary["LR_base"], summary["RF_base"]
    random = report["random_ranking_expected_coverage"]
    content = f"""# Comparacion de modelos base

## Protocolo

Se entrenan tres pipelines independientes en los cinco folds historicos de las
3.539 filas de desarrollo. Imputacion, escalado y codificacion se ajustan solo
con entrenamiento. No se seleccionan hiperparametros en esta fase. La reserva
de 885 filas sigue sin evaluarse.

La regresion logistica usa C=1, ponderacion balanced, max_iter=3000 y semilla 42.
Random Forest usa 200 arboles, min_samples_leaf=3, max_depth=None,
max_features=sqrt, ponderacion balanced y semilla 42. La referencia Dummy prior
devuelve las frecuencias de clase de entrenamiento y predice la clase mayoritaria.

Los parametros completos, versiones y advertencias estan en
[baseline_results.json](../metrics/baseline_results.json).
Las predicciones fuera de fold estan en
[baseline_predictions.csv](../metrics/baseline_predictions.csv), en el orden
historico de desarrollo. No contienen nombres ni identificadores personales;
row_index es una posicion del dataset publico.

## Resultados de validacion

| Modelo | F1 entrenamiento | F1 validacion | SD del F1 validacion | Brecha F1 | Cobertura top 20% |
|---|---:|---:|---:|---:|---:|
{rows}

Las cifras son medias no ponderadas de cinco folds. La SD describe variacion,
no un intervalo de confianza ni una prueba de significacion. Las matrices de
confusion y el classification_report se calculan sobre las predicciones OOF
agrupadas; su F1 no debe sustituir silenciosamente la media de folds.

## Definicion de cobertura

En cada fold se seleccionan ceil(0,20*n) filas con mayor puntuacion Dropout.
Cobertura = abandonos seleccionados / abandonos reales. No equivale a precision,
accuracy ni recall multiclase. Los empates se resuelven de forma estable usando
el orden historico; el archivo registra selected_top20 para auditar la lista.

La referencia prior asigna la misma puntuacion a todos los estudiantes del fold.
Su ranking depende del desempate, no de capacidad predictiva. Se compara ademas
con una seleccion uniforme aleatoria de igual tamano, cuya cobertura esperada
es k/n: **{100*random:.4f}%** en promedio, ligeramente mayor al 20% por el redondeo.
Esto es una expectativa matematica, no el resultado de una simulacion.

La regresion cubre **{100*lr['val_recall20']:.4f}%** de los abandonos, aproximadamente
**{lr['val_recall20']/random:.2f} veces** la cobertura aleatoria esperada. Aun deja
fuera alrededor de **{100*(1-lr['val_recall20']):.2f}%** de los abandonos.
Esto no demuestra reduccion del abandono ni utilidad institucional validada.

## Diagnostico y decisiones

La regresion presenta rendimiento limitado incluso en entrenamiento
(F1 {lr['train_f1_macro']:.5f}) y una brecha menor ({lr['gap_f1']:.5f}).
Es consistente con sesgo alto o senal limitada bajo esta representacion;
no debe tratarse principalmente como un problema de sobreajuste.

Random Forest tiene una brecha de **{rf['gap_f1']:.5f}**, consistente con sobreajuste.
La siguiente fase debe evaluar profundidad y tamano minimo de hojas, y explorar
representaciones o modelos no lineales regularizados para la limitacion de la
regresion. Todos los ajustes se elegiran dentro del entrenamiento.

Ninguno alcanza la meta F1 macro de 0,60. La pequena ventaja de Random Forest en
F1 no basta para declararlo superior: su cobertura es menor y falta cuantificar
la incertidumbre de la diferencia con un procedimiento adecuado.

Estas son configuraciones de referencia, no una seleccion final. No se
persisten modelos definitivos ni se usan resultados de prueba para decidir.
Fairness, calibracion y validacion externa siguen pendientes.

## Figuras

![Comparacion F1](../figures/{FIGURES[0]})

![Cobertura](../figures/{FIGURES[1]})

![Matrices de confusion](../figures/{FIGURES[2]})

## Reproduccion

Desde la raiz del repositorio:

```text
python -m src.train
python -m src.verify
python -m src.baseline_report
```

La verificacion recalcula metricas de validacion desde las predicciones
serializadas, revisa pertenencia a folds, orden, cobertura y reportes agrupados.
Las medias y desviaciones de entrenamiento se contrastan con los registros
por fold; para verificar nuevamente sus predicciones hay que reentrenar.
Los tiempos de ejecucion pueden variar sin implicar diferencias de rendimiento.
"""
    destination = ROOT / "results/reports/baseline_report.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return report


if __name__ == "__main__":
    run()

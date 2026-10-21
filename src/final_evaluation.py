"""Evaluate the frozen artifact once; subsequent calls audit saved predictions."""
import hashlib
import json
import pickle
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split

from .data_processing import ROOT, LABELS, DATA_SHA256, SPLIT_SHA256, load_development, select_predictors
from .evaluate import measure, prediction_metrics, priority_mask
from .finalize import MODEL, configuration, digest, load_frozen, verify as verify_model

RESULT = ROOT / "results/metrics/final_test_results.json"
PREDICTIONS = ROOT / "results/metrics/final_test_predictions.csv"


def load_reserve():
    development, _ = load_development()  # Verifies raw data and historical manifest hashes.
    frame = pd.read_csv(ROOT / "data/raw/data.csv", sep=";")
    frame.columns = frame.columns.str.strip()
    _, indices = train_test_split(np.arange(len(frame)), test_size=.2,
                                  stratify=frame.Target, random_state=42)
    manifest = pd.read_csv(ROOT / "data/processed/particiones.csv")
    expected = set(manifest.loc[manifest.partition.eq("test_reserved"), "row_index"])
    if set(indices) != expected or set(indices) & set(development.index):
        raise ValueError("Reserve membership mismatch or overlap")
    return frame.loc[indices].copy()


def summarize(pred):
    probabilities = pred[[f"p_{label}" for label in LABELS]].to_numpy()
    metrics = prediction_metrics(pred.actual, pred.predicted, probabilities)
    selected = priority_mask(probabilities[:, 0])
    dropout = pred.actual.eq("Dropout").to_numpy()
    k, detected, total = int(selected.sum()), int((selected & dropout).sum()), int(dropout.sum())
    return {
        "metrics": metrics,
        "class_report": classification_report(pred.actual, pred.predicted,
                                               labels=LABELS, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(pred.actual, pred.predicted, labels=LABELS).tolist(),
        "ranking": {"selected": k, "dropout_total": total, "dropout_detected": detected,
                    "dropout_missed": total-detected, "selected_other": k-detected,
                    "random_expected_coverage": k/len(pred),
                    "random_expected_detected": k*total/len(pred)},
        "target_met": bool(metrics["f1_macro"] >= configuration()["primary_target"]),
    }


def run():
    if RESULT.exists() or PREDICTIONS.exists():
        if not (RESULT.exists() and PREDICTIONS.exists()):
            raise FileExistsError("Partial evaluation exists; investigate without overwriting")
        verify()
        report = json.loads(RESULT.read_text())
        render(report)
        return report
    verify_model()
    model, metadata = load_frozen()
    frame = load_reserve()
    before = hashlib.sha256(pickle.dumps(model)).hexdigest()
    _, labels, probabilities = measure(model, select_predictors(frame), frame.Target)
    if before != hashlib.sha256(pickle.dumps(model)).hexdigest():
        raise ValueError("Evaluation changed the model")
    pred = pd.DataFrame({"row_index": frame.index, "actual": frame.Target.to_numpy(),
                         "predicted": labels, "selected_top20": priority_mask(probabilities[:, 0]),
                         **{f"p_{c}": probabilities[:, j] for j, c in enumerate(LABELS)}})
    report = {
        "stage": "final_test", "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": configuration(), "model_sha256": metadata["model_sha256"],
        "dataset_sha256": DATA_SHA256, "partitions_sha256": SPLIT_SHA256,
        "test_rows": len(frame), "training_rows": metadata["training_rows"],
        "test_scored": True, "model_refit": False, "model_state_unchanged": True,
        "prediction_source_sha256": digest(ROOT / "src/final_evaluation.py"),
        **summarize(pred),
    }
    pred.to_csv(PREDICTIONS, index=False, mode="x")
    report["predictions_sha256"] = digest(PREDICTIONS)
    with RESULT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    verify()
    render(report)
    return report


def verify():
    report = json.loads(RESULT.read_text())
    pred = pd.read_csv(PREDICTIONS, float_precision="round_trip")
    frame = load_reserve()
    if digest(PREDICTIONS) != report["predictions_sha256"]:
        raise ValueError("Saved predictions changed")
    if digest(MODEL) != report["model_sha256"] or report["protocol"] != configuration():
        raise ValueError("Model or protocol changed after final evaluation")
    if report["dataset_sha256"] != DATA_SHA256 or report["partitions_sha256"] != SPLIT_SHA256:
        raise ValueError("Data provenance mismatch")
    if not report["test_scored"] or report["model_refit"] or not report["model_state_unchanged"]:
        raise ValueError("Invalid evaluation scope")
    np.testing.assert_array_equal(pred.row_index, frame.index)
    np.testing.assert_array_equal(pred.actual, frame.Target)
    if report["test_rows"] != len(frame) or len(frame) != 885:
        raise ValueError("Unexpected test size")
    np.testing.assert_array_equal(pred.selected_top20, priority_mask(pred.p_Dropout))
    for key, value in summarize(pred).items():
        if value != report[key]:
            raise ValueError(f"Recalculated evidence mismatch: {key}")
    return {"verified": True, "test_rows": len(frame), "model_refit": False}


def render(report):
    metrics, ranking = report["metrics"], report["ranking"]
    baseline = json.loads((ROOT / "results/metrics/baseline_results.json").read_text())["summary"]["LR_base"]
    per_class = "\n".join(
        f"| {label} | {report['class_report'][label]['precision']:.5f} | "
        f"{report['class_report'][label]['recall']:.5f} | "
        f"{report['class_report'][label]['f1-score']:.5f} | "
        f"{int(report['class_report'][label]['support'])} |" for label in LABELS)
    outcome = "alcanzada" if report["target_met"] else "no alcanzada"
    text = f"""# Evaluacion final del modelo seleccionado

## Resultado principal

El F1 macro sobre **{report['test_rows']} casos de prueba** es
**{metrics['f1_macro']:.5f}**. La meta previamente fijada de 0,60 queda
**{outcome}**. Se evalua exclusivamente LR_base entrenada con 3.539 casos
de desarrollo; no se reentrena ni se elige otro candidato con esta prueba.

## Separacion entre validacion y prueba

| Indicador | Validacion: media de 5 folds | Prueba final: 885 casos |
|---|---:|---:|
| F1 macro | {baseline['val_f1_macro']:.5f} | {metrics['f1_macro']:.5f} |
| Accuracy | {baseline['val_accuracy']:.5f} | {metrics['accuracy']:.5f} |
| Cobertura al 20% | {100*baseline['val_recall20']:.2f}% | {100*metrics['recall20']:.2f}% |

La validacion historica usa cinco modelos ajustados por fold; la prueba usa
un solo artefacto ajustado con todo desarrollo. Son estimaciones diferentes,
no correcciones de los resultados anteriores. F1 macro no es porcentaje de
aciertos. Log-loss en prueba: {metrics['log_loss']:.5f}; reportarlo no demuestra
calibracion. Las puntuaciones se usan para ordenar, no como certezas personales.

## Rendimiento por clase

| Clase | Precision | Recall | F1 | Casos |
|---|---:|---:|---:|---:|
{per_class}

Enrolled significa matriculado al corte del dataset, no graduacion futura
confirmada. La matriz usa filas reales y columnas predichas, en el orden
Dropout, Enrolled, Graduate.

![Matriz de confusion de prueba](../results/figures/final_test_confusion.png)

## Priorizacion con cupo del 20%

Se seleccionan **{ranking['selected']}** estudiantes y se incluyen
**{ranking['dropout_detected']} de {ranking['dropout_total']} abandonos**:
cobertura **{100*metrics['recall20']:.2f}%**. Quedan fuera
{ranking['dropout_missed']} abandonos. Entre los seleccionados,
{ranking['selected_other']} no tienen abandono registrado al corte; este conteo
es un error del ranking respecto a esa etiqueta, no el falso positivo multiclase
ni evidencia de que el apoyo sea innecesario.

Una seleccion uniforme aleatoria del mismo cupo cubriria en esperanza el
{100*ranking['random_expected_coverage']:.2f}% de los abandonos,
{ranking['random_expected_detected']:.2f} casos. La cobertura observada es
{metrics['recall20']/ranking['random_expected_coverage']:.2f} veces esa referencia.
No es una prueba de significacion ni demuestra reduccion causal del abandono.

## Trazabilidad y limites

La [decision y protocolo](seleccion_modelo.md) se fijaron antes de la evaluacion.
El modelo conserva su huella SHA-256: `{report['model_sha256']}`.
Se guardaron las predicciones, etiquetas, seleccion y metricas; el verificador
recalcula las cifras sin volver a entrenar ni seleccionar configuraciones.
La reserva ya fue utilizada para esta prueba y no debe reutilizarse para ajustar
el modelo. Una mejora futura requerira una evaluacion independiente adecuada.

La evaluacion corresponde a una particion aleatoria del dataset institucional
portugues. No demuestra validez temporal, transferibilidad a Ecuador, equidad
ni eficacia de una intervencion. La [auditoria por subgrupos](../results/reports/fairness_report.md)
y las [pruebas de robustez](robustez.md) describen validacion de desarrollo,
no pruebas por subgrupo del artefacto final. No deben presentarse como tales.

## Reproduccion

`python -m src.final_evaluation` evalua solo si no existen archivos finales.
Si ya existen, verifica sus predicciones guardadas y reconstruye el informe;
no repite una busqueda ni sustituye resultados.

- [Metricas finales](../results/metrics/final_test_results.json)
- [Predicciones finales](../results/metrics/final_test_predictions.csv)
- [Notebook de evaluacion](../notebooks/05_evaluacion.ipynb)
"""
    (ROOT / "docs/evaluacion_final.md").write_text(text, encoding="utf-8")
    fig, ax = plt.subplots(figsize=(7, 6))
    ConfusionMatrixDisplay(np.array(report["confusion_matrix"]), display_labels=LABELS).plot(
        ax=ax, cmap="Blues", colorbar=False, values_format="d")
    ax.set_xlabel("Clase predicha")
    ax.set_ylabel("Clase real")
    ax.set_title("Prueba final | LR_base | 885 casos")
    fig.tight_layout()
    fig.savefig(ROOT / "results/figures/final_test_confusion.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    result = run()
    print(json.dumps({"metrics": result["metrics"], "ranking": result["ranking"],
                      "target_met": result["target_met"]}, indent=2))

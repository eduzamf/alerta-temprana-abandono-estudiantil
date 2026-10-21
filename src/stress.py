"""Prespecified stress tests with frozen validation pipelines."""
import hashlib
import json
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from .data_processing import LABELS, ROOT, load_development, select_predictors
from .evaluate import measure, prediction_metrics
from .model import build_model
from .verify import verify as verify_baselines

GRADES = ["Previous qualification (grade)", "Admission grade"]
RANDOM = {"missing10", "missing30", "grade_noise", "dropout50"}


def config():
    return json.loads((ROOT / "config/stress.json").read_text())


def perturb(X, y, training, scenario, seed):
    """Never modify input frames or use validation statistics to scale noise."""
    result = X.astype(float).copy()
    rng = np.random.default_rng(seed)
    if scenario in {"missing10", "missing30"}:
        probability = .1 if scenario == "missing10" else .3
        result = result.mask(rng.random(result.shape) < probability)
    elif scenario == "grade_noise":
        for column in GRADES:
            noise = rng.normal(0, .2 * training[column].std(ddof=0), len(result))
            result[column] = (result[column] + noise).clip(0, 200)
    elif scenario == "grades_absent":
        result[GRADES] = np.nan
    elif scenario == "course_unseen":
        result["Course"] = float(training.Course.max()) + 1
    elif scenario == "grade_shift":
        result[GRADES] = (result[GRADES] - 20).clip(0, 200)
    elif scenario == "dropout50":
        positives = y.index[y.eq("Dropout")]
        others = y.index[~y.eq("Dropout")]
        if len(positives) > len(others):
            raise ValueError("Cannot construct specified prevalence without replacement")
        chosen = set(positives) | set(rng.choice(others, len(positives), replace=False))
        result = result.loc[result.index.isin(chosen)]
    elif scenario not in {"clean", "train_under35"}:
        raise ValueError("Unknown scenario")
    return result, y.loc[result.index].copy()


def aggregate(records, protocol):
    summaries = {}
    for scenario in protocol["scenarios"]:
        rows = [r for r in records if r["scenario"] == scenario]
        fold_metrics = []
        for fold in range(1, 6):
            repetitions = [r for r in rows if r["fold"] == fold]
            clean = next(r for r in records if r["scenario"] == "clean" and r["fold"] == fold)
            metrics = {k: float(np.mean([r["metrics"][k] for r in repetitions]))
                       for k in ("f1_macro", "recall20")}
            metrics.update({f"delta_{k}": metrics[k] - clean["metrics"][k]
                            for k in ("f1_macro", "recall20")})
            fold_metrics.append(metrics)
        summary = {key: float(np.mean([row[key] for row in fold_metrics]))
                   for key in fold_metrics[0]}
        summary["worst_fold_delta_f1"] = min(row["delta_f1_macro"] for row in fold_metrics)
        summary["worst_fold_delta_coverage"] = min(row["delta_recall20"] for row in fold_metrics)
        summary["folds"] = fold_metrics
        applicable = scenario not in {"clean", "dropout50"}
        summary["within_mean_tolerance"] = (
            summary["delta_f1_macro"] >= -protocol["max_f1_drop"] - 1e-12
            and summary["delta_recall20"] >= -protocol["max_coverage_drop"] - 1e-12
        ) if applicable else None
        summary["all_folds_within_tolerance"] = (
            summary["worst_fold_delta_f1"] >= -protocol["max_f1_drop"] - 1e-12
            and summary["worst_fold_delta_coverage"] >= -protocol["max_coverage_drop"] - 1e-12
        ) if applicable else None
        summaries[scenario] = summary
    return summaries


def run():
    verify_baselines()
    protocol = config()
    frame, folds = load_development()
    X, y = select_predictors(frame), frame.Target
    records, predictions = [], []
    for fold, (train, validation) in enumerate(folds, 1):
        original = build_model("LR_base")
        with threadpool_limits(limits=4):
            original.fit(X.iloc[train], y.iloc[train])
        for scenario in protocol["scenarios"]:
            model = original
            fitting_indices = X.index[train]
            if scenario == "train_under35":
                restricted = train[X.iloc[train]["Age at enrollment"].to_numpy() < 35]
                fitting_indices = X.index[restricted]
                model = build_model("LR_base")
                with threadpool_limits(limits=4):
                    model.fit(X.iloc[restricted], y.iloc[restricted])
            before = hashlib.sha256(pickle.dumps(model)).hexdigest()
            seeds = protocol["seeds"] if scenario in RANDOM else [0]
            for seed in seeds:
                altered, actual = perturb(X.iloc[validation], y.iloc[validation],
                                          X.iloc[train], scenario, seed + fold)
                metrics, predicted, probabilities = measure(model, altered, actual)
                after = hashlib.sha256(pickle.dumps(model)).hexdigest()
                if before != after:
                    raise ValueError("Prediction mutated fitted model")
                records.append({
                    "scenario": scenario, "fold": fold, "seed": seed,
                    "metrics": metrics, "evaluation_rows": len(actual),
                    "training_rows": len(fitting_indices),
                    "training_indices": fitting_indices.tolist(),
                    "missing_cells": int(altered.isna().sum().sum()),
                    "class_counts": {label: int(actual.eq(label).sum()) for label in LABELS},
                    "model_unchanged": before == after,
                })
                for i, index in enumerate(altered.index):
                    predictions.append({
                        "scenario": scenario, "fold": fold, "seed": seed, "row_index": int(index),
                        "actual": str(actual.loc[index]), "predicted": str(predicted[i]),
                        **{f"p_{label}": float(probabilities[i, j]) for j, label in enumerate(LABELS)},
                    })
        print(f"Fold {fold}: completed", flush=True)
    report = {"protocol": protocol, "test_scored": False, "model": "LR_base",
              "records": records, "summary": aggregate(records, protocol)}
    folder = ROOT / "results/metrics"
    pd.DataFrame(predictions).to_csv(folder / "stress_predictions.csv", index=False)
    (folder / "stress_results.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    verify()
    render(report)
    return report


def verify():
    frame, folds = load_development()
    folder = ROOT / "results/metrics"
    report = json.loads((folder / "stress_results.json").read_text())
    pred = pd.read_csv(folder / "stress_predictions.csv", float_precision="round_trip")
    protocol = config()
    if report["protocol"] != protocol or report["test_scored"]:
        raise ValueError("Unexpected protocol or scope")
    expected = {(s, f, seed) for s in protocol["scenarios"] for f in range(1, 6)
                for seed in (protocol["seeds"] if s in RANDOM else [0])}
    keys = [(r["scenario"], r["fold"], r["seed"]) for r in report["records"]]
    if len(keys) != len(expected) or set(keys) != expected:
        raise ValueError("Missing or duplicate experiments")
    if set(map(tuple, pred[["scenario", "fold", "seed"]].drop_duplicates().to_numpy())) != expected:
        raise ValueError("Unexpected prediction groups")
    baseline = pd.read_csv(folder / "baseline_predictions.csv", float_precision="round_trip")
    baseline = baseline.loc[baseline.model.eq("LR_base")].set_index("row_index")
    for record in report["records"]:
        scenario, fold, seed = record["scenario"], record["fold"], record["seed"]
        train, validation = folds[fold-1]
        group = pred.loc[pred.scenario.eq(scenario) & pred.fold.eq(fold) & pred.seed.eq(seed)]
        altered, actual = perturb(select_predictors(frame.iloc[validation]), frame.Target.iloc[validation],
                                  select_predictors(frame.iloc[train]), scenario, seed+fold)
        np.testing.assert_array_equal(group.row_index, actual.index)
        np.testing.assert_array_equal(group.actual, actual)
        training = frame.index[train]
        if scenario == "train_under35":
            training = frame.iloc[train].loc[frame.iloc[train]["Age at enrollment"] < 35].index
        np.testing.assert_array_equal(record["training_indices"], training)
        if not record["model_unchanged"] or record["missing_cells"] != int(altered.isna().sum().sum()):
            raise ValueError("Transformation or model-state mismatch")
        if record["evaluation_rows"] != len(actual) or record["training_rows"] != len(training):
            raise ValueError("Row-count mismatch")
        if record["class_counts"] != {label: int(actual.eq(label).sum()) for label in LABELS}:
            raise ValueError("Class-count mismatch")
        probabilities = group[[f"p_{label}" for label in LABELS]].to_numpy()
        computed = prediction_metrics(group.actual, group.predicted, probabilities)
        for key, value in computed.items():
            np.testing.assert_allclose(value, record["metrics"][key], atol=1e-12, rtol=0)
        if scenario == "clean":
            np.testing.assert_allclose(probabilities, baseline.loc[actual.index, [f"p_{c}" for c in LABELS]], atol=1e-10, rtol=0)
    if aggregate(report["records"], protocol) != report["summary"]:
        raise ValueError("Summary mismatch")
    return {"verified": True, "experiments": len(expected), "predictions": len(pred), "test_scored": False}


def render(report):
    rows = []
    worst = []
    for scenario, result in report["summary"].items():
        status = {True: "Dentro", False: "Fuera", None: "No aplica"}
        rows.append(f"| {scenario} | {result['f1_macro']:.5f} | {100*result['recall20']:.2f}% | "
                    f"{result['delta_f1_macro']:+.5f} | {100*result['delta_recall20']:+.2f} pp | "
                    f"{status[result['within_mean_tolerance']]} | {status[result['all_folds_within_tolerance']]} |")
        worst.append(f"| {scenario} | {result['worst_fold_delta_f1']:+.5f} | "
                     f"{100*result['worst_fold_delta_coverage']:+.2f} pp |")
    doc = ROOT / "docs/robustez.md"
    protocol = doc.read_text(encoding="utf-8").split("## Resultados")[0].rstrip()
    text = """## Resultados

| Escenario | F1 macro | Cobertura 20% | Cambio F1 | Cambio cobertura | Tolerancia media | Todos los folds |
|---|---:|---:|---:|---:|---|---|
""" + "\n".join(rows)
    text += """

### Peor diferencia entre los cinco folds

Primero se promedian las repeticiones de cada fold. Los peores cambios de F1 y
cobertura pueden corresponder a folds diferentes.

| Escenario | Peor cambio F1 | Peor cambio cobertura |
|---|---:|---:|
""" + "\n".join(worst)
    text += """

### Interpretacion y controles derivados

missing30, course_unseen y grade_shift exceden la tolerancia media de F1.
Aceptar entradas sin fallos de software no equivale a mantener rendimiento:
one-hot admite carreras desconocidas, pero el clasificador pierde informacion.

La interfaz debera advertir sobre categorias no vistas y ausencia extensa de
datos; las escalas de notas deben verificarse antes de inferir. Un valor dentro
de 0-200 puede seguir perteneciendo a otra escala o distribucion: los controles
de rango por si solos no detectan el desplazamiento sistematico ensayado.
Estos controles son recomendaciones derivadas del experimento, no funcionalidades
ya implementadas.

La ausencia conjunta de notas produce poca caida media en este ensayo. Esto
no prueba que las notas carezcan de informacion: hay otras variables y la
imputacion conserva estadisticas del entrenamiento original.
train_under35 queda dentro de tolerancia global, pero eso no garantiza buen
rendimiento en mayores de 34; requeriria una auditoria especifica de ese modelo.

![Cambios de F1 y cobertura](../results/figures/stress_deltas.png)

Las diferencias se comparan con clean. En dropout50, cambia la poblacion
evaluada: no se interpreta su diferencia como perdida atribuible a una
perturbacion de variables. Una media dentro de tolerancia no significa que
todos los folds la cumplan. Pasar estas pruebas no certifica robustez universal.

El escenario train_under35 reajusta el pipeline con un subconjunto del
entrenamiento; todos los demas conservan el modelo fijo. Se comprobo que
predecir no cambia su estado serializado. clean reproduce las probabilidades
historicas de LR_base. La reserva no se evalua y las cifras no son prueba final.

## Evidencia y reproduccion

Ejecutar `python -m src.stress`. Para auditar resultados guardados:
`python -c "from src.stress import verify; print(verify())"`.

[Resultados por fold y repeticion](../results/metrics/stress_results.json).
[Predicciones auditables](../results/metrics/stress_predictions.csv).
Las semillas controlan las perturbaciones; los conteos reales de celdas
ausentes y clases se registran por experimento. Las etiquetas no se alteran.
"""
    doc.write_text(protocol+"\n\n"+text, encoding="utf-8")
    names = [s for s in report["summary"] if s not in {"clean", "dropout50"}]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, metric, limit, title in zip(
        axes, ["delta_f1_macro", "delta_recall20"],
        [report["protocol"]["max_f1_drop"], report["protocol"]["max_coverage_drop"]],
        ["Cambio F1 macro", "Cambio cobertura (proporcion)"],
    ):
        values = [report["summary"][s][metric] for s in names]
        ax.barh(names, values, color=["#bc414a" if v < -limit else "#23877c" for v in values])
        ax.axvline(-limit, linestyle="--", color="#333333", label="Tolerancia previa")
        ax.axvline(0, color="#888888", linewidth=.8)
        ax.set_xlim(-.075, .025)
        ax.set_title(title)
        ax.legend(loc="upper center", bbox_to_anchor=(.5, -.12))
    fig.suptitle("Regresion de referencia: diferencias medias frente a validacion limpia")
    fig.text(.5, .015, "Desarrollo | 5 folds | No incluye el escenario de cambio de prevalencia",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .07, 1, .95))
    fig.savefig(ROOT / "results/figures/stress_deltas.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    run()

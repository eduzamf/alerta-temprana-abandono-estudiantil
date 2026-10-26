"""Descriptive permutation importance on historical held-out development folds."""
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score
from threadpoolctl import threadpool_limits

from .data_processing import ROOT, load_development, select_predictors
from .model import build_model


def summarize(names, fold_importances):
    """Average folds equally; dispersion is descriptive, not a confidence interval."""
    values = np.asarray(fold_importances, dtype=float)
    if values.ndim != 3 or values.shape[1] != len(names):
        raise ValueError("Expected fold x feature x repeat importances")
    if not np.isfinite(values).all():
        raise ValueError("Non-finite importances")
    rows = []
    for index, name in enumerate(names):
        sample = values[:, index, :]
        rows.append({
            "feature": name, "mean_f1_drop": float(sample.mean()),
            "sd_fold_repeat": float(sample.std(ddof=1)),
            "fold_means": sample.mean(axis=1).tolist(),
        })
    return sorted(rows, key=lambda row: row["mean_f1_drop"], reverse=True)


def run():
    """Refit only development-fold replicas; never replace the deployed model."""
    protected = [ROOT / "models/student_support_v1.joblib",
                 ROOT / "results/metrics/final_test_results.json"]
    hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in protected]
    development, folds = load_development()
    X, y = select_predictors(development), development.Target
    historical = pd.read_csv(ROOT / "results/metrics/baseline_predictions.csv")
    historical = historical.loc[historical.model.eq("LR_base")].set_index("row_index")
    records, arrays = [], []
    for number, (train, val) in enumerate(folds, 1):
        pipeline = build_model("LR_base")
        with threadpool_limits(limits=4):
            pipeline.fit(X.iloc[train], y.iloc[train])
            predictions = pipeline.predict(X.iloc[val])
            np.testing.assert_array_equal(
                predictions, historical.loc[X.index[val], "predicted"].to_numpy()
            )
            result = permutation_importance(
                pipeline, X.iloc[val], y.iloc[val], scoring="f1_macro",
                n_repeats=10, random_state=42 + number, n_jobs=1,
            )
        arrays.append(result.importances.tolist())
        records.append({"fold": number, "validation_rows": len(val),
                        "baseline_f1_macro": f1_score(y.iloc[val], predictions,
                                                       average="macro"),
                        "importances": result.importances.tolist()})
        print(f"Verified historical LR predictions; fold {number} complete", flush=True)
    if hashes != [hashlib.sha256(path.read_bytes()).hexdigest() for path in protected]:
        raise AssertionError("Frozen evidence changed")
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Post-hoc descriptive audit of historical LR development folds",
        "model": "LR_base", "metric": "f1_macro", "repeats": 10,
        "seed_by_fold": [43, 44, 45, 46, 47], "test_scored": False,
        "deployed_model_changed": False, "historical_predictions_match": True,
        "model_sha256": hashes[0], "final_results_sha256": hashes[1],
        "features": list(X.columns), "folds": records,
        "ranking": summarize(list(X.columns), arrays),
        "limitations": [
            "Not causal effects, not student attributes' intrinsic importance",
            "Correlated variables may share importance; permutations can form unlikely profiles",
            "SD across fold/repeats is not a confidence interval",
            "Not used for feature selection, model tuning or final-test reevaluation",
        ],
    }
    destination = ROOT / "results/metrics/feature_importance.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Importancia descriptiva de variables", "",
             "Auditoria posterior al cierre del modelo, sobre desarrollo solamente.",
             "Se reconstruye LR original en los cinco folds historicos y se verifica",
             "que sus clases predichas coincidan con las guardadas. En cada validacion",
             "se permuta una columna original diez veces y se mide la caida de F1 macro.",
             "Las categorias se permutan antes del one-hot, no indicador por indicador.",
             "No se altera el artefacto desplegado ni se vuelve a evaluar la reserva.", "",
             "| Variable | Caida media F1 macro | DE descriptiva |",
             "|---|---:|---:|"]
    for row in report["ranking"]:
        lines.append(f"| {row['feature']} | {row['mean_f1_drop']:.5f} | {row['sd_fold_repeat']:.5f} |")
    lines.extend(["", "## Interpretacion y limites", "",
                  "Una caida positiva indica dependencia predictiva bajo este procedimiento.",
                  "Un valor cercano a cero o negativo no demuestra que una variable carezca",
                  "de relevancia educativa. La correlacion puede repartir o esconder importancia",
                  "y las permutaciones pueden crear combinaciones poco plausibles.",
                  "La desviacion estandar no es un intervalo de confianza ni prueba de significacion.",
                  "No son causas de abandono, explicaciones individuales ni razones para sancionar.",
                  "Tampoco son importancias de hiperparametros: esas se documentan por separado.", "",
                  "[Resultados completos](../metrics/feature_importance.json).",
                  "Reproduccion: `python -m src.feature_importance`."])
    (ROOT / "results/reports/feature_importance.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps(result["ranking"][:5], indent=2))

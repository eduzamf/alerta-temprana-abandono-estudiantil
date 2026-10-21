"""Reproduce fixed baselines on historical development folds, not final test."""
import json
import math
import platform
import time
import warnings

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import classification_report, confusion_matrix
from threadpoolctl import threadpool_limits

from .data_processing import DATA_SHA256, LABELS, ROOT, load_development, select_predictors
from .evaluate import measure, prediction_metrics, priority_mask
from .model import BASELINES, build_model

METRICS = ("f1_macro", "accuracy", "log_loss", "recall_dropout", "recall20")


def verify_predictions(frame, records, development):
    """Recompute validation metrics and verify OOF membership/order independently."""
    expected = development.index.tolist()
    manifest = pd.read_csv(ROOT / "data/processed/particiones.csv").set_index("row_index")
    if set(frame.model) != set(BASELINES):
        raise ValueError("Missing or unexpected baseline models")
    for name in BASELINES:
        subset = frame.loc[frame.model.eq(name)]
        if subset.row_index.tolist() != expected:
            raise ValueError("OOF coverage/order mismatch")
        np.testing.assert_array_equal(
            subset.fold.to_numpy(), manifest.loc[subset.row_index, "cv_fold"].to_numpy()
        )
        if sorted(r["fold"] for r in records if r["model"] == name) != [1, 2, 3, 4, 5]:
            raise ValueError("Incomplete or duplicate fold records")
        for record in [r for r in records if r["model"] == name]:
            group = subset.loc[subset.fold.eq(record["fold"])]
            actual = development.loc[group.row_index, "Target"].to_numpy()
            np.testing.assert_array_equal(actual, group.actual.to_numpy())
            proba = group[[f"p_{c}" for c in LABELS]].to_numpy()
            metrics = prediction_metrics(actual, group.predicted, proba)
            for metric in METRICS:
                np.testing.assert_allclose(metrics[metric], record["val"][metric], atol=1e-12, rtol=0)
            np.testing.assert_array_equal(priority_mask(proba[:, 0]), group.selected_top20)
    return True


def run():
    development, folds = load_development()
    X, y = select_predictors(development), development.Target
    records, predictions = [], []
    output = ROOT / "results/metrics"
    output.mkdir(parents=True, exist_ok=True)
    with (output / "baseline_tracking.jsonl").open("w", encoding="utf-8") as log:
        for name in BASELINES:
            for number, (train, val) in enumerate(folds, 1):
                model = build_model(name)
                start = time.perf_counter()
                with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=4):
                    warnings.simplefilter("always")
                    model.fit(X.iloc[train], y.iloc[train])
                    fit_seconds = time.perf_counter() - start
                    train_metrics, _, _ = measure(model, X.iloc[train], y.iloc[train])
                    val_metrics, pred, proba = measure(model, X.iloc[val], y.iloc[val])
                record = {
                    "model": name, "fold": number,
                    "train": train_metrics, "val": val_metrics,
                    "training_rows": len(train), "validation_rows": len(val),
                    "fit_seconds": fit_seconds,
                    "encoded_features": len(model["preprocess"].get_feature_names_out()),
                    "warnings": [str(w.message) for w in caught],
                    "parameters": model["model"].get_params(),
                }
                records.append(record)
                log.write(json.dumps(record) + "\n")
                log.flush()
                mask = priority_mask(proba[:, 0])
                for i, position in enumerate(val):
                    predictions.append({
                        "model": name, "row_index": int(X.index[position]),
                        "fold": number, "actual": str(y.iloc[position]),
                        "predicted": str(pred[i]), "selected_top20": bool(mask[i]),
                        **{f"p_{label}": float(proba[i, j]) for j, label in enumerate(LABELS)},
                    })
                print(f"{name} fold {number}: F1={val_metrics['f1_macro']:.6f}, "
                      f"coverage20={val_metrics['recall20']:.6f}", flush=True)
    frame = pd.DataFrame(predictions)
    order = {row: i for i, row in enumerate(development.index)}
    frame = frame.assign(order=frame.row_index.map(order)).sort_values(
        ["model", "order"]
    ).drop(columns="order")
    frame.to_csv(output / "baseline_predictions.csv", index=False)
    # Verify the serialized values, not only the in-memory arrays.
    persisted = pd.read_csv(output / "baseline_predictions.csv", float_precision="round_trip")
    verify_predictions(persisted, records, development)
    summary, pooled = {}, {}
    for name in BASELINES:
        rows = [r for r in records if r["model"] == name]
        summary[name] = {}
        for split in ("train", "val"):
            for metric in METRICS:
                values = [r[split][metric] for r in rows]
                summary[name][f"{split}_{metric}"] = float(np.mean(values))
                summary[name][f"{split}_{metric}_sd"] = float(np.std(values, ddof=1))
        summary[name]["gap_f1"] = (
            summary[name]["train_f1_macro"] - summary[name]["val_f1_macro"]
        )
        group = frame.loc[frame.model.eq(name)]
        pooled[name] = {
            "confusion_matrix": confusion_matrix(group.actual, group.predicted, labels=LABELS).tolist(),
            "classification_report": classification_report(
                group.actual, group.predicted, labels=LABELS, output_dict=True, zero_division=0
            ),
        }
    report = {
        "dataset_sha256": DATA_SHA256, "seed": 42, "labels": LABELS,
        "development_rows": len(development), "test_reserved_rows": 885,
        "test_scored": False, "oof_verified": True,
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__},
        "aggregation": "Unweighted mean and sample SD across five historical folds; SD is not a CI.",
        "ranking": "Top ceil(0.2*n) within each fold; stable ties in historical development order.",
        "dummy_note": "Prior predicts majority class; tied ranking is arbitrary, not a learned ranking.",
        "random_ranking_expected_coverage": float(np.mean([
            math.ceil(0.2 * len(val)) / len(val) for _, val in folds
        ])),
        "summary": summary, "folds": records, "pooled_oof": pooled,
    }
    (output / "baseline_results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    run()

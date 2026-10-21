"""Recalculate saved baseline metrics and check historical split membership."""
import json

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from .data_processing import DATA_SHA256, LABELS, ROOT, load_development
from .model import BASELINES
from .train import METRICS, verify_predictions


def verify():
    development, _ = load_development()
    folder = ROOT / "results/metrics"
    report = json.loads((folder / "baseline_results.json").read_text(encoding="utf-8"))
    predictions = pd.read_csv(folder / "baseline_predictions.csv", float_precision="round_trip")
    if report["dataset_sha256"] != DATA_SHA256 or report["test_scored"]:
        raise ValueError("Unexpected dataset or final-test status")
    verify_predictions(predictions, report["folds"], development)
    for name in BASELINES:
        rows = [r for r in report["folds"] if r["model"] == name]
        for split in ("train", "val"):
            for metric in METRICS:
                values = [r[split][metric] for r in rows]
                np.testing.assert_allclose(
                    report["summary"][name][f"{split}_{metric}"], np.mean(values), atol=1e-12
                )
                np.testing.assert_allclose(
                    report["summary"][name][f"{split}_{metric}_sd"],
                    np.std(values, ddof=1), atol=1e-12,
                )
        group = predictions.loc[predictions.model.eq(name)]
        summary = report["summary"][name]
        np.testing.assert_allclose(
            summary["gap_f1"], summary["train_f1_macro"] - summary["val_f1_macro"],
            atol=1e-12, rtol=0,
        )
        np.testing.assert_array_equal(
            report["pooled_oof"][name]["confusion_matrix"],
            confusion_matrix(group.actual, group.predicted, labels=LABELS),
        )
        expected = classification_report(
            group.actual, group.predicted, labels=LABELS, output_dict=True, zero_division=0
        )
        if report["pooled_oof"][name]["classification_report"] != expected:
            raise ValueError("Pooled classification report mismatch")
    return {"models": len(BASELINES), "oof_rows": len(predictions),
            "folds_per_model": 5, "verified": True, "test_scored": False}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))

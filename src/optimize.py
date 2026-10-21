"""Nested optimization with a fixed protocol and no final-test access."""
import hashlib
import json
import time
import warnings
from itertools import product

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from .data_processing import (
    DATA_SHA256, LABELS, ROOT, build_preprocessor, load_development, select_predictors,
)
from .evaluate import measure, prediction_metrics, priority_mask
from .train import METRICS

STRATEGIES = ("RF_regularized", "LR_quadratic")


def protocol():
    return json.loads((ROOT / "config/optimization.json").read_text(encoding="utf-8"))


def candidates(strategy, config):
    if strategy == "RF_regularized":
        grid = config[strategy]
        return [dict(zip(("n_estimators", "max_depth", "min_samples_leaf"), values))
                for values in product(grid["n_estimators"], grid["max_depth"], grid["min_samples_leaf"])]
    if strategy == "LR_quadratic":
        return [{"C": value} for value in config[strategy]["C"]]
    raise ValueError("Unknown strategy")


def build_candidate(strategy, parameters):
    if strategy == "RF_regularized":
        estimator = RandomForestClassifier(
            **parameters, max_features="sqrt", class_weight="balanced", n_jobs=4, random_state=42
        )
        prep = build_preprocessor()
    elif strategy == "LR_quadratic":
        estimator = LogisticRegression(
            **parameters, class_weight="balanced", max_iter=3000, random_state=42
        )
        prep = build_preprocessor(numeric_degree=2)
    else:
        raise ValueError("Unknown strategy")
    return Pipeline([("preprocess", prep), ("model", estimator)])


def choice_key(trial):
    params = trial["parameters"]
    simplicity = ((-params["n_estimators"], -params["max_depth"], params["min_samples_leaf"])
                  if trial["strategy"] == "RF_regularized" else (-params["C"],))
    return (trial["inner_f1"], trial["inner_recall20"], *simplicity)


def choose(trials):
    if not trials:
        raise ValueError("No trials")
    return max(trials, key=choice_key)


def fit(model, X, y):
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=4):
        warnings.simplefilter("always")
        model.fit(X, y)
    return time.perf_counter() - start, [str(w.message) for w in caught]


def run():
    config = protocol()
    frame, outer = load_development()
    X, y = select_predictors(frame), frame.Target
    records, trials, predictions, inner_membership = [], [], [], []
    output = ROOT / "results/metrics"
    with (output / "optimization_tracking.jsonl").open("w", encoding="utf-8") as log:
        for outer_number, (train, validation) in enumerate(outer, 1):
            inner = list(StratifiedKFold(
                n_splits=config["inner_folds"], shuffle=True,
                random_state=config["inner_seed_offset"] + outer_number,
            ).split(X.iloc[train], y.iloc[train]))
            for inner_number, (it, iv) in enumerate(inner, 1):
                train_rows = X.index[train[it]].tolist()
                val_rows = X.index[train[iv]].tolist()
                if set(train_rows) & set(val_rows) or (set(train_rows) | set(val_rows)) & set(X.index[validation]):
                    raise ValueError("Inner/outer data leakage")
                inner_membership.append({
                    "outer_fold": outer_number, "inner_fold": inner_number,
                    "train_row_indices": train_rows, "validation_row_indices": val_rows,
                })
            for strategy in STRATEGIES:
                options = []
                for candidate_id, parameters in enumerate(candidates(strategy, config), 1):
                    scores, messages, durations = [], [], []
                    for it, iv in inner:
                        model = build_candidate(strategy, parameters)
                        seconds, caught = fit(model, X.iloc[train[it]], y.iloc[train[it]])
                        metrics, _, _ = measure(model, X.iloc[train[iv]], y.iloc[train[iv]])
                        scores.append(metrics)
                        messages.extend(caught)
                        durations.append(seconds)
                    trial = {
                        "strategy": strategy, "outer_fold": outer_number,
                        "candidate_id": candidate_id, "parameters": parameters,
                        "inner_f1": float(np.mean([s["f1_macro"] for s in scores])),
                        "inner_recall20": float(np.mean([s["recall20"] for s in scores])),
                        "inner_metrics": scores, "fit_seconds": durations, "warnings": messages,
                    }
                    options.append(trial)
                    trials.append(trial)
                    log.write(json.dumps({"stage": "inner", **trial}) + "\n")
                    log.flush()
                selected = choose(options)
                model = build_candidate(strategy, selected["parameters"])
                seconds, caught = fit(model, X.iloc[train], y.iloc[train])
                train_metrics, _, _ = measure(model, X.iloc[train], y.iloc[train])
                val_metrics, pred, proba = measure(model, X.iloc[validation], y.iloc[validation])
                record = {
                    "model": strategy, "fold": outer_number,
                    "parameters": selected["parameters"], "candidate_id": selected["candidate_id"],
                    "train": train_metrics, "val": val_metrics,
                    "training_rows": len(train), "validation_rows": len(validation),
                    "encoded_features": len(model["preprocess"].get_feature_names_out()),
                    "fit_seconds": seconds, "warnings": caught,
                }
                records.append(record)
                log.write(json.dumps({"stage": "outer", **record}) + "\n")
                log.flush()
                mask = priority_mask(proba[:, 0])
                for i, position in enumerate(validation):
                    predictions.append({
                        "model": strategy, "row_index": int(X.index[position]),
                        "fold": outer_number, "actual": str(y.iloc[position]),
                        "predicted": str(pred[i]), "selected_top20": bool(mask[i]),
                        **{f"p_{label}": float(proba[i, j]) for j, label in enumerate(LABELS)},
                    })
                print(strategy, outer_number, selected["parameters"],
                      "F1", round(val_metrics["f1_macro"], 6),
                      "coverage", round(val_metrics["recall20"], 6), flush=True)
    pred_frame = pd.DataFrame(predictions)
    order = {row: i for i, row in enumerate(frame.index)}
    pred_frame = pred_frame.assign(order=pred_frame.row_index.map(order)).sort_values(
        ["model", "order"]
    ).drop(columns="order")
    pred_frame.to_csv(output / "optimization_predictions.csv", index=False)
    summary = {}
    for strategy in STRATEGIES:
        rows = [r for r in records if r["model"] == strategy]
        summary[strategy] = {}
        for split in ("train", "val"):
            for metric in METRICS:
                values = [r[split][metric] for r in rows]
                summary[strategy][f"{split}_{metric}"] = float(np.mean(values))
                summary[strategy][f"{split}_{metric}_sd"] = float(np.std(values, ddof=1))
        summary[strategy]["gap_f1"] = (
            summary[strategy]["train_f1_macro"] - summary[strategy]["val_f1_macro"]
        )
    report = {
        "protocol": config,
        "protocol_sha256": hashlib.sha256((ROOT / "config/optimization.json").read_bytes()).hexdigest(),
        "dataset_sha256": DATA_SHA256, "development_rows": len(frame), "test_scored": False,
        "summary": summary, "folds": records, "trials": trials,
        "inner_membership": inner_membership,
        "aggregation": "Unweighted external-fold means; sample SD is not an independent-sample CI.",
        "selection": "No final model selected or persisted by this experiment.",
    }
    (output / "optimization_results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    verify()
    return report


def verify():
    frame, outer = load_development()
    folder = ROOT / "results/metrics"
    report = json.loads((folder / "optimization_results.json").read_text())
    predictions = pd.read_csv(folder / "optimization_predictions.csv", float_precision="round_trip")
    if report["test_scored"] or report["dataset_sha256"] != DATA_SHA256:
        raise ValueError("Unexpected data scope")
    if report["protocol"] != protocol():
        raise ValueError("Protocol changed after experiment")
    if set(predictions.model) != set(STRATEGIES):
        raise ValueError("Unexpected strategy predictions")
    if len(report["folds"]) != 10 or len(report["trials"]) != 105 or len(report["inner_membership"]) != 15:
        raise ValueError("Unexpected experiment record counts")
    for strategy in STRATEGIES:
        subset = predictions.loc[predictions.model.eq(strategy)]
        np.testing.assert_array_equal(subset.row_index, frame.index)
        for fold, (train, validation) in enumerate(outer, 1):
            group = subset.loc[subset.fold.eq(fold)]
            np.testing.assert_array_equal(group.row_index, frame.index[validation])
            np.testing.assert_array_equal(group.actual, frame.Target.iloc[validation])
            options = [t for t in report["trials"] if t["strategy"] == strategy and t["outer_fold"] == fold]
            expected_candidates = candidates(strategy, report["protocol"])
            if [t["parameters"] for t in options] != expected_candidates:
                raise ValueError("Missing or changed candidate search")
            for trial in options:
                if len(trial["inner_metrics"]) != 3:
                    raise ValueError("Incomplete inner scores")
                np.testing.assert_allclose(trial["inner_f1"],
                    np.mean([s["f1_macro"] for s in trial["inner_metrics"]]), atol=1e-12)
                np.testing.assert_allclose(trial["inner_recall20"],
                    np.mean([s["recall20"] for s in trial["inner_metrics"]]), atol=1e-12)
            row = next(r for r in report["folds"] if r["model"] == strategy and r["fold"] == fold)
            if row["parameters"] != choose(options)["parameters"]:
                raise ValueError("Selection does not match inner results")
            proba = group[[f"p_{c}" for c in LABELS]].to_numpy()
            computed = prediction_metrics(group.actual, group.predicted, proba)
            for metric in METRICS:
                np.testing.assert_allclose(computed[metric], row["val"][metric], atol=1e-12, rtol=0)
            np.testing.assert_array_equal(group.selected_top20, priority_mask(proba[:, 0]))
        rows = [r for r in report["folds"] if r["model"] == strategy]
        if sorted(r["fold"] for r in rows) != list(range(1, 6)):
            raise ValueError("Duplicate or missing external fold")
        summary = report["summary"][strategy]
        np.testing.assert_allclose(
            summary["gap_f1"], summary["train_f1_macro"] - summary["val_f1_macro"],
            atol=1e-12, rtol=0,
        )
        for split in ("train", "val"):
            for metric in METRICS:
                values = [r[split][metric] for r in rows]
                np.testing.assert_allclose(report["summary"][strategy][f"{split}_{metric}"], np.mean(values), atol=1e-12)
                np.testing.assert_allclose(report["summary"][strategy][f"{split}_{metric}_sd"], np.std(values, ddof=1), atol=1e-12)
    for fold, (train, validation) in enumerate(outer, 1):
        expected_inner = list(StratifiedKFold(n_splits=3, shuffle=True, random_state=142+fold).split(
            frame.iloc[train], frame.Target.iloc[train]))
        for inner_number, (it, iv) in enumerate(expected_inner, 1):
            recorded = next(r for r in report["inner_membership"]
                            if r["outer_fold"] == fold and r["inner_fold"] == inner_number)
            np.testing.assert_array_equal(recorded["train_row_indices"], frame.index[train[it]])
            np.testing.assert_array_equal(recorded["validation_row_indices"], frame.index[train[iv]])
    return {"verified": True, "oof_predictions": len(predictions), "test_scored": False}


if __name__ == "__main__":
    run()

"""One metric implementation for predictions, reports and verification."""
import math

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, log_loss, recall_score

from .data_processing import LABELS


def priority_mask(scores, fraction=0.2):
    """Stable ties preserve the historical development order within each fold."""
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Scores must be a nonempty finite vector")
    if not 0 < fraction <= 1:
        raise ValueError("Capacity fraction must be in (0, 1]")
    selected = np.zeros(len(values), dtype=bool)
    selected[np.argsort(-values, kind="stable")[:math.ceil(fraction * len(values))]] = True
    return selected


def prediction_metrics(actual, predicted, probabilities):
    """Probabilities must have columns ordered exactly as LABELS."""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    probabilities = np.asarray(probabilities, dtype=float)
    if actual.ndim != 1 or predicted.shape != actual.shape or not len(actual):
        raise ValueError("Actual and predicted labels must be aligned nonempty vectors")
    if not set(actual).issubset(LABELS) or not set(predicted).issubset(LABELS):
        raise ValueError("Unexpected class labels")
    if probabilities.shape != (len(actual), len(LABELS)):
        raise ValueError("Expected three probability columns in LABELS order")
    if (not np.isfinite(probabilities).all() or (probabilities < 0).any()
            or (probabilities > 1).any()
            or not np.allclose(probabilities.sum(axis=1), 1.0)):
        raise ValueError("Invalid class probabilities")
    selected = priority_mask(probabilities[:, LABELS.index("Dropout")])
    dropout = actual == "Dropout"
    coverage = float(np.sum(selected & dropout) / dropout.sum()) if dropout.any() else None
    return {
        "f1_macro": float(f1_score(actual, predicted, labels=LABELS,
                                   average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(actual, predicted)),
        "log_loss": float(log_loss(actual, probabilities, labels=LABELS)),
        "recall_dropout": float(recall_score(
            actual, predicted, labels=["Dropout"], average=None, zero_division=0
        )[0]),
        "recall20": coverage,
    }


def measure(model, predictors, actual):
    raw = model.predict_proba(predictors)
    classes = list(model.classes_)
    probabilities = raw[:, [classes.index(label) for label in LABELS]]
    predicted = model.predict(predictors)
    return prediction_metrics(actual, predicted, probabilities), predicted, probabilities

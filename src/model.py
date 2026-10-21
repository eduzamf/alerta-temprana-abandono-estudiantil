"""Fresh pipelines for historical baselines and a non-informative reference."""
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .data_processing import build_preprocessor

BASELINES = ("Dummy_prior", "LR_base", "RF_base")


def build_model(name):
    """Keep preprocessing inside each fit, including future inner CV fits."""
    if name == "Dummy_prior":
        classifier = DummyClassifier(strategy="prior", random_state=42)
    elif name == "LR_base":
        classifier = LogisticRegression(
            C=1.0, class_weight="balanced", max_iter=3000, random_state=42,
        )
    elif name == "RF_base":
        classifier = RandomForestClassifier(
            n_estimators=200, min_samples_leaf=3, max_features="sqrt",
            class_weight="balanced", n_jobs=4, random_state=42,
        )
    else:
        raise ValueError(f"Unknown model: {name}")
    return Pipeline([("preprocess", build_preprocessor()), ("model", classifier)])

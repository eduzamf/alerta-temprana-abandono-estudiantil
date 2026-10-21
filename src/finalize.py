"""Fit the frozen model on development only and persist its provenance."""
import hashlib
import json
import platform
import warnings
from importlib.metadata import version

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from .data_processing import DATA_SHA256, SPLIT_SHA256, FEATURES, LABELS, ROOT, load_development, select_predictors
from .model import build_model

MODEL = ROOT / "models/student_support_v1.joblib"
METADATA = ROOT / "models/student_support_v1.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configuration():
    return json.loads((ROOT / "config/final_model.json").read_text())


def validate_configuration(config):
    expected = {
        "version": "1.0", "model": "LR_base",
        "parameters": {"C": 1.0, "class_weight": "balanced", "max_iter": 3000, "random_state": 42},
        "numeric_degree": 1, "calibration": "none", "ranking_fraction": .2,
        "primary_metric": "f1_macro", "primary_target": .6,
        "test_order": "historical train_test_split random_state=42", "post_test_tuning": False,
    }
    if config != expected:
        raise ValueError("Configuration differs from frozen v1 protocol")


def train():
    if MODEL.exists() or METADATA.exists():
        raise FileExistsError("Frozen artifact exists; verify it instead of overwriting")
    config = configuration()
    validate_configuration(config)
    frame, _ = load_development()
    X = select_predictors(frame)
    model = build_model(config["model"])
    with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=4):
        warnings.simplefilter("always")
        model.fit(X, frame.Target)
    if caught:
        raise RuntimeError("Training warnings require review: " + "; ".join(str(w.message) for w in caught))
    MODEL.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL, compress=3)
    restored = joblib.load(MODEL)  # Only this locally generated trusted artifact.
    np.testing.assert_array_equal(model.predict(X), restored.predict(X))
    np.testing.assert_allclose(model.predict_proba(X), restored.predict_proba(X), rtol=0, atol=0)
    metadata = {
        "configuration": config, "dataset_sha256": DATA_SHA256, "partitions_sha256": SPLIT_SHA256,
        "model_sha256": digest(MODEL), "training_rows": len(frame),
        "training_indices": frame.index.tolist(), "features": FEATURES,
        "classes": model.classes_.tolist(), "test_used_for_training": False,
        "training_stage_test_scored": False,
        "versions": {name: version(name) for name in ["numpy", "pandas", "scikit-learn", "joblib"]},
        "python": platform.python_version(), "serialization_predictions_identical": True,
        "encoded_features": len(model["preprocess"].get_feature_names_out()),
        "iterations": model["model"].n_iter_.tolist(),
        "training_source_sha256": {name: digest(ROOT / name) for name in
                                   ["src/finalize.py", "src/model.py", "src/data_processing.py"]},
    }
    METADATA.write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    return verify()


def load_frozen():
    """Load only the trusted repository artifact, after validating its checksum."""
    metadata = json.loads(METADATA.read_text())
    validate_configuration(configuration())
    if metadata["configuration"] != configuration():
        raise ValueError("Artifact configuration mismatch")
    if digest(MODEL) != metadata["model_sha256"]:
        raise ValueError("Artifact checksum mismatch")
    if version("scikit-learn") != metadata["versions"]["scikit-learn"]:
        raise ValueError("Use the recorded scikit-learn version")
    # A checksum detects accidental changes, not an attacker replacing both files.
    return joblib.load(MODEL), metadata


def verify():
    model, metadata = load_frozen()
    frame, _ = load_development()
    np.testing.assert_array_equal(metadata["training_indices"], frame.index)
    if metadata["training_rows"] != len(frame) or metadata["test_used_for_training"]:
        raise ValueError("Unexpected training scope")
    if metadata["features"] != FEATURES or set(metadata["classes"]) != set(LABELS):
        raise ValueError("Feature or class contract mismatch")
    if metadata["dataset_sha256"] != DATA_SHA256 or metadata["partitions_sha256"] != SPLIT_SHA256:
        raise ValueError("Data provenance mismatch")
    for name, value in metadata["configuration"]["parameters"].items():
        if model["model"].get_params()[name] != value:
            raise ValueError("Model parameters mismatch")
    X = select_predictors(frame)
    np.testing.assert_array_equal(model.feature_names_in_, FEATURES)
    numeric = model["preprocess"].named_transformers_["numeric"]
    columns = model["preprocess"].transformers_[0][2]
    np.testing.assert_allclose(numeric["impute"].statistics_, X[columns].median())
    np.testing.assert_allclose(numeric["scale"].mean_, X[columns].mean())
    probabilities = model.predict_proba(X.iloc[:10])
    if not np.isfinite(probabilities).all() or not np.allclose(probabilities.sum(axis=1), 1):
        raise ValueError("Invalid prediction contract")
    return {"verified": True, "training_rows": len(frame),
            "model_sha256": metadata["model_sha256"], "test_used_for_training": False}


if __name__ == "__main__":
    print(json.dumps(verify() if MODEL.exists() else train(), indent=2))

"""Verify historical data and expose development rows without final-test scoring."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_SHA256 = "3ef126de5cefff26eb11fbb4237f1a1401cb64b488e2f1d598c23cedeb4c45ae"
SPLIT_SHA256 = "421699f3d13e2f4d0096ed829ac971ee29ee7f694d300730df08414c2d39da14"
FEATURES = [
    "Marital status", "Application mode", "Application order", "Course",
    "Daytime/evening attendance", "Previous qualification",
    "Previous qualification (grade)", "Nacionality", "Mother's qualification",
    "Father's qualification", "Mother's occupation", "Father's occupation",
    "Admission grade", "Displaced", "Educational special needs", "Gender",
    "Age at enrollment", "International",
]
NUMERIC = [
    "Application order", "Previous qualification (grade)",
    "Admission grade", "Age at enrollment",
]
CATEGORICAL = [name for name in FEATURES if name not in NUMERIC]
LABELS = ["Dropout", "Enrolled", "Graduate"]


def select_predictors(frame):
    """Select the fixed feature contract, preserving missing values and row order.

    This validates structure and numeric storage, not every allowed domain code.
    Extra columns (including Target) never become predictors. Call before fitting
    or predicting; do not pass the complete audit frame to the model.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Predictors must be provided as a pandas DataFrame")
    if frame.columns.duplicated().any():
        raise ValueError("Duplicate column names are not allowed")
    missing = [column for column in FEATURES if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required predictors: {', '.join(missing)}")
    if frame.empty:
        raise ValueError("At least one observation is required")
    selected = frame.loc[:, FEATURES].copy()
    for column in FEATURES:
        if not pd.api.types.is_numeric_dtype(selected[column]):
            raise ValueError(f"Expected numeric values or category codes: {column}")
    if np.isinf(selected.to_numpy(dtype=float, na_value=np.nan)).any():
        raise ValueError("Infinite predictor values are not supported")
    return selected


def build_preprocessor(min_frequency=None):
    """Return an unfitted clone-compatible transformer matching the baseline.

    Fit independently on each training fold. Validation and final test must use
    transform only. Unknown category codes map to zeros in their one-hot block;
    this prevents an exception, but does not establish validity for new groups.
    """
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(
            handle_unknown="ignore", sparse_output=False,
            min_frequency=min_frequency,
        )),
    ])
    return ColumnTransformer([
        ("numeric", numeric, NUMERIC),
        ("categorical", categorical, CATEGORICAL),
    ], remainder="drop")


def verify_hash(path, expected):
    """Reject changed source bytes before parsing any observations."""
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"Integrity mismatch: {Path(path).name}")
    return actual


def validate_manifest(manifest, n_rows):
    """Require exhaustive, unique row IDs and legal partition/fold pairs."""
    if list(manifest.columns) != ["row_index", "partition", "cv_fold"]:
        raise ValueError("Unexpected partition schema")
    if manifest.isna().any().any():
        raise ValueError("Missing partition values")
    if not pd.api.types.is_integer_dtype(manifest.row_index):
        raise ValueError("Row IDs must be integers")
    if not pd.api.types.is_integer_dtype(manifest.cv_fold):
        raise ValueError("Fold IDs must be integers")
    if len(manifest) != n_rows or set(manifest.row_index) != set(range(n_rows)):
        raise ValueError("Missing, duplicated or out-of-range row IDs")
    if set(manifest.partition) != {"development", "test_reserved"}:
        raise ValueError("Unexpected partition names")
    dev = manifest.partition.eq("development")
    if not manifest.loc[dev, "cv_fold"].isin(range(1, 6)).all():
        raise ValueError("Invalid development fold")
    if not manifest.loc[~dev, "cv_fold"].eq(-1).all():
        raise ValueError("Final reserve cannot belong to development folds")


def load_development(data_dir=None):
    """Return development frame and positional CV folds in historical order.

    Full-source labels are used only to verify the pre-existing stratified split.
    No test predictions, test metrics or test feature summaries are computed.
    This is a workflow safeguard, not access control over a public CSV.
    """
    data_dir = Path(data_dir) if data_dir is not None else ROOT / "data"
    raw = data_dir / "raw/data.csv"
    split = data_dir / "processed/particiones.csv"
    verify_hash(raw, DATA_SHA256)
    verify_hash(split, SPLIT_SHA256)
    frame = pd.read_csv(raw, sep=";")
    frame.columns = frame.columns.str.strip()
    manifest = pd.read_csv(split)
    validate_manifest(manifest, len(frame))
    if frame.shape != (4424, 37) or not set(FEATURES).issubset(frame.columns):
        raise ValueError("Unexpected dataset shape or features")
    if set(frame.Target.unique()) != set(LABELS):
        raise ValueError("Unexpected target labels")
    dev, reserved = train_test_split(
        np.arange(len(frame)), test_size=0.2, stratify=frame.Target, random_state=42
    )
    for name, indices in [("development", dev), ("test_reserved", reserved)]:
        expected = set(manifest.loc[manifest.partition.eq(name), "row_index"])
        if set(indices) != expected:
            raise ValueError(f"Historical split mismatch: {name}")
    development = frame.loc[dev].copy()
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(
        development[FEATURES], development.Target
    ))
    for number, (_, validation) in enumerate(folds, 1):
        expected = set(manifest.loc[manifest.cv_fold.eq(number), "row_index"])
        if set(dev[validation]) != expected:
            raise ValueError(f"Historical fold mismatch: {number}")
    return development, folds


def audit_data():
    """Summarize development integrity without training or evaluating models."""
    development, folds = load_development()
    return {
        "dataset_sha256": DATA_SHA256,
        "partitions_sha256": SPLIT_SHA256,
        "source_rows": 4424,
        "source_predictors": 36,
        "development_rows": len(development),
        "test_reserved_rows": 885,
        "test_scored": False,
        "historical_partitions_match": True,
        "historical_folds_match": True,
        "development_class_counts": development.Target.value_counts().to_dict(),
        "development_missing_cells": int(development.isna().sum().sum()),
        "development_exact_duplicates": int(development.duplicated().sum()),
        "features": FEATURES,
        "excluded_predictors": [
            c for c in development.columns if c not in FEATURES + ["Target"]
        ],
        "validation_fold_sizes": [len(validation) for _, validation in folds],
        "development_order": "Original train_test_split order; stable ranking ties",
    }


if __name__ == "__main__":
    report = audit_data()
    destination = ROOT / "results/metrics/data_audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

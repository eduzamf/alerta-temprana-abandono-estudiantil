"""Audit fold-local transformations without fitting a predictive model."""
import json

import numpy as np

from .data_processing import (
    CATEGORICAL, DATA_SHA256, FEATURES, NUMERIC, ROOT, SPLIT_SHA256,
    build_preprocessor, load_development, select_predictors,
)


def audit_preprocessing():
    """Check train-only statistics, categories and stable transform dimensions."""
    development, folds = load_development()
    predictors = select_predictors(development)
    records = []
    for number, (train_ids, validation_ids) in enumerate(folds, 1):
        train = predictors.iloc[train_ids]
        validation = predictors.iloc[validation_ids]
        transformer = build_preprocessor()
        train_matrix = transformer.fit_transform(train)
        numeric = transformer.named_transformers_["numeric"]
        categorical = transformer.named_transformers_["categorical"]
        medians = numeric["impute"].statistics_.copy()
        means = numeric["scale"].mean_.copy()
        variances = numeric["scale"].var_.copy()
        modes = categorical["impute"].statistics_.copy()
        categories = [values.copy() for values in categorical["encode"].categories_]
        validation_matrix = transformer.transform(validation)

        expected_medians = train[NUMERIC].median().to_numpy()
        filled_numeric = train[NUMERIC].fillna(train[NUMERIC].median())
        np.testing.assert_allclose(medians, expected_medians)
        np.testing.assert_allclose(means, filled_numeric.mean().to_numpy())
        np.testing.assert_allclose(variances, filled_numeric.var(ddof=0).to_numpy())
        np.testing.assert_array_equal(medians, numeric["impute"].statistics_)
        np.testing.assert_array_equal(means, numeric["scale"].mean_)
        np.testing.assert_array_equal(variances, numeric["scale"].var_)
        np.testing.assert_array_equal(modes, categorical["impute"].statistics_)
        unknown_counts = {}
        for column, mode, known, after in zip(
            CATEGORICAL, modes, categories, categorical["encode"].categories_
        ):
            expected_mode = train[column].mode().iloc[0]
            if mode != expected_mode:
                raise ValueError(f"Training mode mismatch: {column}")
            expected_categories = np.sort(train[column].fillna(mode).unique())
            np.testing.assert_array_equal(known, expected_categories)
            np.testing.assert_array_equal(known, after)
            unknown_counts[column] = int(
                (~validation[column].fillna(mode).isin(known)).sum()
            )
        if train_matrix.shape[1] != validation_matrix.shape[1]:
            raise ValueError("Train and validation feature dimensions differ")
        if not (np.isfinite(train_matrix).all() and np.isfinite(validation_matrix).all()):
            raise ValueError("Non-finite transformed values")
        records.append({
            "fold": number,
            "training_rows": len(train), "validation_rows": len(validation),
            "input_predictors": len(FEATURES),
            "encoded_predictors": train_matrix.shape[1],
            "training_numeric_medians": dict(zip(NUMERIC, medians.tolist())),
            "training_numeric_means": dict(zip(NUMERIC, means.tolist())),
            "training_numeric_variances": dict(zip(NUMERIC, variances.tolist())),
            "training_categorical_modes": dict(zip(CATEGORICAL, modes.tolist())),
            "training_category_counts": dict(zip(CATEGORICAL, map(len, categories))),
            "unknown_validation_counts": unknown_counts,
            "training_statistics_verified": True,
            "state_unchanged_after_validation_transform": True,
            "finite_outputs": True,
        })
    return {
        "scope": "development CV only; no predictive model training",
        "dataset_sha256": DATA_SHA256, "partitions_sha256": SPLIT_SHA256,
        "development_rows": len(development), "test_scored": False,
        "feature_names": FEATURES, "numeric_features": NUMERIC,
        "categorical_features": CATEGORICAL,
        "configuration": {
            "numeric_imputation": "training median", "scaling": "StandardScaler",
            "categorical_imputation": "training most frequent",
            "encoding": "one-hot", "unknown_categories": "ignore (all-zero block)",
            "min_frequency": None, "remainder": "drop",
        },
        "folds": records,
    }


def run():
    report = audit_preprocessing()
    path = ROOT / "results/metrics/preprocessing_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    for fold in result["folds"]:
        print(f"Fold {fold['fold']}: {fold['training_rows']} training, "
              f"{fold['validation_rows']} validation, "
              f"{fold['encoded_predictors']} encoded columns; checks passed")
    print("No predictive model fitted; final reserve not evaluated.")

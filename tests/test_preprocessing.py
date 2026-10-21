"""Train-only preprocessing tests with synthetic held-out perturbations."""
import unittest

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.exceptions import NotFittedError

from src.data_processing import (
    CATEGORICAL, FEATURES, NUMERIC, build_preprocessor, select_predictors,
)
from src.preprocessing_audit import audit_preprocessing


def sample():
    frame = pd.DataFrame({column: [0., 0., 1., 1.] for column in FEATURES})
    for column in NUMERIC:
        frame[column] = [10., 20., 30., np.nan]
    return frame


class PreprocessingTests(unittest.TestCase):
    def test_selection_excludes_extra_columns_and_preserves_order(self):
        frame = sample()
        frame.index = [9, 4, 8, 2]
        frame["Target"] = "Dropout"
        frame["Scholarship holder"] = 1
        frame["Curricular units 1st sem (grade)"] = 20
        result = select_predictors(frame)
        self.assertEqual(list(result.columns), FEATURES)
        self.assertEqual(result.index.tolist(), [9, 4, 8, 2])
        self.assertEqual(frame.shape[1], len(FEATURES) + 3)

    def test_rejects_missing_column(self):
        with self.assertRaises(ValueError):
            select_predictors(sample().drop(columns=FEATURES[0]))

    def test_rejects_duplicate_names(self):
        frame = sample()
        with self.assertRaises(ValueError):
            select_predictors(pd.concat([frame, frame[[FEATURES[0]]]], axis=1))

    def test_rejects_infinite_values(self):
        frame = sample()
        frame.loc[0, NUMERIC[0]] = np.inf
        with self.assertRaises(ValueError):
            select_predictors(frame)

    def test_rejects_text_codes(self):
        frame = sample()
        frame[CATEGORICAL[0]] = "invalid text"
        with self.assertRaises(ValueError):
            select_predictors(frame)

    def test_requires_dataframe_and_nonempty_input(self):
        with self.assertRaises(TypeError):
            select_predictors([[0] * len(FEATURES)])
        with self.assertRaises(ValueError):
            select_predictors(sample().iloc[:0])

    def test_factory_is_unfitted(self):
        with self.assertRaises(NotFittedError):
            build_preprocessor().transform(sample())

    def test_numeric_imputation_uses_training_median(self):
        prep = build_preprocessor().fit(sample())
        numeric = prep.named_transformers_["numeric"]
        np.testing.assert_array_equal(numeric["impute"].statistics_, [20.] * 4)
        np.testing.assert_array_equal(numeric["scale"].mean_, [20.] * 4)
        np.testing.assert_allclose(numeric["scale"].var_, [50.] * 4)
        validation = sample().iloc[[0]].copy()
        validation[NUMERIC] = np.nan
        np.testing.assert_allclose(prep.transform(validation)[:, :4], 0.)

    def test_validation_cannot_change_fitted_statistics(self):
        prep = build_preprocessor().fit(sample())
        numeric = prep.named_transformers_["numeric"]
        before = numeric["scale"].mean_.copy()
        validation = sample().copy()
        validation[NUMERIC] = 1000000.
        prep.transform(validation)
        np.testing.assert_array_equal(numeric["scale"].mean_, before)
        np.testing.assert_array_equal(numeric["impute"].statistics_, [20.] * 4)

    def test_missing_category_uses_training_mode(self):
        training = sample()
        training[CATEGORICAL[0]] = [1., 1., 2., np.nan]
        prep = build_preprocessor().fit(training)
        unknown = training.iloc[[0]].copy()
        unknown[CATEGORICAL[0]] = np.nan
        np.testing.assert_array_equal(prep.transform(unknown), prep.transform(training.iloc[[0]]))

    def test_unseen_category_is_not_learned_from_validation(self):
        training = sample()
        prep = build_preprocessor().fit(training)
        validation = training.iloc[[0]].copy()
        validation[CATEGORICAL[0]] = 99.
        transformed = prep.transform(validation)
        encoder = prep.named_transformers_["categorical"]["encode"]
        self.assertNotIn(99., encoder.categories_[0])
        np.testing.assert_array_equal(transformed[0, 4:6], [0., 0.])
        self.assertTrue(np.isfinite(transformed).all())

    def test_cloning_does_not_share_fitted_state(self):
        prep = build_preprocessor().fit(sample())
        with self.assertRaises(NotFittedError):
            clone(prep).transform(sample())

    def test_extra_columns_do_not_affect_transform(self):
        training = sample()
        prep = build_preprocessor().fit(training)
        extra = training.assign(Target="Graduate", Debtor=999)
        np.testing.assert_array_equal(prep.transform(training), prep.transform(extra))

    def test_historical_folds_have_valid_training_only_transformations(self):
        report = audit_preprocessing()
        self.assertEqual(len(report["folds"]), 5)
        self.assertFalse(report["test_scored"])
        for fold in report["folds"]:
            self.assertEqual(fold["training_rows"] + fold["validation_rows"], 3539)
            self.assertTrue(fold["training_statistics_verified"])
            self.assertTrue(fold["state_unchanged_after_validation_transform"])
            self.assertTrue(fold["finite_outputs"])


if __name__ == "__main__":
    unittest.main()

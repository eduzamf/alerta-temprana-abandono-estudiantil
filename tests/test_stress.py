import unittest

import numpy as np
import pandas as pd

from src.data_processing import load_development, select_predictors
from src.stress import GRADES, perturb, verify


class StressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frame, folds = load_development()
        train, validation = folds[0]
        cls.training = select_predictors(frame.iloc[train])
        cls.X = select_predictors(frame.iloc[validation])
        cls.y = frame.Target.iloc[validation]

    def test_perturbations_preserve_source(self):
        original = self.X.copy(deep=True)
        for scenario in ["missing10", "missing30", "grade_noise", "grades_absent",
                         "course_unseen", "grade_shift", "dropout50"]:
            perturb(self.X, self.y, self.training, scenario, 72)
        pd.testing.assert_frame_equal(original, self.X)

    def test_missing_reproducible(self):
        a, y = perturb(self.X, self.y, self.training, "missing30", 72)
        b, _ = perturb(self.X, self.y, self.training, "missing30", 72)
        pd.testing.assert_frame_equal(a, b)
        self.assertTrue(.27 < a.isna().to_numpy().mean() < .33)
        pd.testing.assert_series_equal(y, self.y)

    def test_noise_uses_training_scale(self):
        seed = 72
        altered, _ = perturb(self.X, self.y, self.training, "grade_noise", seed)
        rng = np.random.default_rng(seed)
        for column in GRADES:
            expected = (self.X[column] + rng.normal(
                0, .2*self.training[column].std(ddof=0), len(self.X))).clip(0, 200)
            np.testing.assert_allclose(altered[column], expected)

    def test_missing_grades_only(self):
        altered, _ = perturb(self.X, self.y, self.training, "grades_absent", 0)
        self.assertTrue(altered[GRADES].isna().all().all())
        np.testing.assert_array_equal(altered.drop(columns=GRADES), self.X.drop(columns=GRADES))

    def test_unseen_course(self):
        altered, _ = perturb(self.X, self.y, self.training, "course_unseen", 0)
        self.assertFalse(altered.Course.isin(self.training.Course).any())

    def test_prevalence_subsample_preserves_order_and_labels(self):
        altered, actual = perturb(self.X, self.y, self.training, "dropout50", 72)
        self.assertEqual(actual.eq("Dropout").sum()*2, len(actual))
        np.testing.assert_array_equal(altered.index, self.X.index[self.X.index.isin(altered.index)])
        pd.testing.assert_series_equal(actual, self.y.loc[altered.index])

    def test_unknown_scenario_rejected(self):
        with self.assertRaises(ValueError):
            perturb(self.X, self.y, self.training, "unknown", 0)

    def test_saved_results_recalculate(self):
        result = verify()
        self.assertTrue(result["verified"])
        self.assertEqual(result["experiments"], 85)
        self.assertFalse(result["test_scored"])


if __name__ == "__main__":
    unittest.main()

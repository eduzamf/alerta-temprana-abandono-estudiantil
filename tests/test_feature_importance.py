"""Check signed importance and aggregation without training or touching test data."""
import unittest

from src.feature_importance import summarize


class ImportanceTests(unittest.TestCase):
    def test_signed_equal_fold_average(self):
        result = summarize(["a", "b"], [[[.1, .3], [-.2, -.4]],
                                        [[.5, .7], [-.6, -.8]]])
        self.assertEqual([row["feature"] for row in result], ["a", "b"])
        self.assertAlmostEqual(result[0]["mean_f1_drop"], .4)
        self.assertAlmostEqual(result[1]["mean_f1_drop"], -.5)

    def test_rejects_shape_and_nonfinite_values(self):
        for values in ([[1, 2]], [[[float("nan"), 1]]]):
            with self.assertRaises(ValueError):
                summarize(["a"], values)

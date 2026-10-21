import copy
import unittest

import numpy as np

from src.data_processing import FEATURES, load_development, select_predictors
from src.finalize import configuration, load_frozen, train, validate_configuration, verify


class FinalModelTests(unittest.TestCase):
    def test_configuration_is_frozen(self):
        config = copy.deepcopy(configuration())
        config["parameters"]["C"] = 10
        with self.assertRaises(ValueError):
            validate_configuration(config)

    def test_scope_and_artifact(self):
        result = verify()
        self.assertEqual(result["training_rows"], 3539)
        self.assertFalse(result["test_used_for_training"])

    def test_overwrite_rejected(self):
        with self.assertRaises(FileExistsError):
            train()

    def test_reloaded_output_contract(self):
        model, metadata = load_frozen()
        frame, _ = load_development()
        X = select_predictors(frame.iloc[:25])
        p = model.predict_proba(X)
        self.assertEqual(p.shape, (25, 3))
        np.testing.assert_allclose(p.sum(axis=1), 1)
        self.assertEqual(metadata["features"], FEATURES)
        self.assertTrue(metadata["serialization_predictions_identical"])


if __name__ == "__main__":
    unittest.main()

"""Baseline configuration and small development-only model contract tests."""
import unittest
import json

import numpy as np
from sklearn.exceptions import NotFittedError
from threadpoolctl import threadpool_limits

from src.data_processing import LABELS, ROOT, load_development, select_predictors
from src.evaluate import measure
from src.model import BASELINES, build_model
from src.verify import verify


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frame, _ = load_development()
        cls.X = select_predictors(frame.iloc[:150])
        cls.y = frame.Target.iloc[:150]

    def test_historical_configurations(self):
        lr = build_model('LR_base')['model']
        rf = build_model('RF_base')['model']
        self.assertEqual(lr.C, 1.)
        self.assertEqual(lr.max_iter, 3000)
        self.assertEqual(lr.class_weight, 'balanced')
        self.assertEqual(rf.n_estimators, 200)
        self.assertEqual(rf.min_samples_leaf, 3)
        self.assertIsNone(rf.max_depth)
        self.assertEqual(rf.max_features, 'sqrt')
        self.assertEqual(rf.class_weight, 'balanced')

    def test_unknown_model_rejected(self):
        with self.assertRaises(ValueError):
            build_model('unknown')

    def test_fresh_pipeline_is_unfitted(self):
        with self.assertRaises(NotFittedError):
            build_model('LR_base').predict(self.X)

    def test_output_contract_all_models(self):
        with threadpool_limits(limits=4):
            for name in BASELINES:
                model = build_model(name).fit(self.X, self.y)
                _, predicted, probabilities = measure(model, self.X.iloc[:5], self.y.iloc[:5])
                self.assertEqual(probabilities.shape, (5, 3))
                np.testing.assert_allclose(probabilities.sum(axis=1), 1.)
                self.assertTrue(set(predicted).issubset(LABELS))

    def test_dummy_does_not_rank_by_features(self):
        model = build_model('Dummy_prior').fit(self.X, self.y)
        probabilities = model.predict_proba(self.X)
        np.testing.assert_allclose(probabilities, np.tile(probabilities[0], (len(self.X), 1)))

    def test_saved_results_recalculate(self):
        result = verify()
        self.assertTrue(result['verified'])
        self.assertEqual(result['oof_rows'], 3 * 3539)

    def test_fixed_baselines_match_historical_means(self):
        # Frozen validation means from Week 3, not thresholds for new candidates.
        expected = {
            'LR_base': [0.5158390651037961, 0.397526856789551, 0.05901570722984206],
            'RF_base': [0.5199557516062783, 0.39137877733982535, 0.2606126794147171],
        }
        report = json.loads((ROOT / 'results/metrics/baseline_results.json').read_text())
        for name, values in expected.items():
            actual = [report['summary'][name][key] for key in ['val_f1_macro', 'val_recall20', 'gap_f1']]
            np.testing.assert_allclose(actual, values, atol=1e-12, rtol=0)


if __name__ == '__main__':
    unittest.main()

"""Protocol and nested selection checks, without scoring the final reserve."""
import unittest

import numpy as np
from sklearn.exceptions import NotFittedError

from src.data_processing import NUMERIC, load_development, select_predictors
from src.optimize import build_candidate, candidates, choose, protocol, verify


class OptimizationTests(unittest.TestCase):
    def test_prespecified_grid_sizes(self):
        config = protocol()
        self.assertEqual(len(candidates('RF_regularized', config)), 18)
        self.assertEqual(len(candidates('LR_quadratic', config)), 3)

    def test_f1_has_priority_over_coverage(self):
        a = dict(strategy='LR_quadratic', parameters={'C': 1.}, inner_f1=.52, inner_recall20=.39)
        b = dict(strategy='LR_quadratic', parameters={'C': .1}, inner_f1=.51, inner_recall20=.50)
        self.assertEqual(choose([a, b]), a)

    def test_ties_use_coverage_then_simplicity(self):
        a = dict(strategy='LR_quadratic', parameters={'C': 1.}, inner_f1=.52, inner_recall20=.39)
        b = dict(strategy='LR_quadratic', parameters={'C': .1}, inner_f1=.52, inner_recall20=.40)
        self.assertEqual(choose([a, b]), b)
        a['inner_recall20'] = .40
        self.assertEqual(choose([a, b]), b)

    def test_rf_constraints(self):
        for params in candidates('RF_regularized', protocol()):
            model = build_candidate('RF_regularized', params)['model']
            self.assertGreater(model.min_samples_leaf, 3)
            self.assertIsNotNone(model.max_depth)

    def test_quadratic_expands_only_numeric_features(self):
        frame, _ = load_development()
        X = select_predictors(frame.iloc[:100])
        model = build_candidate('LR_quadratic', {'C': 1.})
        transformer = model['preprocess']
        result = transformer.fit_transform(X)
        numeric = transformer.named_transformers_['numeric']
        self.assertEqual(numeric['polynomial'].n_features_in_, len(NUMERIC))
        self.assertEqual(numeric['polynomial'].n_output_features_, 14)
        self.assertTrue(np.isfinite(result).all())

    def test_candidates_are_unfitted(self):
        frame, _ = load_development()
        with self.assertRaises(NotFittedError):
            build_candidate('LR_quadratic', {'C': 1.}).predict(select_predictors(frame.iloc[:2]))

    def test_saved_nested_experiment(self):
        result = verify()
        self.assertTrue(result['verified'])
        self.assertEqual(result['oof_predictions'], 7078)
        self.assertFalse(result['test_scored'])


if __name__ == '__main__':
    unittest.main()

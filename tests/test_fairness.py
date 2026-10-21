import json
import unittest

import pandas as pd

from src.data_processing import ROOT
from src.fairness import RATES, compute, counts, wilson


class FairnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = compute()

    def test_wilson_known_value(self):
        p, low, high = wilson(5, 10)
        self.assertEqual(p, .5)
        self.assertAlmostEqual(low, .2365930905)
        self.assertAlmostEqual(high, .7634069095)

    def test_empty_and_extreme_intervals(self):
        self.assertEqual(wilson(0, 0), (None, None, None))
        self.assertGreater(wilson(0, 1)[2], .79)
        self.assertLess(wilson(1, 1)[1], .21)
        with self.assertRaises(ValueError):
            wilson(2, 1)

    def test_ranking_is_not_classifier(self):
        group = pd.DataFrame({'actual': ['Dropout', 'Graduate', 'Enrolled'],
                              'predicted': ['Dropout', 'Graduate', 'Dropout'],
                              'selected_top20': [False, True, True]})
        result = counts(group)
        self.assertEqual(result['selected_non_dropout'], 2)
        self.assertEqual(result['classifier_false_positive'], 1)
        self.assertEqual(result['selected_dropout'], 0)

    def test_subgroups_reconcile(self):
        total = self.report['rows'][0]
        dimensions = {r['dimension'] for r in self.report['rows']} - {'Total'}
        self.assertEqual(len(dimensions), 6)
        for dimension in dimensions:
            rows = [r for r in self.report['rows'] if r['dimension'] == dimension]
            for count in ['n', 'selected', 'dropout', 'selected_dropout', 'selected_non_dropout']:
                self.assertEqual(sum(r[count] for r in rows), total[count])

    def test_denominators_and_bounds(self):
        for row in self.report['rows']:
            for rate, (num, den) in RATES.items():
                if row[den]:
                    self.assertAlmostEqual(row[rate], row[num]/row[den])
                    self.assertLessEqual(row[rate+'_low'], row[rate]+1e-14)
                    self.assertGreaterEqual(row[rate+'_high'], row[rate]-1e-14)
                else:
                    self.assertIsNone(row[rate])

    def test_saved_evidence_recalculates(self):
        saved = json.loads((ROOT / 'results/metrics/fairness_results.json').read_text())
        self.assertEqual(saved, self.report)
        self.assertFalse(saved['test_scored'])
        self.assertEqual(saved['rows'][0]['n'], 3539)

    def test_random_baseline_and_historical_mean(self):
        total = self.report['rows'][0]
        self.assertGreater(total['random_expected_coverage'], .2)
        self.assertLess(total['random_expected_coverage'], .201)
        self.assertAlmostEqual(self.report['historical_mean_fold_coverage'], .397526856789551)


if __name__ == '__main__':
    unittest.main()

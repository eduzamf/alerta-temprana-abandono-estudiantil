"""Metric definitions, ranking ties and invalid inputs."""
import unittest

import numpy as np

from src.evaluate import prediction_metrics, priority_mask


class MetricTests(unittest.TestCase):
    def test_ceiling_and_stable_ties(self):
        np.testing.assert_array_equal(priority_mask([0.5] * 6), [True, True, False, False, False, False])

    def test_ranking_not_input_order_when_scores_differ(self):
        np.testing.assert_array_equal(priority_mask([0.1, 0.8, 0.2, 0.4, 0.3]), [False, True, False, False, False])

    def test_coverage_denominator_is_actual_dropout(self):
        actual = ['Dropout', 'Dropout', 'Graduate', 'Graduate', 'Enrolled']
        probabilities = np.array([[.8, .1, .1], [.6, .2, .2], [.1, .1, .8], [.1, .2, .7], [.1, .8, .1]])
        metrics = prediction_metrics(actual, actual, probabilities)
        self.assertEqual(metrics['f1_macro'], 1.)
        self.assertEqual(metrics['recall20'], .5)

    def test_no_dropout_coverage_is_undefined(self):
        metrics = prediction_metrics(['Graduate'], ['Graduate'], [[.1, .1, .8]])
        self.assertIsNone(metrics['recall20'])

    def test_invalid_probabilities_rejected(self):
        for values in [[[1, 1, 1]], [[np.nan, .2, .8]], [[-.1, .2, .9]], [[.2, .8]]]:
            with self.assertRaises(ValueError):
                prediction_metrics(['Dropout'], ['Graduate'], values)

    def test_invalid_ranking_input_rejected(self):
        for scores in [[], [np.inf], [[.1, .2]]]:
            with self.assertRaises(ValueError):
                priority_mask(scores)
        with self.assertRaises(ValueError):
            priority_mask([.1], fraction=0)

    def test_misaligned_labels_rejected(self):
        with self.assertRaises(ValueError):
            prediction_metrics(['Dropout'], [], [[.8, .1, .1]])


if __name__ == '__main__':
    unittest.main()

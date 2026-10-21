import json
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.data_processing import load_development
from src.final_evaluation import RESULT, PREDICTIONS, load_reserve, run, summarize, verify
from src.finalize import MODEL, digest


class FinalEvaluationTests(unittest.TestCase):
    def test_reserve_disjoint(self):
        development, _ = load_development()
        reserve = load_reserve()
        self.assertEqual(len(reserve), 885)
        self.assertFalse(set(reserve.index) & set(development.index))

    def test_saved_metrics_recalculate(self):
        self.assertTrue(verify()["verified"])

    def test_confusion_counts(self):
        report = json.loads(RESULT.read_text())
        matrix = np.array(report["confusion_matrix"])
        self.assertEqual(matrix.sum(), 885)
        self.assertEqual(report["ranking"]["dropout_detected"]+
                         report["ranking"]["dropout_missed"], report["ranking"]["dropout_total"])
        self.assertEqual(report["ranking"]["selected"], 177)

    def test_frozen_model_unchanged(self):
        self.assertEqual(digest(MODEL),
                         "028b9d7071eaa9549b2cfb64f177f34d2aaf5aeb645eb1f7b4af63b746d8c5f1")

    def test_rerun_only_reads_saved_predictions(self):
        before = RESULT.read_bytes(), PREDICTIONS.read_bytes()
        with patch("src.final_evaluation.measure", side_effect=AssertionError("Must not predict again")):
            with patch("src.final_evaluation.render"):
                run()
        self.assertEqual(before, (RESULT.read_bytes(), PREDICTIONS.read_bytes()))

    def test_target_is_original_threshold(self):
        pred = pd.read_csv(PREDICTIONS, float_precision="round_trip")
        evidence = summarize(pred)
        self.assertEqual(evidence["target_met"], evidence["metrics"]["f1_macro"] >= .6)


if __name__ == "__main__":
    unittest.main()

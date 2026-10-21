"""Integrity and partition tests; no final-test model evaluation."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_processing import (
    DATA_SHA256, FEATURES, ROOT, audit_data, load_development,
    validate_manifest, verify_hash,
)


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.development, cls.folds = load_development()
        cls.manifest = pd.read_csv(ROOT / "data/processed/particiones.csv")

    def test_original_data_hash(self):
        self.assertEqual(verify_hash(ROOT / "data/raw/data.csv", DATA_SHA256), DATA_SHA256)

    def test_tampered_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "changed.csv"
            changed.write_bytes(b"modified data")
            with self.assertRaises(ValueError):
                verify_hash(changed, DATA_SHA256)

    def test_development_excludes_reserve(self):
        reserved = self.manifest.loc[
            self.manifest.partition.eq("test_reserved"), "row_index"
        ]
        self.assertEqual(len(self.development), 3539)
        self.assertEqual(len(reserved), 885)
        self.assertFalse(set(self.development.index) & set(reserved))

    def test_folds_disjoint_and_exhaustive(self):
        seen = []
        for train, val in self.folds:
            self.assertFalse(set(train) & set(val))
            self.assertEqual(len(train) + len(val), len(self.development))
            seen.extend(val)
        np.testing.assert_array_equal(sorted(seen), np.arange(3539))

    def test_historical_validation_membership(self):
        for number, (_, val) in enumerate(self.folds, 1):
            expected = set(self.manifest.loc[self.manifest.cv_fold.eq(number), "row_index"])
            self.assertEqual(set(self.development.index[val]), expected)

    def test_duplicate_row_rejected(self):
        changed = self.manifest.copy()
        changed.loc[0, "row_index"] = changed.loc[1, "row_index"]
        with self.assertRaises(ValueError):
            validate_manifest(changed, 4424)

    def test_reserve_fold_rejected(self):
        changed = self.manifest.copy()
        changed.loc[changed.partition.eq("test_reserved"), "cv_fold"] = 1
        with self.assertRaises(ValueError):
            validate_manifest(changed, 4424)

    def test_feature_contract_and_no_test_scoring(self):
        self.assertEqual(len(FEATURES), 18)
        for name in ["Target", "Scholarship holder", "Debtor", "GDP"]:
            self.assertNotIn(name, FEATURES)
        self.assertFalse(any("sem (" in name for name in FEATURES))
        self.assertFalse(audit_data()["test_scored"])


if __name__ == "__main__":
    unittest.main()

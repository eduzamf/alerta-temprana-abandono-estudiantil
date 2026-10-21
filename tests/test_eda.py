"""Check that descriptive outputs are consistent and development-only."""
import unittest

import pandas as pd

from src.data_processing import FEATURES, load_development
from src.eda import AGE_LABELS, age_groups, summarize


class EdaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame, _ = load_development()
        cls.summary = summarize(cls.frame)

    def test_development_counts(self):
        self.assertEqual(self.summary['rows'], 3539)
        self.assertEqual(self.summary['class_counts'], {
            'Dropout': 1137, 'Enrolled': 635, 'Graduate': 1767,
        })

    def test_all_subgroups_cover_development(self):
        for counts in self.summary['subgroup_counts'].values():
            self.assertEqual(sum(counts.values()), len(self.frame))

    def test_categorical_counts_cover_development(self):
        for item in self.summary['categorical'].values():
            self.assertEqual(sum(item['counts'].values()), len(self.frame))
            self.assertEqual(item['levels'], len(item['counts']))

    def test_fixed_age_boundaries(self):
        actual = age_groups(pd.Series([19, 20, 24, 25, 34, 35])).astype(str).tolist()
        self.assertEqual(actual, [AGE_LABELS[i] for i in [0, 1, 1, 2, 2, 3]])

    def test_age_class_table_totals(self):
        table = pd.DataFrame.from_dict(self.summary['age_outcomes'], orient='index')
        self.assertEqual(table.sum().to_dict(), self.summary['class_counts'])

    def test_numeric_statistics_and_outlier_counts(self):
        for column, stats in self.summary['numeric'].items():
            self.assertEqual(stats['count'], len(self.frame))
            self.assertAlmostEqual(stats['mean'], self.frame[column].mean())
            flags = ((self.frame[column] < stats['iqr_lower']) |
                     (self.frame[column] > stats['iqr_upper']))
            self.assertEqual(stats['iqr_flags'], int(flags.sum()))

    def test_no_model_features_added_for_audit(self):
        self.assertEqual(self.summary['predictor_count'], 18)
        self.assertNotIn('Scholarship holder', FEATURES)
        self.assertNotIn('Debtor', FEATURES)

    def test_summary_does_not_modify_frame(self):
        original = self.frame.copy(deep=True)
        summarize(self.frame)
        pd.testing.assert_frame_equal(original, self.frame)


if __name__ == '__main__':
    unittest.main()

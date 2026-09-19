"""Fourth-lesson label audit: independent arithmetic, masks, and readable outputs."""
from copy import deepcopy
import csv
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.runtime import run_experiment
from mlcourse.foundations import console_summary

DATA = json.loads((ROOT / 'lesson-04/data/base.json').read_text(encoding='utf-8'))
CONFIG = json.loads((ROOT / 'lesson-04/config-start.json').read_text(encoding='utf-8'))


def run(data=None, **patch):
    return run_experiment('S02', deepcopy(DATA if data is None else data), {**CONFIG, **patch})


class LabelAuditReview(unittest.TestCase):
    def test_fixed_cohort_cutoffs_and_independent_sums(self):
        expected = {4: (4, 20, 4), 5: (5, 27, 8), 6: (6, 32, 8), 7: (7, 43, 12)}
        for day, (n, total, error) in expected.items():
            with self.subTest(day=day):
                result = run(observation_day=day)
                m = result['metrics']
                self.assertEqual((m['n'], m['total_rows'], m['unknown_labels']), (n, 8, 8-n))
                self.assertAlmostEqual(m['mean_minutes'], float(Fraction(total, n)))
                self.assertEqual(m['coverage'], n/8)
                self.assertAlmostEqual(m['proxy_mae_observed'], error/n)
                self.assertAlmostEqual(result['comparison']['zero_fill_demo']['mean_minutes'], total/8)
                self.assertEqual(result['comparison']['proxy_all']['mean_minutes'], 4)
                self.assertEqual((m['review_pairs'], m['disagreements']), (n, 1))
                self.assertEqual(len(result['details']['tables']['records']), 8)

    def test_uploaded_zero_is_counted_not_dropped(self):
        data = deepcopy(DATA)
        data['rows'][0]['wait_minutes'] = 0
        result = run(data)
        self.assertEqual((result['metrics']['n'], result['metrics']['mean_minutes']), (4, 19/4))
        self.assertEqual(result['metrics']['coverage'], .5)
        record = result['details']['tables']['records'][0]
        self.assertTrue(record['visible'])
        self.assertEqual(record['observed_minutes'], 0)
        self.assertEqual(record['proxy_absolute_error'], 1)

    def test_missing_second_annotation_is_not_agreement(self):
        data = deepcopy(DATA)
        data['rows'][3]['review_minutes'] = None
        result = run(data)
        m = result['metrics']
        self.assertEqual((m['n'], m['review_pairs'], m['disagreements'], m['agreement']), (4, 3, 0, 1))
        record = result['details']['tables']['records'][3]
        self.assertTrue(record['visible'])
        self.assertIsNone(record['disagreement'])
        self.assertIsNone(record['review_absolute_difference'])

    def test_no_pairs_does_not_mean_all_correct(self):
        data = deepcopy(DATA)
        for row in data['rows']:
            row['review_minutes'] = None
        result = run(data)
        self.assertEqual((result['metrics']['n'], result['metrics']['review_pairs']), (4, 0))
        self.assertIsNone(result['metrics']['agreement'])
        self.assertIn('未定义（没有配对）', console_summary(result))

    def test_no_observed_labels_retains_null_means(self):
        data = deepcopy(DATA)
        for row in data['rows']:
            if row['available_day'] is not None:
                row['available_day'] += 20
        result = run(data)
        m = result['metrics']
        self.assertEqual((m['n'], m['coverage'], m['unknown_labels']), (0, 0, 8))
        for key in ('mean_minutes', 'proxy_mae_observed', 'agreement'):
            self.assertIsNone(m[key])
        self.assertIn('均值 = 未定义', console_summary(result))
        self.assertTrue(all(r['observed_minutes'] is None for r in result['details']['tables']['records']))

    def test_threshold_equality_only_changes_flags(self):
        original, wider = run(), run(disagreement_minutes=3)
        self.assertEqual(original['metrics']['disagreements'], 1)
        self.assertEqual(wider['metrics']['disagreements'], 0)
        self.assertEqual(wider['metrics']['agreement'], 1)
        for key in ('n', 'coverage', 'mean_minutes', 'proxy_mae_observed', 'review_pairs'):
            self.assertEqual(original['metrics'][key], wider['metrics'][key])
        self.assertEqual(run(disagreement_minutes=1)['metrics']['disagreements'], 1)
        data = deepcopy(DATA)
        data['rows'][1]['review_minutes'] = 5  # Difference exactly equals tolerance 2.
        self.assertEqual(run(data)['metrics']['disagreements'], 1)

    def test_future_labels_and_reviews_stay_hidden_in_current_snapshot(self):
        changed = deepcopy(DATA)
        for row in changed['rows']:
            if row['available_day'] is not None and row['available_day'] > 4:
                row['wait_minutes'] += 100
                row['review_minutes'] += 200
        a, b = run(), run(changed)
        self.assertEqual(a['metrics'], b['metrics'])
        self.assertEqual(a['details']['tables'], b['details']['tables'])
        self.assertNotEqual(a['stress_test']['metrics'], b['stress_test']['metrics'])
        r = {x['id']: x for x in a['details']['tables']['records']}
        self.assertTrue(r['A04']['visible'])  # Uploaded on the cutoff is included.
        self.assertFalse(r['A03']['visible'])
        for key in ('observed_minutes', 'review_minutes', 'proxy_absolute_error', 'review_absolute_difference', 'disagreement'):
            self.assertIsNone(r['A03'][key])
        self.assertEqual((r['A03']['day'], r['A03']['available_day']), (3, 6))

    def test_invalid_dates_and_tolerance_have_actionable_errors(self):
        for patch, field in [({'observation_day': 3}, 'observation_day'),
                             ({'observation_day': 8}, 'later_day'),
                             ({'observation_day': 4.5}, 'observation_day'),
                             ({'disagreement_minutes': -1}, 'disagreement_minutes'),
                             ({'disagreement_minutes': True}, 'disagreement_minutes')]:
            with self.subTest(patch=patch), self.assertRaisesRegex(ValueError, field):
                run(**patch)
        self.assertEqual(run(observation_day=7)['metrics'], run(observation_day=7)['stress_test']['metrics'])

    def test_cli_exports_inspectable_dates_and_differences_without_mutating_source(self):
        before = (ROOT/'lesson-04/data/base.json').read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'output'
            env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
            result = subprocess.run([sys.executable, 'lesson-04/analysis.py', '--output', str(out)],
                                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=30, check=True)
            self.assertIn('已收到 4/8', result.stdout)
            self.assertIn('分歧 1 对', result.stdout)
            self.assertIn('一致比例 75%', result.stdout)
            self.assertNotIn('评价样本数', result.stdout)
            with (out/'records.csv').open(encoding='utf-8') as stream:
                rows = {row['id']: row for row in csv.DictReader(stream)}
            self.assertEqual(rows['A04']['review_absolute_difference'], '3')
            self.assertEqual(rows['B02']['proxy_absolute_error'], '4')
            self.assertEqual(rows['A03']['observed_minutes'], '')
            self.assertEqual((ROOT/'lesson-04/data/base.json').read_bytes(), before)
            old_output = (out/'summary.json').read_bytes()
            bad = subprocess.run([sys.executable, 'lesson-04/analysis.py', '--split', 'test', '--output', str(out)],
                                 cwd=ROOT, env=env, text=True, capture_output=True, timeout=30)
            self.assertEqual(bad.returncode, 2)
            self.assertIn('observation_day', bad.stderr)
            self.assertEqual((out/'summary.json').read_bytes(), old_output)


if __name__ == '__main__':
    unittest.main()

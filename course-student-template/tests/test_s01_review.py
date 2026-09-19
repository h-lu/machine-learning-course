"""第三课的手算、阈值、独立新输入和结果展示；不把测试当学生学习实测。"""
from __future__ import annotations
import copy
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


def payload():
    folder = ROOT / 'lesson-03'
    return (json.loads((folder / 'data/base.json').read_text(encoding='utf-8')),
            json.loads((folder / 'config-start.json').read_text(encoding='utf-8')))


class S01FocusedReview(unittest.TestCase):
    def test_hand_calculation_matches_all_six_validation_records(self):
        data, config = payload()
        result = run_experiment('S01', data, config)
        ids = ['A05', 'A06', 'B05', 'B06', 'C05', 'C06']
        actual = [2, 4, 8, 10, 12, 14]
        queue = [0, 1, 1, 2, 2, 3]
        formulas = {'baseline': lambda x: 22/3, 'rule': lambda x: 1+2*x,
                    'linear': lambda x: 13/3+2*x}
        reports = {result['details']['primary_method']: result['metrics'], **result['comparison']}
        for method, formula in formulas.items():
            rows = [r for r in result['details']['tables']['records'] if r['method'] == method]
            self.assertEqual([r['id'] for r in rows], ids)
            self.assertEqual([r['actual'] for r in rows], actual)
            total = 0
            for row, x, y in zip(rows, queue, actual):
                self.assertAlmostEqual(row['prediction'], formula(x), places=8)
                self.assertAlmostEqual(row['absolute_error'], abs(formula(x)-y), places=8)
                total += abs(formula(x)-y)
            self.assertEqual(reports[method]['n'], 6)
            self.assertAlmostEqual(reports[method]['mae'], total/6, places=8)
        self.assertIsNone(reports['no_action']['mae'])

    def test_threshold_includes_equality_and_uses_prediction_not_label(self):
        data, config = payload()
        config.update(primary_model='rule', alert_minutes=3)
        result = run_experiment('S01', data, config)
        target = next(r for r in result['details']['tables']['records']
                      if r['id'] == 'B05' and r['method'] == 'rule')
        self.assertTrue(target['alert'])  # prediction 3 equals the threshold
        config['alert_minutes'] = 8
        result = run_experiment('S01', data, config)
        target = next(r for r in result['details']['tables']['records']
                      if r['id'] == 'B05' and r['method'] == 'rule')
        self.assertEqual(target['actual'], 8)
        self.assertFalse(target['alert'])  # actual 8 must not replace prediction 3

    def test_personal_threshold_choices_preserve_fit_and_predictions(self):
        data, config = payload()
        first = run_experiment('S01', data, config)
        for threshold, count in [(9, 1), (10, 1), (12, 0)]:
            result = run_experiment('S01', data, {**config, 'alert_minutes': threshold})
            self.assertEqual(result['details']['model'], first['details']['model'])
            self.assertEqual(result['metrics']['mae'], first['metrics']['mae'])
            self.assertEqual(result['metrics']['alerts'], count)
            self.assertEqual([r['prediction'] for r in result['details']['tables']['records']],
                             [r['prediction'] for r in first['details']['tables']['records']])

    def test_new_input_is_not_added_to_validation_and_has_no_error(self):
        data, config = payload()
        first = run_experiment('S01', data, config)
        result = run_experiment('S01', data, {**config, 'stress_queue': 4})
        self.assertEqual(result['metrics'], first['metrics'])
        self.assertEqual(result['details'], first['details'])
        stress = result['stress_test']['metrics']
        self.assertIsNone(stress['actual'])
        self.assertNotIn('mae', stress)
        self.assertAlmostEqual(stress['predictions']['baseline'], 22/3, places=8)
        self.assertAlmostEqual(stress['predictions']['rule'], 9, places=8)
        self.assertAlmostEqual(stress['predictions']['linear'], 37/3, places=8)

    def test_console_prioritizes_taught_metrics_and_explains_new_input(self):
        data, config = payload()
        text = console_summary(run_experiment('S01', data, config))
        for term in ('训练样本 12', '验证集 6', 'True=提醒', 'False=不提醒', '新输入检查', '没有标签'):
            self.assertIn(term, text)
        self.assertNotIn('加权误差', text)
        self.assertNotIn('按时段核对', text)

    def test_validation_labels_cannot_change_fit_or_alerts(self):
        data, config = payload()
        first = run_experiment('S01', data, config)
        changed = copy.deepcopy(data)
        for row in changed['rows']:
            if row['split'] == 'validation': row['wait_minutes'] += 10
        result = run_experiment('S01', changed, config)
        self.assertEqual(result['details']['model'], first['details']['model'])
        self.assertEqual(result['metrics']['alerts'], first['metrics']['alerts'])
        self.assertNotEqual(result['metrics']['mae'], first['metrics']['mae'])
        for a, b in zip(first['details']['tables']['records'], result['details']['tables']['records']):
            self.assertEqual((a['prediction'], a['alert']), (b['prediction'], b['alert']))

    def test_bad_personal_input_reports_field_without_new_success(self):
        data, config = payload()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'mine.json'
            path.write_text(json.dumps({**config, 'stress_queue': -1}), encoding='utf-8')
            run = subprocess.run([sys.executable, 'lesson-03/analysis.py', '--config', str(path),
                                  '--output', str(Path(tmp)/'result')], cwd=ROOT,
                                 text=True, capture_output=True, timeout=30,
                                 env={**os.environ, 'OPENBLAS_NUM_THREADS': '1'})
            self.assertEqual(run.returncode, 2)
            self.assertIn('stress_queue', run.stderr)
            self.assertNotIn('结果写入', run.stdout)
            self.assertFalse((Path(tmp)/'result/summary.json').exists())

if __name__ == '__main__':
    unittest.main()

"""实际运行入门路径；验证操作和数值，不冒充真人可读性研究。"""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.runtime import run_experiment

CHANGED = ['alert_minutes', 'observation_day', 'train_through_day',
           'underestimate_weight', 'budget', 'change']
OWN = [{'alert_minutes': 9}, {'disagreement_minutes': 3}, {'train_through_day': 2},
       {'capacity': 1}, {'seed': 11}, {'stress_queue_shift': 1}]


def payload(i, variant='start'):
    folder = ROOT / f'lesson-{i+2:02d}'
    data = json.loads((folder/'data/base.json').read_text(encoding='utf-8'))
    config = json.loads((folder/f'config-{variant}.json').read_text(encoding='utf-8'))
    return data, config, run_experiment(f'S{i:02d}', data, config)


def command(args, cwd):
    return subprocess.run(args, cwd=cwd, text=True, encoding='utf-8', capture_output=True,
                          check=True, timeout=60,
                          env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
                                   PYTHONDONTWRITEBYTECODE='1'))


class GuidedValues(unittest.TestCase):
    def test_prepared_configs_change_exactly_one_named_setting(self):
        for i, field in enumerate(CHANGED, 1):
            with self.subTest(lesson=i):
                _, a, _ = payload(i)
                _, b, _ = payload(i, 'support')
                self.assertEqual(set(a), set(b))
                self.assertEqual([key for key in a if a[key] != b[key]], [field])

    def test_s01_threshold_changes_actions_not_predictions(self):
        a, b = payload(1)[2], payload(1, 'support')[2]
        self.assertEqual((a['metrics']['alerts'], b['metrics']['alerts']), (3, 1))
        self.assertEqual(a['metrics']['mae'], b['metrics']['mae'])
        row = next(r for r in a['details']['tables']['records'] if r['id']=='B05' and r['method']=='rule')
        self.assertEqual((row['prediction'], row['actual'], row['absolute_error']), (3, 8, 5))

    def test_s02_cutoff_and_strict_disagreement_tolerance(self):
        a, b = payload(2)[2], payload(2, 'support')[2]
        self.assertEqual((a['metrics']['n'], a['metrics']['mean_minutes'], a['metrics']['coverage']), (4, 5, .5))
        self.assertEqual(b['metrics']['n'], 7)
        self.assertAlmostEqual(b['metrics']['mean_minutes'], 43/7)
        d, c, _ = payload(2); c.update(OWN[1])
        q = run_experiment('S02', d, c)
        self.assertEqual(q['metrics']['disagreements'], 0)
        self.assertEqual(q['metrics']['n'], 4)

    def test_s03_changed_date_reallocates_records_without_touching_holdout(self):
        d, _, a = payload(3); b = payload(3, 'support')[2]
        self.assertEqual((a['metrics']['train_n'], a['metrics']['n']), (12, 6))
        self.assertEqual((b['metrics']['train_n'], b['metrics']['n']), (9, 9))
        heldout = {r['id'] for r in d['rows'] if r['split']=='test'}
        for result in (a, b):
            for plan in result['details']['splits'].values():
                self.assertFalse(heldout & (set(plan['train_ids']) | set(plan['evaluation_ids'])))
        self.assertEqual(a['comparison']['group'], b['comparison']['group'])
        self.assertEqual(a['comparison']['random'], b['comparison']['random'])

    def test_s04_weight_does_not_change_predictions_or_decisions(self):
        a, b = payload(4)[2], payload(4, 'support')[2]
        for key in ('n','mae','alerts','tp','fp','fn','tn'):
            self.assertEqual(a['metrics'][key], b['metrics'][key])
        self.assertAlmostEqual(a['metrics']['asymmetric_loss'], 55/9)
        self.assertAlmostEqual(b['metrics']['asymmetric_loss'], b['metrics']['mae'])
        d,c,_ = payload(4);c.update(OWN[3]);q=run_experiment('S04',d,c)
        self.assertEqual(q['metrics']['fn'], 3)
        self.assertEqual(sum(q['metrics'][k] for k in ('tp','fp','fn','tn')),6)

    def test_s05_budget_and_label_sources_are_visible(self):
        a,b=payload(5)[2],payload(5,'support')[2]
        self.assertEqual((a['metrics']['added_n'],b['metrics']['added_n']),(4,2))
        self.assertEqual(a['details']['evaluation_ids'],b['details']['evaluation_ids'])
        self.assertAlmostEqual(a['comparison']['synthetic']['mae'],13/3)
        self.assertEqual(a['comparison']['synthetic']['evening_train_n'],0)
        for row in a['details']['tables']['added_samples']:
            self.assertIn('模拟' if row['method']=='synthetic' else '人工教学数据',row['label_source'])

    def test_s06_compares_candidates_to_the_same_original(self):
        a,b=payload(6)[2],payload(6,'support')[2]
        self.assertEqual(a['comparison']['original'],b['comparison']['original'])
        self.assertEqual(a['details']['models']['original'],b['details']['models']['original'])
        self.assertAlmostEqual(a['details']['models']['candidate']['fill_value'],13/9)
        self.assertEqual(b['details']['models']['candidate']['fill_value'],0)
        self.assertEqual(b['details']['models']['candidate']['features'],['queue_length','evening'])

class GuidedWalkthrough(unittest.TestCase):
    def test_foundation_guides_keep_the_reviewed_route_and_optional_levels(self):
        for i in range(3,9):
            folder=ROOT/f'lesson-{i:02d}'
            readme=(folder/'README.md').read_text(encoding='utf-8')
            self.assertIn('(SUPPORT.md)',readme.split('## 本课要学会什么')[0])
            self.assertEqual(len(re.findall(r'^## ',readme,re.M)),7)
            for term in ('入门支持（Support）','必做任务（Core）','提高任务（Upgrade）','换数据重测（Transfer）','自选拓展（Open extension）'):
                self.assertIn(term,readme)
            guide=(folder/'SUPPORT.md').read_text(encoding='utf-8')
            self.assertTrue(any(term in guide for term in ('手算','计算','核对')))

    def test_new_candidate_support_variants_run_from_the_public_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for lesson in range(9,33):
                with self.subTest(lesson=lesson):
                    folder=ROOT/f'lesson-{lesson:02d}'
                    for name in ('config-start.json','config-support.json'):
                        output=base/f'{lesson:02d}'/name.removesuffix('.json')
                        command([sys.executable,str(folder/'analysis.py'),'--config',str(folder/name),'--output',str(output)],ROOT)
                        self.assertTrue((output/'summary.json').is_file())

    def test_documented_commands_personal_changes_and_fresh_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp)/'student'
            shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns('.git','.venv','artifacts','__pycache__','.pytest_cache'))
            command(['git','init','-q'],work)
            command(['git','config','user.name','Guided test'],work)
            command(['git','config','user.email','guided@example.invalid'],work)
            command(['git','add','.'],work)
            for i in range(1,7):
                with self.subTest(lesson=i):
                    folder=work/f'lesson-{i+2:02d}'
                    text=(folder/'SUPPORT.md').read_text(encoding='utf-8')
                    mine=json.loads((folder/'config-start.json').read_text(encoding='utf-8'));mine.update(OWN[i-1])
                    (folder/'config-mine.json').write_text(json.dumps(mine),encoding='utf-8')
                    expected=run_experiment(f'S{i:02d}',json.loads((folder/'data/base.json').read_text()),mine)
                    if i==6:
                        (folder/'config-validation.json').write_text(json.dumps(mine),encoding='utf-8')
                        final={**mine,'evaluation_split':'test'}
                    else:final=mine
                    (folder/'config.json').write_text(json.dumps(final),encoding='utf-8')
                    task=json.loads((folder/'contract.json').read_text(encoding='utf-8'))
                    for key in ('question','user','data_source','metric','split_plan','initial_expectation'):
                        task[key]='操作回归测试用说明，不是学生作业。'
                    (folder/'contract.json').write_text(json.dumps(task,ensure_ascii=False),encoding='utf-8')
                    (folder/'report.md').write_text('# 操作回归测试\n只验证命令和保存，不评价真实学习。\n',encoding='utf-8')
                    sub=json.loads((folder/'submission.json').read_text(encoding='utf-8'));sub['status']='complete'
                    (folder/'submission.json').write_text(json.dumps(sub),encoding='utf-8')
                    for block in re.findall(r'```bash\n(.*?)```',text,re.S):
                        for line in block.strip().splitlines():
                            args=shlex.split(line)
                            self.assertIn(args[0],('python','git'))
                            if args[0]=='python':args[0]=sys.executable
                            # Only local staging is documented; never push student submissions.
                            if args[0]=='git':self.assertIn(args[1],('add','diff'))
                            command(args,work)
                    original=folder/'artifacts/support-start/summary.json'
                    contrast=folder/'artifacts/support-compare/summary.json'
                    self.assertTrue(original.is_file());self.assertTrue(contrast.is_file())
                    actual=json.loads((folder/'artifacts/my-check/summary.json').read_text())
                    self.assertEqual(actual['metrics'],expected['metrics'])
                    self.assertEqual(actual['stress_test'],expected['stress_test'])
                    if i==6:
                        before=json.loads((folder/'artifacts/chosen-validation/summary.json').read_text())
                        after=json.loads((folder/'artifacts/summary.json').read_text())
                        self.assertEqual(before['details']['evaluation_split'],'validation')
                        self.assertEqual(after['details']['evaluation_split'],'test')
                    for path in sub['artifacts']:self.assertTrue((work/path).is_file())
            command(['git','add','.'],work)
            command(['git','commit','-qm','Save guided test artifacts locally'],work)
            fresh=Path(tmp)/'fresh'
            command(['git','clone','-q',str(work),str(fresh)],Path(tmp))
            for i in range(3,9):
                command([sys.executable,'scripts/course.py','check',str(i)],fresh)
                sub=json.loads((fresh/f'lesson-{i:02d}/submission.json').read_text())
                saved={name:(fresh/name).read_bytes() for name in sub['artifacts']}
                command([sys.executable,'scripts/course.py','run',str(i)],fresh)
                for name,value in saved.items():self.assertEqual((fresh/name).read_bytes(),value)


if __name__=='__main__':
    unittest.main()

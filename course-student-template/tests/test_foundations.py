"""新 S01–S06 的独立性质、配置、冷读命令与文件保存检查。不是学生推理评分器。"""
from __future__ import annotations
import copy
import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mlcourse.foundations_data import TITLES, CONFIGS, core_rows, example_data, example_config
from mlcourse.foundations import errors, alert_counts, choose_pool
from mlcourse.runtime import run_experiment


def run(lesson, **patch):
    c=example_config(lesson);c.update(patch)
    return run_experiment(lesson,example_data(lesson),c)


class FoundationalRelationships(unittest.TestCase):
    def test_default_data_and_configuration_match_generator(self):
        for i in range(1,7):
            l=f'S{i:02d}';d=ROOT/f'lesson-{i+2:02d}'
            self.assertEqual(json.loads((d/'data/base.json').read_text()),example_data(l))
            self.assertEqual(json.loads((d/'config.json').read_text()),example_config(l))

    def test_s01_rule_baseline_and_actions_are_separate(self):
        r=run('S01');rows=r['details']['tables']['records']
        item=next(x for x in rows if x['id']=='B05' and x['method']=='rule')
        self.assertEqual((item['actual'],item['prediction'],item['absolute_error']),(8,3,5))
        self.assertIsNone(r['comparison']['no_action']['mae'])
        self.assertIsNone(r['details']['intervention_effect'])
        altered=run('S01',alert_minutes=10)
        self.assertEqual(r['metrics']['mae'],altered['metrics']['mae'])
        self.assertNotEqual(r['metrics']['alerts'],altered['metrics']['alerts'])
        self.assertIsNone(r['stress_test']['metrics']['actual'])

    def test_s02_unknown_is_not_zero_and_denominators_are_explicit(self):
        r=run('S02');m=r['metrics']
        self.assertEqual((m['n'],m['unknown_labels'],m['coverage'],m['mean_minutes']),(4,4,.5,5))
        self.assertEqual(r['comparison']['zero_fill_demo']['mean_minutes'],2.5)
        self.assertEqual((m['proxy_mae_observed'],m['review_pairs'],m['disagreements'],m['agreement']),(1,4,1,.75))
        self.assertEqual(r['details']['visible_ids'],['A01','A02','A04','B02'])
        for row in r['details']['tables']['records']:
            if not row['visible']:
                self.assertIsNone(row['observed_minutes']);self.assertIsNone(row['review_minutes'])

    def test_s02_future_labels_do_not_enter_current_statistics(self):
        d=example_data('S02');c=example_config('S02');r=run_experiment('S02',d,c)
        d['rows'][2]['wait_minutes']+=100
        q=run_experiment('S02',d,c)
        self.assertEqual(r['metrics'],q['metrics'])
        self.assertNotEqual(r['stress_test']['metrics'],q['stress_test']['metrics'])

    def test_s02_no_available_labels_or_review_pairs_remain_undefined(self):
        d=example_data('S02')
        for row in d['rows']:
            if row['available_day'] is not None:row['available_day']=20
        r=run_experiment('S02',d,example_config('S02'))
        self.assertEqual(r['metrics']['n'],0)
        self.assertIsNone(r['metrics']['mean_minutes']);self.assertIsNone(r['metrics']['agreement'])
        self.assertIsNone(r['metrics']['proxy_mae_observed'])

    def test_s02_cutoff_does_not_include_not_yet_occurred_cases(self):
        with self.assertRaisesRegex(ValueError, "observation_day"):
            run('S02', observation_day=3)

    def test_s03_every_plan_keeps_the_final_holdout_out_of_training_and_validation(self):
        r=run('S03');rows=example_data('S03')['rows'];byid={x['id']:x for x in rows}
        holdout={x['id'] for x in rows if x['split']=='test'}
        for name,p in r['details']['splits'].items():
            tr=set(p['train_ids']);ev=set(p['evaluation_ids'])
            self.assertFalse(tr & ev);self.assertFalse(holdout & (tr|ev))
            if name=='group':self.assertFalse({byid[i]['site'] for i in tr}&{byid[i]['site'] for i in ev})
            if name=='time':self.assertLess(max(byid[i]['day'] for i in tr),min(byid[i]['day'] for i in ev))
        self.assertEqual(r['comparison']['group']['n'],6)
        self.assertEqual(r['comparison']['group']['shared_sites'],0)

    def test_s03_test_labels_do_not_change_development_comparisons(self):
        d=example_data('S03');c=example_config('S03');a=run_experiment('S03',d,c)
        for row in d['rows']:
            if row['split']=='test':row['wait_minutes']+=100;row['receipt_minutes']+=100
        b=run_experiment('S03',d,c)
        for key in ('metrics','comparison','details'):self.assertEqual(a[key],b[key])
        self.assertGreater(a['metrics']['mae'],0)
        self.assertAlmostEqual(a['metrics']['leaked_mae_demo'],0,places=7)

    def test_s04_weighted_loss_can_reverse_mae_ranking_without_changing_predictions(self):
        r=run('S04');q=run('S04',underestimate_weight=1)
        self.assertLess(r['metrics']['mae'],r['comparison']['buffered']['mae'])
        self.assertGreater(r['metrics']['asymmetric_loss'],r['comparison']['buffered']['asymmetric_loss'])
        self.assertEqual(r['metrics']['mae'],q['metrics']['mae'])
        self.assertEqual([x['prediction'] for x in r['details']['tables']['records']],
                         [x['prediction'] for x in q['details']['tables']['records']])
        self.assertEqual(errors([4,8],[2,6],3)['asymmetric_loss'],6)

    def test_s04_capacity_counts_and_ties_do_not_use_labels(self):
        rows=[dict(id='a',wait_minutes=3),dict(id='b',wait_minutes=9),dict(id='c',wait_minutes=10)]
        m,flags=alert_counts(rows,[12,1,12],8,8,2)
        self.assertEqual((m['tp'],m['fp'],m['fn'],m['tn']),(1,1,1,0))
        self.assertEqual(flags,[True,False,True])
        none,flags=alert_counts(rows,[12,1,12],8,8,0)
        self.assertEqual(none['alerts'],0);self.assertEqual(none['fn'],2)
        m,flags=alert_counts(rows,[12,12,12],8,8,1)
        self.assertEqual(flags,[True,False,False])
        with self.assertRaises(ValueError):alert_counts(rows,[12,1,12],8,8,4)
        r=run('S04');self.assertEqual(r['metrics']['fn'],2)
        self.assertEqual(r['stress_test']['metrics']['linear']['fn'],3)

    def test_s05_candidate_selection_does_not_require_labels(self):
        pool=[dict(id='a',period='午间'),dict(id='b',period='晚间'),dict(id='c',period='晚间')]
        self.assertEqual([r['id'] for r in choose_pool(pool,2,'group_first','晚间',7)],['b','c'])
        self.assertEqual(len(choose_pool(pool,2,'random_sample','晚间',7)),2)

    def test_s05_same_budget_unique_pool_ids_and_same_evaluation(self):
        r=run('S05');pool={x['id'] for x in example_data('S05')['rows'] if x['split']=='pool'}
        for method in ('random_sample','group_first'):
            ids=r['details']['selected_ids'][method]
            self.assertEqual(len(ids),4);self.assertEqual(len(set(ids)),4);self.assertTrue(set(ids)<=pool)
        records=r['details']['tables']['records']
        ids=[{x['id'] for x in records if x['method']==m} for m in ('no_addition','random_sample','group_first','synthetic')]
        self.assertTrue(all(i==ids[0] for i in ids))
        self.assertEqual(r['comparison']['synthetic']['mae'],r['comparison']['no_addition']['mae'])
        self.assertEqual(r['comparison']['synthetic']['evening_train_n'],0)

    def test_s05_pool_label_changes_cannot_select_favorable_ids(self):
        d=example_data('S05');c=example_config('S05');a=run_experiment('S05',d,c)
        for row in d['rows']:
            if row['split']=='pool':row['wait_minutes']+=20
        b=run_experiment('S05',d,c)
        self.assertEqual(a['details']['selected_ids'],b['details']['selected_ids'])
        self.assertNotEqual(a['metrics']['mae'],b['metrics']['mae'])

    def test_s06_only_one_factor_changes_and_mean_is_train_only(self):
        r=run('S06');m=r['details']['models']
        self.assertAlmostEqual(m['candidate']['fill_value'],13/9)
        self.assertEqual(m['original']['features'],m['candidate']['features'])
        q=run('S06',change='period_feature');old,new=q['details']['models'].values()
        self.assertEqual(old['fill_value'],new['fill_value'])
        self.assertEqual(new['features'],['queue_length','evening'])
        self.assertEqual(r['comparison']['original'],q['comparison']['original'])
        base={x['id']:x for x in core_rows()}
        for row in example_data('S06')['rows']:
            self.assertEqual(row['wait_minutes'],base[row['id']]['wait_minutes'])

    def test_s06_evaluation_values_never_fit_imputer_or_model(self):
        d=example_data('S06');c=example_config('S06');a=run_experiment('S06',d,c)
        for row in d['rows']:
            if row['split']!='train':row['queue_length']=100;row['wait_minutes']=1000
        b=run_experiment('S06',d,c)
        self.assertEqual(a['details']['models'],b['details']['models'])
        self.assertNotEqual(a['metrics']['mae'],b['metrics']['mae'])

    def test_input_and_config_failures_are_visible(self):
        for lesson,patch in [('S01',{'primary_model':'typo'}),('S02',{'later_day':1}),('S03',{'train_through_day':6}),
                              ('S04',{'capacity':True}),('S05',{'budget':99}),('S06',{'change':'both'})]:
            with self.subTest(lesson=lesson),self.assertRaises(ValueError):run(lesson,**patch)
        for lesson in TITLES:
            d=example_data(lesson);d['rows'][0]['id']=d['rows'][1]['id']
            with self.assertRaisesRegex(ValueError,'id'):run_experiment(lesson,d,example_config(lesson))
        with self.assertRaisesRegex(ValueError,'未知'):run('S01',alert_minuts=10)

    def test_run_is_deterministic_and_does_not_mutate_inputs(self):
        for lesson in TITLES:
            d=example_data(lesson);c=example_config(lesson);saved=copy.deepcopy((d,c))
            a=run_experiment(lesson,d,c);b=run_experiment(lesson,d,c)
            self.assertEqual(a,b);self.assertEqual((d,c),saved)


class FoundationColdRead(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'student'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','.venv','__pycache__','artifacts','.pytest_cache'))
    def cmd(self,*args,check=True,cwd=None):
        return subprocess.run(args,cwd=cwd or self.root,text=True,capture_output=True,check=check,timeout=60,
                              env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1'})
    def test_all_readme_trial_json_and_commands_run_and_preserve_originals(self):
        for i in range(1,7):
            folder=f'lesson-{i+2:02d}';text=(self.root/folder/'README.md').read_text()
            trial=(json.loads((self.root/folder/'config-support.json').read_text()) if i == 1
                   else json.loads(re.search(r'```json\n(.*?)\n```',text,re.S).group(1)))
            self.cmd(sys.executable,'scripts/course.py','start',f'{i+2:02d}')
            original=[f'{folder}/analysis.py']
            if i == 1: original += ['--config', f'{folder}/config-start.json']
            original += ['--output',f'{folder}/artifacts/original']
            if i == 2:
                # S02 now supplies a fixed starting config, a date contrast, then a personal check.
                original=[f'{folder}/analysis.py','--config',f'{folder}/config-start.json','--output',f'{folder}/artifacts/original']
            self.assertIn('python '+' '.join(original),text)
            result=self.cmd(sys.executable,*original)
            self.assertIn('comparison.csv',result.stdout);self.assertIn('records.csv',result.stdout)
            old=(self.root/folder/'artifacts/original/records.csv').read_bytes()
            config_name, output_name = ('config-support.json', 'trial') if i == 1 else (('config-mine.json', 'my-check') if i == 2 else ('config-trial.json', 'trial'))
            if i == 2:
                contrast=[f'{folder}/analysis.py','--config',f'{folder}/config-support.json','--output',f'{folder}/artifacts/trial']
                self.assertIn('python '+' '.join(contrast),text)
                self.cmd(sys.executable,*contrast)
                dated=json.loads((self.root/folder/'artifacts/trial/summary.json').read_text())
                self.assertEqual(dated['details']['observation_day'],7)
                self.assertEqual(dated['metrics']['n'],7)
                self.assertEqual(old,(self.root/folder/'artifacts/original/records.csv').read_bytes())
            if i != 1:
                (self.root/folder/config_name).write_text(json.dumps(trial,ensure_ascii=False))
            args=[f'{folder}/analysis.py','--config',f'{folder}/{config_name}','--output',f'{folder}/artifacts/{output_name}']
            self.assertIn('python '+' '.join(args),text);self.cmd(sys.executable,*args)
            self.assertEqual(old,(self.root/folder/'artifacts/original/records.csv').read_bytes())
            payload=json.loads((self.root/folder/f'artifacts/{output_name}/summary.json').read_text())
            if i == 2:
                self.assertEqual(payload['details']['observation_day'],4)
                self.assertEqual(payload['metrics']['disagreements'],0)
            with (self.root/folder/f'artifacts/{output_name}/records.csv').open(encoding='utf-8', newline='') as f:
                table=list(csv.DictReader(f))
            self.assertEqual(len(table),len(payload['details']['tables']['records']))
            self.assertEqual(payload['status'],'example_only')

    def test_bad_split_and_json_give_errors_not_success(self):
        p=self.root/'lesson-04/config-bad.json';p.write_text('{"observation_day":4,}')
        r=self.cmd(sys.executable,'lesson-04/analysis.py','--config','lesson-04/config-bad.json',check=False)
        self.assertEqual(r.returncode,2);self.assertIn('config-bad.json',r.stderr)
        r=self.cmd(sys.executable,'lesson-04/analysis.py','--split','test',check=False)
        self.assertEqual(r.returncode,2);self.assertIn('observation_day',r.stderr)

    def test_s06_validation_then_test_keeps_snapshot(self):
        folder=self.root/'lesson-08';config=example_config('S06')
        (folder/'config-validation.json').write_text(json.dumps(config))
        self.cmd(sys.executable,'lesson-08/analysis.py','--config','lesson-08/config-validation.json','--split','validation','--output','lesson-08/artifacts/validation')
        old=(folder/'artifacts/validation/records.csv').read_bytes()
        config['evaluation_split']='test';(folder/'config.json').write_text(json.dumps(config))
        self.cmd(sys.executable,'scripts/course.py','run','08')
        self.assertEqual(old,(folder/'artifacts/validation/records.csv').read_bytes())
        r=json.loads((folder/'artifacts/summary.json').read_text())
        self.assertEqual(r['details']['evaluation_split'],'test')
        self.assertTrue(all(x.endswith(('07','08')) for x in r['details']['evaluation_ids']))

    def test_full_data_generator_matches_new_lesson_data(self):
        target=Path(self.tmp.name)/'generated'
        self.cmd(sys.executable,'scripts/build_example_data.py','--output',str(target))
        for i in range(1,7):
            p=target/f'lesson-{i+2:02d}'
            self.assertEqual(json.loads((p/'data/base.json').read_text()),example_data(f'S{i:02d}'))
            self.assertEqual((p/'data/DATA.md').read_text(),(self.root/f'lesson-{i+2:02d}/data/DATA.md').read_text())

    def test_results_tracked_and_reproduced_from_fresh_local_clone(self):
        # Local-only Git repository: never sends student code, credentials or classroom tags to a remote.
        for n in range(3,9):
            folder=self.root/f'lesson-{n:02d}'
            self.cmd(sys.executable,'scripts/course.py','run',str(n))
            task=json.loads((folder/'contract.json').read_text())
            for key in ('question','user','data_source','metric','split_plan','initial_expectation'):task[key]='只用于文件与重跑测试的说明，不是学生成果'
            (folder/'contract.json').write_text(json.dumps(task))
            (folder/'report.md').write_text('文件流程测试，实际学生仍需完成自己的比较与解释。')
            sub=json.loads((folder/'submission.json').read_text());sub['status']='complete';(folder/'submission.json').write_text(json.dumps(sub))
            self.cmd(sys.executable,'scripts/course.py','check',str(n))
        self.cmd('git','init','-q');self.cmd('git','add','.')
        for n in range(3,9):self.cmd('git','add','-f',f'lesson-{n:02d}/artifacts')
        self.cmd('git','-c','user.name=Local test','-c','user.email=test@example.invalid','commit','-qm','Test artifact submission')
        clone=Path(self.tmp.name)/'clone';self.cmd('git','clone','-q',str(self.root),str(clone))
        self.cmd(sys.executable,'scripts/course.py','ci',cwd=clone)
        for n in range(3,9):self.assertTrue((clone/f'lesson-{n:02d}/artifacts/records.csv').is_file())


if __name__=='__main__':unittest.main()

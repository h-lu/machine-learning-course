"""Run with python3 -m unittest discover -s tests -p test_bike08.py.

All test evaluation is temporary synthetic data; no student answer artifacts.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import csv
from datetime import datetime
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np

STUDENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDENT/'scripts'))
import bike_runtime as br


def csv_rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


class Bike08Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bike08-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'scripts').mkdir()
        for file in br.SOURCE_FILES:
            (self.root/file).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(STUDENT/file, self.root/file)
        (self.root/'data/bike').mkdir(parents=True)
        self.data = self.root/'data/bike/hour.csv'
        self.config_path = self.root/'config.json'
        self.config = {**br.DEFAULTS}
        br.write_json(self.config_path, self.config)
        fieldnames = ['instant', 'dteday', 'season', 'yr', 'mnth', 'hr', 'holiday', 'weekday',
                      'workingday', 'weathersit', 'temp', 'atemp', 'hum', 'windspeed',
                      'casual', 'registered', 'cnt']
        rows = []
        for day in ['2012-06-02','2012-06-04','2012-06-05','2012-07-02','2012-07-07','2012-10-02','2012-10-06']:
            dt = datetime.fromisoformat(day)
            work = int(dt.weekday() < 5)
            for hour in range(24):
                count = 20 + hour*2 + 100*int(hour in (8,17)) + 35*work*int(hour in (8,17))
                rows.append({'instant':len(rows)+1,'dteday':day,'season':2,'yr':1,'mnth':dt.month,
                             'hr':hour,'holiday':0,'weekday':(dt.weekday()+1)%7,'workingday':work,
                             'weathersit':1,'temp':.4+hour/100,'atemp':.4,'hum':.5,'windspeed':.2,
                             'casual':0,'registered':count,'cnt':count})
        with self.data.open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=fieldnames)
            writer.writeheader(); writer.writerows(rows)
        self.plan_path = self.root/'preregister.json'
        self.plan = br.preregister_draft(self.config)
        self.plan.update(primary_metric='overall_mae',
                         hypothesis='This synthetic candidate should improve hour shape.',
                         explanation='Only the hour encoding changes; common calendar and weather are fixed.',
                         check_reason='The synthetic purpose values overall error while limiting subgroup harm.',
                         check_rule={'minimum_primary_improvement':0.,'maximum_secondary_mae_increase':10.})
        br.write_json(self.plan_path,self.plan)

    def run_validation(self, name='validation'):
        out=self.root/name
        with redirect_stdout(io.StringIO()):
            br.run_bike(self.root,self.config_path,out,preregister_path=self.plan_path,allow_fixture=True)
        return out

    def save_decision(self, reviewed, method='original'):
        decision=br.decision_draft(self.root,reviewed)
        decision.update(selected_method=method,reason='The saved validation evidence supports this fixed choice.')
        path=self.root/'decision.json'
        br.write_json(path,decision)
        return path

    def test_validation_requires_own_completed_preregistration(self):
        with self.assertRaisesRegex(ValueError,'preregister'):
            br.run_bike(self.root,self.config_path,self.root/'invalid',allow_fixture=True)
        self.assertFalse((self.root/'invalid').exists())
        br.write_json(self.plan_path,br.preregister_draft(self.config))
        with self.assertRaisesRegex(ValueError,'primary_metric'):
            self.run_validation()

    def test_single_factor_feature_changes_and_excluded_targets(self):
        rows,_=br.load_data(self.data,True)
        numeric,names=br.features(rows,'hour_numeric')
        onehot,one_names=br.features(rows,'hour_onehot')
        interaction,int_names=br.features(rows,'workingday_interaction')
        self.assertEqual(names[1:],one_names[23:])
        np.testing.assert_array_equal(numeric[:,1:],onehot[:,23:])
        self.assertEqual(int_names[:len(one_names)],one_names)
        np.testing.assert_array_equal(interaction[:,:len(one_names)],onehot)
        work=np.asarray([r['workingday'] for r in rows])
        np.testing.assert_array_equal(interaction[:,len(one_names):],onehot[:,:23]*work[:,None])
        self.assertTrue({'cnt','casual','registered','instant'}.isdisjoint(int_names))
        self.assertNotIn('hr_0',one_names)

    def test_scale_coefficients_train_only_and_common_clip(self):
        rows,_=br.load_data(self.data,True)
        splits=br.split_data(rows,self.config)
        model=br.fit(splits['train'],'hour_numeric')
        x,_=br.features(splits['train'],'hour_numeric')
        np.testing.assert_allclose(model['center'],x.mean(0))
        self.assertEqual(model['train_rows'],72)
        model['weights'][:]=0
        model['weights'][0]=-123
        np.testing.assert_array_equal(br.predict(model,splits['validation']),np.zeros(48))

    def test_validation_has_no_test_scores_and_null_empty_groups(self):
        out=self.run_validation()
        result=br.read_json(out/'metrics.json')
        self.assertEqual(set(result['metrics']),{'train','validation'})
        self.assertTrue(result['test_sealed'])
        records=csv_rows(out/'records.csv')
        self.assertEqual({r['split'] for r in records},{'train','validation'})
        self.assertEqual(len(records),2*(72+48))
        groups=csv_rows(out/'group_metrics.csv')
        empty=[r for r in groups if r['dimension']=='weather' and r['group']=='4']
        self.assertTrue(empty)
        self.assertTrue(all(r['n']=='0' and r['mae']=='' and r['status']=='unavailable' for r in empty))
        audit=br.read_json(out/'data_audit.json')
        self.assertNotIn('test_target_mean',audit)

    def test_commute_definition_and_trace_reconstruction(self):
        self.assertFalse(br.is_commute({'workingday':0,'hr':8}))
        self.assertTrue(br.is_commute({'workingday':1,'hr':8}))
        self.assertFalse(br.is_commute({'workingday':1,'hr':12}))
        out=self.run_validation()
        trace=csv_rows(out/'feature_trace.csv')
        for method in ['original','candidate']:
            subset=[r for r in trace if r['method']==method]
            total=sum(float(r['contribution']) for r in subset)
            self.assertAlmostEqual(total,float(subset[0]['raw_prediction']),places=9)
            self.assertAlmostEqual(max(0,total),float(subset[0]['clipped_prediction']),places=9)
            for r in subset:
                if r['feature']!='intercept':
                    value=(float(r['raw_feature'])-float(r['training_mean']))/float(r['training_scale'])
                    self.assertAlmostEqual(value,float(r['standardized_feature']),places=12)

    def test_replay_bytes_identical_no_output_overwrite(self):
        first=self.run_validation('first'); second=self.run_validation('second')
        self.assertEqual({p.name for p in first.iterdir()},{p.name for p in second.iterdir()})
        for file in first.iterdir():
            self.assertEqual(file.read_bytes(),(second/file.name).read_bytes(),file.name)
        with self.assertRaisesRegex(ValueError,'已经存在'):
            self.run_validation('first')

    def test_test_requires_decision_and_only_evaluates_selected(self):
        out=self.run_validation()
        with self.assertRaisesRegex(ValueError,'decision'):
            br.run_bike(self.root,self.config_path,self.root/'bad-test',unlock_test=True,allow_fixture=True)
        decision=self.save_decision(out)
        test=self.root/'test'
        with redirect_stdout(io.StringIO()):
            br.run_bike(self.root,self.config_path,test,unlock_test=True,decision_path=decision,allow_fixture=True)
        result=br.read_json(test/'metrics.json')
        self.assertEqual(set(result['metrics']),{'test'})
        self.assertEqual(set(result['metrics']['test']),{'original'})
        self.assertEqual(set(br.read_json(test/'models.json')),{'original'})
        records=csv_rows(test/'records.csv')
        self.assertEqual({r['method'] for r in records},{'original'})
        self.assertEqual(len(records),48)

    def test_failed_preregister_rule_cannot_select_candidate_for_test(self):
        self.plan['check_rule']['minimum_primary_improvement']=1e6
        br.write_json(self.plan_path,self.plan)
        out=self.run_validation()
        decision=self.save_decision(out,'candidate')
        with self.assertRaisesRegex(ValueError,'未通过'):
            br.run_bike(self.root,self.config_path,self.root/'bad-test',unlock_test=True,decision_path=decision,allow_fixture=True)
        self.assertFalse((self.root/'bad-test').exists())

    def test_validation_mutation_and_source_or_config_changes_rejected(self):
        out=self.run_validation()
        decision=self.save_decision(out)
        summary=out/'summary.json'
        saved=summary.read_bytes(); summary.write_bytes(saved+b' ')
        with self.assertRaisesRegex(ValueError,'已被修改'):
            br.run_bike(self.root,self.config_path,self.root/'bad1',unlock_test=True,decision_path=decision,allow_fixture=True)
        summary.write_bytes(saved)
        source=self.root/'scripts/lesson08.py'
        saved_source=source.read_bytes();source.write_bytes(saved_source+b'\n# changed\n')
        with self.assertRaisesRegex(ValueError,'程序已改变'):
            br.run_bike(self.root,self.config_path,self.root/'bad2',unlock_test=True,decision_path=decision,allow_fixture=True)
        source.write_bytes(saved_source)
        self.config['condition_hour_shift']=2
        br.write_json(self.config_path,self.config)
        with self.assertRaisesRegex(ValueError,'配置'):
            br.run_bike(self.root,self.config_path,self.root/'bad3',unlock_test=True,decision_path=decision,allow_fixture=True)

    def test_test_target_values_do_not_fit_or_define_tail(self):
        first=self.run_validation('first')
        fieldnames=[];rows=[]
        with self.data.open(newline='') as stream:
            reader=csv.DictReader(stream);fieldnames=reader.fieldnames;rows=list(reader)
        for row in rows:
            if row['dteday'] >= self.config['validation_end']:
                row['cnt']='99999';row['registered']='99999';row['casual']='0'
        with self.data.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fieldnames);writer.writeheader();writer.writerows(rows)
        second=self.run_validation('second')
        for name in ['models.json','metrics.json','records.csv','feature_trace.csv','condition_check.json']:
            self.assertEqual((first/name).read_bytes(),(second/name).read_bytes(),name)
        decision=self.save_decision(first)
        with self.assertRaisesRegex(ValueError,'数据'):
            br.run_bike(self.root,self.config_path,self.root/'bad-test',unlock_test=True,decision_path=decision,allow_fixture=True)

    def test_default_replay_protects_student_notes_and_handles_ci_partial_cleanup(self):
        default=self.root/'lesson-08/artifacts/run'
        with redirect_stdout(io.StringIO()):
            br.run_bike(self.root,self.config_path,default,preregister_path=self.plan_path,
                        allow_fixture=True,replace_default=True)
        first=(default/'metrics.json').read_bytes()
        for name in ['summary.json','comparison.csv','records.csv']:
            (default/name).unlink()
        with redirect_stdout(io.StringIO()):
            br.run_bike(self.root,self.config_path,default,preregister_path=self.plan_path,
                        allow_fixture=True,replace_default=True)
        self.assertEqual(first,(default/'metrics.json').read_bytes())
        (default/'student_notes.txt').write_text('Keep my interpretation.')
        with self.assertRaisesRegex(ValueError,'非运行产物'):
            br.run_bike(self.root,self.config_path,default,preregister_path=self.plan_path,
                        allow_fixture=True,replace_default=True)
        self.assertEqual((default/'student_notes.txt').read_text(),'Keep my interpretation.')

    def test_paths_cannot_escape_student_root(self):
        with self.assertRaises(ValueError):
            br.safe_path(self.root,'../outside.json')


if __name__=='__main__':
    unittest.main()

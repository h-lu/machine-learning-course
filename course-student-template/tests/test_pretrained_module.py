"""S13–S18 连续作品的运行与证据边界回归；不代替真人试读。"""
from __future__ import annotations
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

def run(work:Path,lesson:int,config:str,output:str,data:str|None=None):
    requested=Path(output)
    output_path=requested if requested.is_absolute() else Path(f'lesson-{lesson:02d}')/requested
    cmd=[sys.executable,f'lesson-{lesson:02d}/analysis.py','--config',f'lesson-{lesson:02d}/{config}','--output',str(output_path)]
    if data: cmd += ['--data',f'lesson-{lesson:02d}/{data}']
    subprocess.run(cmd,cwd=work,check=True,capture_output=True,text=True,timeout=30)
    return requested if requested.is_absolute() else work/output_path
def rows(path):
    with path.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))

class PretrainedModule(unittest.TestCase):
    def test_support_configs_change_one_field(self):
        fields=['context_boost','changed_future_value','prompt_text','min_overlap','routes','presentation_order']
        for lesson,field in zip(range(15,21),fields,strict=True):
            folder=ROOT/f'lesson-{lesson:02d}'
            a=json.loads((folder/'config-start.json').read_text()); b=json.loads((folder/'config-support.json').read_text())
            self.assertEqual([key for key in a if a[key]!=b[key]],[field])

    def test_s13_sources_and_parameter_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=run(ROOT,15,'config-start.json',str(Path(tmp).resolve()))
            routes={r['route']:r for r in rows(out/'routes.csv')}
            self.assertEqual(routes['fixed_record']['changed_parameters'],'False')
            self.assertEqual(routes['input_context_rule']['changed_parameters'],'False')
            self.assertEqual(routes['trained_output_head']['changed_parameters'],'True')
            trace=rows(out/'parameter_trace.csv'); self.assertNotEqual(trace[0]['weight'],trace[-1]['weight'])

    def test_s14_future_is_blocked_only_by_causal_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=run(ROOT,16,'config-start.json',str(Path(tmp).resolve()))
            table={(r['id'],r['condition']):float(r['absolute_change']) for r in rows(out/'visibility.csv')}
            self.assertEqual(table['sequence-01','causal_mask'],0)
            self.assertGreater(table['sequence-01','no_mask'],1)

    def test_s15_new_prompt_has_new_outputs_and_final_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=run(ROOT,17,'config-start.json',str(Path(tmp)/'old')); new=run(ROOT,17,'config-support.json',str(Path(tmp)/'new')); final=run(ROOT,17,'config-final.json',str(Path(tmp)/'final'),'data/final.json')
            a={r['id']:r['output'] for r in rows(old/'responses.csv') if r['repeat']=='1'}; b={r['id']:r['output'] for r in rows(new/'responses.csv') if r['repeat']=='1'}
            self.assertNotEqual(a['dev-04'],b['dev-04']); self.assertIn('资料不足',b['dev-04'])
            self.assertEqual({r['split'] for r in rows(final/'responses.csv')},{'final'})

    def test_final_data_and_submission_are_explicitly_separated(self):
        keys={17:'rows',18:'queries',20:'cases'}
        expected_artifacts={17:'responses.csv',18:'checks.csv',20:'dimension_scores.csv'}
        for lesson,key in keys.items():
            with self.subTest(lesson=lesson):
                folder=ROOT/f'lesson-{lesson:02d}'
                development=json.loads((folder/'data/base.json').read_text(encoding='utf-8'))
                final_data=json.loads((folder/'data/final.json').read_text(encoding='utf-8'))
                self.assertEqual({row['split'] for row in development[key]},{'development'})
                self.assertEqual({row['split'] for row in final_data[key]},{'final'})
                self.assertTrue({row['id'] for row in development[key]}.isdisjoint({row['id'] for row in final_data[key]}))
                default=json.loads((folder/'submission.json').read_text(encoding='utf-8'))
                final=json.loads((folder/'submission-final.json').read_text(encoding='utf-8'))
                default_command=' '.join(default['run']); final_command=' '.join(final['run'])
                self.assertNotIn('final.json',default_command)
                self.assertNotIn('config-final.json',default_command)
                self.assertIn('data/final.json',final_command)
                self.assertIn('config-final.json',final_command)
                self.assertIn(f'lesson-{lesson:02d}/artifacts/{expected_artifacts[lesson]}',final['artifacts'])

    def test_s16_and_s18_final_commands_use_only_final_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            retrieval=run(ROOT,18,'config-final.json',str(Path(tmp)/'retrieval'),'data/final.json')
            evaluation=run(ROOT,20,'config-final.json',str(Path(tmp)/'evaluation'),'data/final.json')
            self.assertEqual({row['query_id'].split('-')[0] for row in rows(retrieval/'checks.csv')},{'final'})
            self.assertEqual({row['case_id'].split('-')[0] for row in rows(evaluation/'dimension_scores.csv')},{'final'})

    def test_s16_separates_retrieval_and_answer_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            one=run(ROOT,18,'config-start.json',str(Path(tmp)/'one')); two=run(ROOT,18,'config-support.json',str(Path(tmp)/'two'))
            a={r['query_id']:r for r in rows(one/'checks.csv')}; b={r['query_id']:r for r in rows(two/'checks.csv')}
            self.assertEqual(a['dev-03']['failure_stage'],'answer')
            self.assertEqual(b['dev-02']['failure_stage'],'retrieval')

    def test_s17_fixed_material_rejects_unknown_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp); cfg=work/'bad.json'; cfg.write_text(json.dumps({'seed':17,'routes':['prompt_revision','unknown']}))
            result=subprocess.run([sys.executable,'lesson-19/analysis.py','--config',str(cfg)],cwd=ROOT,text=True,capture_output=True)
            self.assertNotEqual(result.returncode,0); self.assertIn('固定材料只覆盖',result.stderr+result.stdout)

    def test_s18_order_changes_proxy_not_human_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            ab=run(ROOT,20,'config-start.json',str(Path(tmp)/'ab')); ba=run(ROOT,20,'config-support.json',str(Path(tmp)/'ba'))
            a={(r['case_id'],r['candidate']):r for r in rows(ab/'dimension_scores.csv')}; b={(r['case_id'],r['candidate']):r for r in rows(ba/'dimension_scores.csv')}
            key=('dev-01','A'); self.assertEqual(a[key]['weighted_total'],b[key]['weighted_total']); self.assertNotEqual(a[key]['fixed_proxy_score'],b[key]['fixed_proxy_score'])

    def test_default_outputs_reproduce_in_fresh_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp)/'student'; shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns('.git','.venv','artifacts','__pycache__','.pytest_cache'))
            for lesson in range(15,21):
                folder=work/f'lesson-{lesson:02d}'
                run(work,lesson,'config.json','artifacts')
                task=json.loads((folder/'contract.json').read_text())
                for field in ('question','user','data_source','metric','split_plan','initial_expectation'):task[field]='自动回归测试说明，不是学生作业。'
                (folder/'contract.json').write_text(json.dumps(task,ensure_ascii=False))
                (folder/'report.md').write_text('# 自动回归测试\n只验证文件重建，不评价学习。\n')
                sub=json.loads((folder/'submission.json').read_text()); sub['status']='complete'; (folder/'submission.json').write_text(json.dumps(sub,ensure_ascii=False))
                subprocess.run([sys.executable,'scripts/course.py','check',str(lesson)],cwd=work,check=True,capture_output=True,text=True)
                before={p:(work/p).read_bytes() for p in sub['artifacts']}
                subprocess.run([sys.executable,'scripts/course.py','run',str(lesson)],cwd=work,check=True,capture_output=True,text=True)
                self.assertEqual(before,{p:(work/p).read_bytes() for p in sub['artifacts']})

if __name__=='__main__': unittest.main()

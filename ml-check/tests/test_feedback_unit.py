"""验证27—32候选快照的装载、题目对应、公开接口和前课保留。"""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from app.questions import bank_from_snapshot, bank_snapshot
from app.legacy import response

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'ml-check/deploy/lessons27-32-20261104'
BASE = ROOT / 'ml-check/deploy/lessons21-26-20261103/lessons.json'

class FeedbackUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new=json.loads((RELEASE/'lessons.json').read_text())
        cls.old=json.loads(BASE.read_text())
        cls.changed=[l for l in cls.new['lessons'] if l['lesson_id'] in {f'S{i:02d}' for i in range(25,31)}]

    def test_complete_bank_loads_and_keeps_order(self):
        self.assertEqual([l['lesson_id'] for l in self.new['lessons']], ['C01','C02']+[f'S{i:02d}' for i in range(1,31)])
        for lesson in self.new['lessons']:
            bank_from_snapshot(json.dumps(lesson))
        for before,after in zip(self.old['lessons'][:26],self.new['lessons'][:26]):
            expected=copy.deepcopy(before)
            if before['lesson_id'] in {f'S{i:02d}' for i in range(19,25)}:
                for q in expected['questions']:
                    q['id']=f"{before['lesson_id']}-{q['phase']}-{q['concept_id'].split('-')[-1]}"
                expected.setdefault('durations',{'attempt_a':240,'learn':300,'attempt_b':240})
                expected.setdefault('module','工具与协作系统')
            self.assertEqual(expected,after)

    def test_changed_sources_pairs_and_explanations(self):
        self.assertEqual(len(self.changed),6)
        for l in self.changed:
            self.assertEqual(l,json.loads((RELEASE/'source'/f"{l['lesson_id'].lower()}.json").read_text()))
            bank=bank_from_snapshot(json.dumps(l))
            self.assertEqual(len(bank.questions),10)
            self.assertEqual(sum(bank.durations.values())+120,900)
            for item in bank.items:
                a,b=item['pair']['a'],item['pair']['b']
                self.assertNotEqual(a['prompt'],b['prompt'])
                for q in [a,b]:
                    self.assertEqual(len(set(q['options'])),4)
                    self.assertTrue(all(f'{c}：' in q['explanation'] for c in 'ABCD'))
                    self.assertNotIn(q['prompt'],item['tutor_context'])

    def test_public_payload_excludes_answers_and_old_snapshot_survives(self):
        for lesson in self.changed:
            status,payload=response('/ml-check/api/lessons/'+lesson['lesson_id'],self.new)
            self.assertEqual(status,200)
            for q in payload['questions']:
                self.assertNotIn('answer',q)
                self.assertNotIn('explanation',q)
            old=next(l for l in self.old['lessons'] if l['lesson_id']==lesson['lesson_id'])
            snapshot=bank_snapshot(bank_from_snapshot(json.dumps(old)))
            self.assertEqual(bank_from_snapshot(snapshot).questions,old['questions'])

    def test_manifest_and_numeric_keys(self):
        manifest=json.loads((RELEASE/'manifest.json').read_text())
        self.assertEqual(manifest['version'],self.new['version'])
        for name,sha in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)
        questions={q['id']:q for l in self.changed for q in l['questions']}
        for qid,expected in [('S26-A-03',1.3),('S26-B-03',0),('S29-A-02',0.7),('S30-B-03',0.9)]:
            q=questions[qid]
            self.assertAlmostEqual(float(q['options'][q['answer']]),expected)

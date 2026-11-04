"""全32课新版题库：配对、唯一选项、数值、评分和历史兼容。"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unittest
from app.questions import bank_from_snapshot, bank_snapshot
from app.legacy import response
from app.pages import lesson_page

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'ml-check/deploy/expert-review-20261104'


class ExpertReviewBank(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new = json.loads((RELEASE/'lessons.json').read_text())
        cls.old = json.loads((RELEASE.parent/'lesson16-gpt-20261104/lessons.json').read_text())
        cls.questions = {q['id']:q for l in cls.new['lessons'] for q in l['questions']}

    def answer(self, qid):
        q = self.questions[qid]
        return q['options'][q['answer']]

    def test_32_lessons_320_questions_and_historical_contracts(self):
        self.assertEqual(len(self.new['lessons']),32)
        self.assertEqual(sum(len(l['questions']) for l in self.new['lessons']),320)
        self.assertNotEqual(self.new['version'],self.old['version'])
        for old,new in zip(self.old['lessons'],self.new['lessons']):
            self.assertEqual(old['lesson_id'],new['lesson_id'])
            self.assertEqual(old['durations'],new['durations'])
            self.assertEqual([q['id'] for q in old['questions']],[q['id'] for q in new['questions']])
            self.assertEqual([c['concept_id'] for c in old['concepts']],[c['concept_id'] for c in new['concepts']])
            history = bank_from_snapshot(json.dumps(old))
            self.assertEqual(bank_from_snapshot(bank_snapshot(history)).questions,history.questions)
            bank = bank_from_snapshot(json.dumps(new))
            for item in bank.items:
                self.assertNotEqual(item['pair']['a']['prompt'],item['pair']['b']['prompt'])
                for q in [item['pair']['a'],item['pair']['b']]:
                    self.assertEqual(len(set(q['options'])),4)
                    self.assertTrue(q['explanation'].strip())
                    self.assertNotIn(q['prompt'],item['tutor_context'])
                    self.assertNotIn(q['explanation'],item['tutor_context'])
            for phase in 'AB':
                self.assertEqual(sorted(Counter(q['answer'] for q in bank._by_phase(phase)).values()),[1,1,1,2])

    def test_manifest_and_all_source_lessons(self):
        manifest = json.loads((RELEASE/'manifest.json').read_text())
        for path,digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((RELEASE/path).read_bytes()).hexdigest(),digest)
        for lesson in self.new['lessons']:
            self.assertEqual(lesson,json.loads((RELEASE/'source'/f"{lesson['lesson_id'].lower()}.json").read_text()))

    def test_every_correct_and_wrong_option_is_scored_and_answers_hidden(self):
        for lesson in self.new['lessons']:
            status,public = response('/ml-check/api/lessons/'+lesson['lesson_id'],self.new)
            self.assertEqual(status,200)
            self.assertTrue(all(set(q)=={'id','phase','prompt','options'} for q in public['questions']))
            bank = bank_from_snapshot(json.dumps(lesson))
            for phase in 'AB':
                questions = bank._by_phase(phase)
                answers = {q['id']:q['answer'] for q in questions}
                self.assertIn('这轮判断都与题目依据一致',lesson_page(lesson,phase,answers))
                for q in questions:
                    for option in range(4):
                        if option!=q['answer']:
                            self.assertIn('有 1 道题值得再想一想',lesson_page(lesson,phase,{**answers,q['id']:option}))

    def test_revised_numeric_answers_independently(self):
        self.assertEqual(float(self.answer('C02-A-02')),0.4*20-4)
        self.assertAlmostEqual(float(self.answer('C02-B-02')),0.3*18-2)
        self.assertEqual(float(self.answer('C02-A-03')),((-1)**2+1**2)/2)
        self.assertEqual(self.answer('S04-A-01'),f'{sum([.2,.4,.6])/3:.1f} kg')
        self.assertAlmostEqual(float(self.answer('S04-A-02')),math.sqrt((0**2+2**2)/2),places=3)
        self.assertEqual(self.answer('S04-A-03'),'3/4')
        self.assertEqual(float(self.answer('S04-B-04')),(90*.2+10*.8)/100)
        self.assertEqual(json.loads(self.answer('S07-A-01')),[120/100,4/10])
        self.assertEqual(int(self.answer('S08-A-13')),5*2+3)
        self.assertIn(str(5*2+1),self.answer('S08-B-13'))
        self.assertEqual(float(self.answer('S08-A-14')),1/(1+math.exp(-(2-2))))

    def test_revised_mechanisms(self):
        self.assertIn('需求识别',self.answer('S19-A-05'))
        self.assertIn('查询已执行',self.answer('S20-A-05'))
        self.assertIn('本次检索范围',self.answer('S21-B-02'))
        self.assertIn('已有证据',self.answer('S21-B-05'))
        self.assertIn('外部资料',self.answer('S22-B-01'))
        self.assertIn('重跑下游',self.answer('S23-B-04'))
        self.assertIn('质量未达目标',self.questions['S27-B-05']['explanation'])
        self.assertNotIn('另一个场景的结果',self.questions['S29-A-02']['explanation'])


if __name__=='__main__': unittest.main()

"""Validate the prepared generation unit and historical compatibility."""
import hashlib
import json
from pathlib import Path
import unittest
from app.questions import bank_from_snapshot, bank_snapshot
from app.legacy import response
from app.pages import lesson_page

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'ml-check/deploy/lessons15-20-20261102'


class GenerationUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = json.loads((RELEASE/'archive/production-before.json').read_text())
        cls.new = json.loads((RELEASE/'lessons.json').read_text())
        cls.lessons = cls.new['lessons'][15:20]

    def test_only_five_lessons_change(self):
        self.assertEqual(len(self.new['lessons']), 32)
        self.assertNotEqual(self.new['version'], self.old['version'])
        self.assertEqual([a['lesson_id'] for a,b in zip(self.old['lessons'],self.new['lessons']) if a != b],
                         ['S14','S15','S16','S17','S18'])
        approved = json.loads((ROOT/'ml-check/deploy/lesson15-20261102/source/questions.json').read_text())
        self.assertEqual(self.new['lessons'][14], approved)
        for n, lesson in enumerate(self.lessons,16):
            self.assertEqual(lesson,json.loads((RELEASE/f'source/lesson{n}.json').read_text()))
        for lesson in self.new['lessons']:
            bank_from_snapshot(json.dumps(lesson))

    def test_pairs_explanations_learning(self):
        seen = set()
        for lesson in self.lessons:
            self.assertEqual(len(lesson['concepts']),5)
            self.assertEqual(len(lesson['questions']),10)
            for concept in lesson['concepts']:
                pair = [q for q in lesson['questions'] if q['concept_id']==concept['concept_id']]
                self.assertEqual({q['phase'] for q in pair},{'A','B'})
                self.assertNotEqual(pair[0]['prompt'],pair[1]['prompt'])
            for q in lesson['questions']:
                self.assertNotIn(q['id'],seen)
                seen.add(q['id'])
                self.assertEqual(len(set(q['options'])),4)
                self.assertIn(q['answer'],range(4))
                self.assertTrue(all(c in q['explanation'] for c in 'ABCD'))
                for concept in lesson['concepts']:
                    self.assertNotIn(q['prompt'],concept['tutor_context'])
                    self.assertNotIn(q['explanation'],concept['tutor_context'])
        self.assertEqual(len(seen),50)

    def test_manifest_and_old_snapshots(self):
        manifest=json.loads((RELEASE/'manifest.json').read_text())
        for name, sha in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)
        for old,new in zip(self.old['lessons'][15:20],self.lessons):
            old_bank=bank_from_snapshot(json.dumps(old))
            snapshot=bank_snapshot(old_bank)
            bank_from_snapshot(json.dumps(new))
            self.assertEqual(bank_from_snapshot(snapshot).questions,old_bank.questions)

    def test_public_views_hide_answers(self):
        for lesson in self.lessons:
            status,payload=response('/ml-check/api/lessons/'+lesson['lesson_id'],self.new)
            self.assertEqual(status,200)
            for q in payload['questions']:
                self.assertNotIn('answer',q)
                self.assertNotIn('explanation',q)
            for phase in 'AB':
                page=lesson_page(lesson,phase)
                for q in lesson['questions']:
                    self.assertNotIn(q['explanation'],page)
                    if q['phase']==phase:
                        self.assertIn(q['id'],page)

    def test_each_answer_and_distractor(self):
        for lesson in self.lessons:
            bank=bank_from_snapshot(json.dumps(lesson))
            for phase in 'AB':
                qs=bank._by_phase(phase)
                correct={q['id']:q['answer'] for q in qs}
                self.assertIn('这轮判断都与题目依据一致',lesson_page(lesson,phase,correct))
                for q in qs:
                    for option in range(4):
                        if option != q['answer']:
                            page=lesson_page(lesson,phase,{**correct,q['id']:option})
                            self.assertIn('有 1 道题值得再想一想',page)

    def test_numeric_answers(self):
        self.assertEqual(.25*2+.75*8,6.5)
        self.assertEqual(.5*4+.5*10,7)
        self.assertEqual(.8*4+.2*10,5.2)
        scores={'D1':.18,'D2':.62,'D3':.41}
        self.assertEqual(sorted(scores,key=scores.get,reverse=True)[:2],['D2','D3'])


if __name__ == '__main__':
    unittest.main()

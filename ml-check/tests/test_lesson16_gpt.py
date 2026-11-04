"""第16课新题的数值、历史兼容与作答反馈；在hblu-5090运行。"""
import hashlib
import json
import math
from pathlib import Path
import unittest
from app.questions import bank_from_snapshot, bank_snapshot
from app.legacy import response
from app.pages import lesson_page

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'ml-check/deploy/lesson16-gpt-20261104'


class Lesson16GPT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = json.loads((RELEASE.parent / 'lessons27-32-20261104/lessons.json').read_text())
        cls.new = json.loads((RELEASE / 'lessons.json').read_text())
        cls.lesson = next(item for item in cls.new['lessons'] if item['lesson_id'] == 'S14')

    def test_replaces_only_s14_and_preserves_old_snapshot(self):
        self.assertEqual(len(self.new['lessons']), 32)
        self.assertNotEqual(self.old['version'], self.new['version'])
        self.assertEqual([a['lesson_id'] for a,b in zip(self.old['lessons'], self.new['lessons']) if a != b], ['S14'])
        before = next(item for item in self.old['lessons'] if item['lesson_id'] == 'S14')
        old_bank = bank_from_snapshot(json.dumps(before))
        saved = bank_snapshot(old_bank)
        new_bank = bank_from_snapshot(json.dumps(self.lesson))
        self.assertEqual(bank_from_snapshot(saved).questions, old_bank.questions)
        self.assertEqual([q['id'] for q in new_bank.questions], [q['id'] for q in old_bank.questions])
        self.assertEqual(new_bank.durations, old_bank.durations)

    def test_source_manifest_and_pairs(self):
        self.assertEqual(self.lesson, json.loads((RELEASE / 'source/s14.json').read_text()))
        manifest = json.loads((RELEASE / 'manifest.json').read_text())
        for name, digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)
        for lesson in self.new['lessons']:
            bank_from_snapshot(json.dumps(lesson))
        bank = bank_from_snapshot(json.dumps(self.lesson))
        self.assertEqual(len(bank.items), 5)
        for item in bank.items:
            a, b = item['pair']['a'], item['pair']['b']
            self.assertNotEqual(a['prompt'], b['prompt'])
            for question in [a, b]:
                self.assertEqual(len(set(question['options'])), 4)
                self.assertIn(question['answer'], range(4))
                self.assertTrue(all(f'{letter}：' in question['explanation'] for letter in 'ABCD'))
                self.assertNotIn(question['prompt'], item['tutor_context'])
                self.assertNotIn(question['explanation'], item['tutor_context'])

    def test_public_answers_hidden_and_every_option_graded(self):
        status, public = response('/ml-check/api/lessons/S14', self.new)
        self.assertEqual(status, 200)
        self.assertTrue(all(set(q) == {'id','phase','prompt','options'} for q in public['questions']))
        bank = bank_from_snapshot(json.dumps(self.lesson))
        for phase in 'AB':
            questions = bank._by_phase(phase)
            correct = {q['id']: q['answer'] for q in questions}
            self.assertIn('这轮判断都与题目依据一致', lesson_page(self.lesson, phase, correct))
            for question in questions:
                for option in range(4):
                    if option != question['answer']:
                        self.assertIn('有 1 道题值得再想一想', lesson_page(self.lesson, phase, {**correct, question['id']: option}))

    def test_vector_and_temperature_numbers(self):
        questions = {q['id']: q for q in self.lesson['questions']}
        for name, word, position in [('S14-A-01', [.2,-.4,.7], [.1,0,-.1]), ('S14-B-01', [.4,-.2], [-.1,.3])]:
            question = questions[name]
            answer = json.loads(question['options'][question['answer']])
            self.assertEqual(len(answer), len(word))
            for a,b,c in zip(word, position, answer):
                self.assertAlmostEqual(a+b,c)
        def probabilities(logits, temperature):
            scores = [math.exp(value / temperature) for value in logits]
            return [value / sum(scores) for value in scores]
        self.assertEqual(round(100 * probabilities([0,3,0,0,1,2], 1)[1], 1), 60.5)
        self.assertEqual(round(100 * probabilities([0,3,0,0,1,2], .5)[1], 1), 86.1)
        low, high = probabilities([3,2,0], 1), probabilities([3,2,0], 2)
        self.assertLess(high[0], low[0])
        self.assertTrue(high[1] > low[1] and high[2] > low[2])
        self.assertGreater(high[0], high[1])
        self.assertGreater(high[1], high[2])


if __name__ == '__main__':
    unittest.main()

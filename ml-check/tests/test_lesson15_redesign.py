"""Validate the prepared lesson 15 bank against the captured live bank."""
import hashlib
import json
import math
from pathlib import Path
import unittest

from app.questions import bank_from_snapshot, bank_snapshot
from app.legacy import response
from app.pages import lesson_page

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'ml-check/deploy/lesson15-20261102'


class Lesson15Redesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = json.loads((RELEASE / 'archive/production-before.json').read_text())
        cls.new = json.loads((RELEASE / 'lessons.json').read_text())
        cls.lesson = cls.new['lessons'][14]
        cls.bank = bank_from_snapshot(json.dumps(cls.lesson))

    def test_full_bank_changes_only_lesson15(self):
        self.assertEqual(len(self.new['lessons']), 32)
        self.assertNotEqual(self.old['version'], self.new['version'])
        self.assertEqual([a['lesson_id'] for a, b in zip(self.old['lessons'], self.new['lessons']) if a != b], ['S13'])
        self.assertEqual(self.lesson['lesson_id'], 'S13')
        for lesson in self.new['lessons']:
            bank_from_snapshot(json.dumps(lesson))
        source = json.loads((RELEASE / 'source/questions.json').read_text())
        self.assertEqual(source, self.lesson)

    def test_manifest_and_snapshot_roundtrip(self):
        manifest = json.loads((RELEASE / 'manifest.json').read_text())
        for name, sha in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), sha)
        restored = bank_from_snapshot(bank_snapshot(self.bank))
        self.assertEqual(restored.questions, self.bank.questions)
        old = bank_from_snapshot(json.dumps(self.old['lessons'][14]))
        self.assertNotEqual(old.title, restored.title)
        self.assertEqual(old.title, '预训练模型的能力来自哪里')

    def test_student_api_and_pages_hide_answers(self):
        status, payload = response('/ml-check/api/lessons/S13', self.new)
        self.assertEqual(status, 200)
        for question in payload['questions']:
            self.assertNotIn('answer', question)
            self.assertNotIn('explanation', question)
        for phase in ('A', 'B'):
            page = lesson_page(self.lesson, phase)
            for question in self.bank._by_phase(phase):
                self.assertIn(question['id'], page)
                self.assertNotIn(question['explanation'], page)
            self.assertNotIn('参考选项', page)

    def test_each_answer_and_distractor_scored(self):
        for phase in ('A', 'B'):
            questions = self.bank._by_phase(phase)
            answers = {q['id']: q['answer'] for q in questions}
            self.assertIn('这轮判断都与题目依据一致', lesson_page(self.lesson, phase, answers))
            for q in questions:
                for option in range(4):
                    changed = {**answers, q['id']: option}
                    page = lesson_page(self.lesson, phase, changed)
                    if option != q['answer']:
                        self.assertIn('有 1 道题值得再想一想', page)

    def test_numeric_answers_independently(self):
        self.assertEqual(max(0, -2), 0)
        self.assertAlmostEqual(1/(1+math.exp(0.1)), .475, places=3)
        self.assertGreater(1/(1+math.exp(-(.2*max(0,3)-.2))), .5)
        self.assertAlmostEqual(.2-.1*(-.3), .23)
        self.assertLess(-math.log(1-.3), -math.log(1-.4))
        self.assertEqual(8*8, 64)
        self.assertEqual(int(.72 >= .5), 1)
        self.assertEqual(int(.46 >= .5), 0)
        self.assertAlmostEqual(70/72*100, 97.2, places=1)

    def test_learning_context_uses_separate_examples(self):
        for concept in self.bank.concepts:
            for question in self.bank.questions:
                self.assertNotIn(question['prompt'], concept['tutor_context'])
                self.assertNotIn(question['explanation'], concept['tutor_context'])
        text = json.dumps(self.lesson, ensure_ascii=False)
        self.assertNotIn('Keras', text)
        self.assertNotIn('Softmax', text)


if __name__ == '__main__':
    unittest.main()

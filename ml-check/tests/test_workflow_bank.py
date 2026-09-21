"""S19–S24 新模块题目与在线学习页的数据边界。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class WorkflowQuestionBank(unittest.TestCase):
    def test_each_lesson_has_five_paired_concepts(self):
        for number in range(19, 25):
            lesson = f"S{number:02d}"
            bank = json.loads(
                (ROOT / f"course-instructor/lessons/{lesson}/questions.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(bank["concepts"]), 5)
            self.assertEqual(len(bank["questions"]), 10)
            by_pair = {}
            for question in bank["questions"]:
                by_pair.setdefault(question["concept_id"], {})[question["phase"]] = question
            self.assertEqual(set(by_pair), {f"{lesson}-{i:02d}" for i in range(1, 6)})
            for pair in by_pair.values():
                self.assertEqual(set(pair), {"A", "B"})
                self.assertNotEqual(pair["A"]["prompt"], pair["B"]["prompt"])

    def test_learning_context_contains_no_question_or_answer_fields(self):
        for number in range(19, 25):
            lesson = f"S{number:02d}"
            bank = json.loads(
                (ROOT / f"course-instructor/lessons/{lesson}/questions.json").read_text(
                    encoding="utf-8"
                )
            )
            for concept in bank["concepts"]:
                self.assertEqual(set(concept), {"concept_id", "title", "tutor_context"})
                self.assertNotIn("哪项", concept["tutor_context"])


if __name__ == "__main__":
    unittest.main()

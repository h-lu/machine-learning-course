"""S25–S30 概念题与学生实验的关键边界。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class OperationsQuestionBankTests(unittest.TestCase):
    def source(self, lesson: str) -> dict:
        return json.loads(
            (ROOT / f"course-instructor/lessons/{lesson}/questions.json").read_text(encoding="utf-8")
        )

    def test_each_lesson_has_five_ab_pairs_and_reviewed_timing(self):
        for number in range(25, 31):
            lesson = f"S{number:02d}"
            bank = self.source(lesson)
            self.assertEqual(bank["durations"], {"attempt_a": 240, "learn": 300, "attempt_b": 240})
            concepts = [item["concept_id"] for item in bank["concepts"]]
            self.assertEqual(concepts, [f"{lesson}-{index:02d}" for index in range(1, 6)])
            pairs = {concept: set() for concept in concepts}
            for question in bank["questions"]:
                pairs[question["concept_id"]].add(question["phase"])
                self.assertEqual(len(question["options"]), 4)
                self.assertIn(question["answer"], range(4))
                self.assertTrue(question["explanation"].strip())
            self.assertTrue(all(phases == {"A", "B"} for phases in pairs.values()))

    def test_study_context_does_not_reveal_s30_final_results(self):
        bank = self.source("S30")
        study = "\n".join(item["tutor_context"] for item in bank["concepts"])
        for leaked in ("5/8", "8/8", "D01", "D02", "D06"):
            self.assertNotIn(leaked, study)

    def test_s28_and_s29_questions_stay_within_taught_relationships(self):
        s28 = self.source("S28")
        contexts = "\n".join(item["tutor_context"] for item in s28["concepts"])
        self.assertIn("平均每条请求延迟", contexts)
        s29_b04 = next(item for item in self.source("S29")["questions"] if item["id"] == "S29-B-04")
        self.assertIn("关键条件", s29_b04["explanation"])
        self.assertNotIn("受保护群体", json.dumps(s29_b04, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()

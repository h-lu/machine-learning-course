import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from app.main import ReceiptStore, load_bank, make_handler, response
from app.questions import CURRENT_BANKS
from ml_check.checker import LESSONS, Report, check_question_set
from pathlib import Path


class Questions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = load_bank()

    def test_all_32_lessons_have_ten_valid_questions(self):
        self.assertEqual([x["lesson_id"] for x in self.bank["lessons"]], LESSONS)
        for lesson in self.bank["lessons"]:
            report = Report(Path.cwd(), "instructor")
            check_question_set(lesson, Path(lesson["lesson_id"]), report, lesson["lesson_id"])
            self.assertFalse(report.failed(), report.issues)

    def test_no_duplicate_question_prompts_across_lessons(self):
        prompts = [q["prompt"] for lesson in self.bank["lessons"] for q in lesson["questions"]]
        self.assertEqual(len(prompts), len(set(prompts)))

    def test_every_lesson_defines_five_named_concepts_and_ab_pairs(self):
        self.assertEqual(len(CURRENT_BANKS), 32)
        for bank in CURRENT_BANKS:
            self.assertEqual(len(bank.items), 5)
            self.assertEqual(
                bank.concept_ids,
                [f"{bank.lesson_id}-{index:02d}" for index in range(1, 6)],
            )
            for item in bank.items:
                self.assertFalse(item["title"].startswith(("概念", "知识点")))
                self.assertEqual(set(item["pair"]), {"a", "b"})
                self.assertNotEqual(item["tutor_context"], item["pair"]["a"]["prompt"])
                self.assertNotIn(item["pair"]["a"]["prompt"], item["tutor_context"])
                for phase in ("a", "b"):
                    self.assertEqual(
                        item["pair"][phase]["concept_id"], item["concept_id"]
                    )

    def test_ai_learning_template_never_renders_ab_question_text(self):
        template = (Path(__file__).parents[1] / "app/templates/learn.html").read_text(encoding="utf-8")
        self.assertNotIn("pair.a", template)
        self.assertNotIn("pair.b", template)
        self.assertNotIn("A 版问题", template)
        self.assertIn("item.title", template)
        self.assertIn("item.tutor_context", template)

    def test_question_get_does_not_publish_teacher_answers(self):
        for lesson in LESSONS:
            status, payload = response(f"/ml-check/api/lessons/{lesson}", self.bank)
            self.assertEqual(status, 200)
            for question in payload["questions"]:
                self.assertEqual(set(question), {"id", "phase", "prompt", "options"})

    def test_unknown_routes_and_lesson_return_404(self):
        for path in ["/ml-check/api/lessons/S31", "/ml-check/api/lessons/C01/answers", "/etc/passwd"]:
            self.assertEqual(response(path, self.bank)[0], 404)

    def test_legacy_paths_and_case_insensitive_ids(self):
        self.assertEqual(response("/ml-check/healthz", self.bank)[1]["lesson_count"], 32)
        self.assertEqual(len(response("/ml-check/api/lessons", self.bank)[1]), 32)
        self.assertEqual(response("/ml-check/api/lessons/s01", self.bank)[1]["lesson_id"], "S01")

    def test_actual_http_read(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.bank))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/ml-check/api/lessons/S23", timeout=5) as r:
                payload = json.load(r)
                self.assertEqual(r.status, 200)
                self.assertEqual(payload["lesson_id"], "S23")
                self.assertNotIn("answer", payload["questions"][0])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_receipt_store_keeps_metadata_without_answers(self):
        lesson = self.bank["lessons"][0]
        questions = [q for q in lesson["questions"] if q["phase"] == "A"]
        store = ReceiptStore(":memory:")
        receipt = store.add(lesson["lesson_id"], "A", {q["id"]: 0 for q in questions}, questions)
        fetched = store.get(receipt["receipt_id"])
        self.assertEqual(fetched["lesson_id"], lesson["lesson_id"])
        self.assertEqual(fetched["total"], 5)
        self.assertNotIn("answers", fetched)

    def test_receipt_api_returns_404_for_unknown_id(self):
        status, payload = response("/ml-check/api/receipts/does-not-exist", self.bank, ReceiptStore(":memory:"))
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()

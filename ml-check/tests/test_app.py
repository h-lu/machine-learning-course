import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from app.main import load_bank, make_handler, response
from ml_check.checker import LESSONS, Report, check_question_set
from pathlib import Path


class Questions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = load_bank()

    def test_all_32_lessons_have_four_valid_questions(self):
        self.assertEqual([x["lesson_id"] for x in self.bank["lessons"]], LESSONS)
        for lesson in self.bank["lessons"]:
            report = Report(Path.cwd(), "instructor")
            check_question_set(lesson, Path(lesson["lesson_id"]), report, lesson["lesson_id"])
            self.assertFalse(report.failed(), report.issues)

    def test_no_duplicate_question_prompts_across_lessons(self):
        prompts = [q["prompt"] for lesson in self.bank["lessons"] for q in lesson["questions"]]
        self.assertEqual(len(prompts), len(set(prompts)))

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


if __name__ == "__main__":
    unittest.main()

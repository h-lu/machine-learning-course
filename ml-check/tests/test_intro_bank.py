"""新 C01–C02 的题库同步、计时和公开读取边界。"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from app import db
from app.config import Settings
from app.main import create_app
from app.legacy import load_bank
from app.questions import BANK_VERSION, CURRENT_BANKS, LessonBank

ROOT = Path(__file__).resolve().parents[2]


class IntroBank(unittest.TestCase):
    def test_both_loaders_use_the_same_bank_and_version(self):
        raw = load_bank()
        self.assertEqual(raw["version"], BANK_VERSION)
        self.assertEqual(BANK_VERSION, "ml-v11-s02-review-2026-09-20")
        for bank, source in zip(CURRENT_BANKS, raw["lessons"]):
            self.assertEqual(bank.lesson_id, source["lesson_id"])
            self.assertEqual(bank.questions, source["questions"])
            self.assertEqual(bank.concepts, source["concepts"])

    def test_intro_questions_match_teacher_source_when_full_workspace_is_present(self):
        if not (ROOT / "course-instructor").exists():
            self.skipTest("教师源文件不在独立 ml-check 发布包内")
        for bank in CURRENT_BANKS[:2]:
            source = json.loads((ROOT/f"course-instructor/lessons/{bank.lesson_id}/questions.json").read_text())
            self.assertEqual(bank.title, source["title"])
            self.assertEqual(bank.concepts, source["concepts"])
            self.assertEqual(bank.questions, source["questions"])
            self.assertEqual(len(bank.items), 5)
            for item in bank.items:
                self.assertEqual(set(item["pair"]), {"a", "b"})
                self.assertNotEqual(item["pair"]["a"]["prompt"], item["pair"]["b"]["prompt"])
                for phase in ("a", "b"):
                    self.assertNotIn(item["pair"][phase]["prompt"], item["tutor_context"])

    def test_first_eight_phases_fit_fifteen_minutes_and_other_lessons_keep_durations(self):
        for bank in CURRENT_BANKS[:8]:
            self.assertEqual(bank.durations, {"attempt_a": 240, "learn": 300, "attempt_b": 240})
            self.assertEqual(sum(bank.durations.values()) + 120, 900)
        for bank in CURRENT_BANKS[8:]:
            self.assertEqual(bank.durations, {"attempt_a": 600, "learn": 900, "attempt_b": 600})

    def test_invalid_phase_duration_is_rejected(self):
        bank = CURRENT_BANKS[0]
        for bad in (0, -1, True, "240", 4000):
            values = copy.deepcopy(bank.__dict__); values["durations"]["attempt_a"] = bad
            with self.assertRaises(ValueError): LessonBank(**values)

    def test_phase_timing_uses_aware_utc_on_supported_python_versions(self):
        self.assertEqual(db.utc_now().tzinfo, timezone.utc)
        self.assertEqual(datetime.fromisoformat(db.iso_now()).utcoffset(), timedelta(0))
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / "time.sqlite3")
            db.initialize(path, "C01", "入门检查")
            session = db.current_session(path)
            db.set_phase(path, session["id"], "a", CURRENT_BANKS[0].durations["attempt_a"])
            updated = db.get_session(path, session["id"])
            started = datetime.fromisoformat(updated["phase_started_at"])
            ended = datetime.fromisoformat(updated["phase_ends_at"])
            self.assertEqual(started.utcoffset(), timedelta(0))
            self.assertEqual(ended - started, timedelta(seconds=240))

    def test_fastapi_health_and_public_intro_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = Settings(database_path=str(Path(temp)/"test.sqlite3"), session_secret="local-test-only",
                                gitea_base_url="https://example.invalid", gitea_client_id="", gitea_client_secret="",
                                public_base_url="http://testserver/ml-check", teacher_logins=frozenset(),
                                secure_cookie=False, testing=True)
            with TestClient(create_app(settings)) as client:
                health = client.get("/ml-check/healthz")
                self.assertEqual(health.status_code, 200)
                self.assertEqual(health.json()["bank_version"], BANK_VERSION)
                for lesson in ("C01", "C02"):
                    result = client.get(f"/ml-check/api/lessons/{lesson}")
                    self.assertEqual(result.status_code, 200)
                    self.assertEqual(len(result.json()["questions"]), 10)
                    for question in result.json()["questions"]:
                        self.assertEqual(set(question), {"id", "phase", "prompt", "options"})


if __name__ == "__main__":
    unittest.main()

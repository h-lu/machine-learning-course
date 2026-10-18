"""Lesson10 publication checks use only synthetic, temporary classroom data."""
import hashlib
import html
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import db, main
from app.config import Settings
from app.questions import LessonBank, bank_from_snapshot, bank_for_lesson, bank_snapshot
from ml_check.checker import Report, active_ids, check_question_set, check_repo, formal_question_numbers


ROOT = Path(__file__).resolve().parents[2]
INSTRUCTOR = ROOT / "course-instructor"
BANKS = ROOT / "ml-check/deploy/banks"
SOURCE = INSTRUCTOR / "lessons/S08/questions.draft-20261013.json"
FORMAL = SOURCE.with_name("questions.json")
VERSION = "ml-lesson10-sms-20261013-v1"
SOURCE_SHA = "757213629c4e8fc42b91a9159586edc234a717579f1f7063978dd19dfb4a0fc6"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def as_bank(raw):
    return bank_from_snapshot(json.dumps(raw, ensure_ascii=False))


def csrf(text):
    return html.unescape(re.search(r'name="csrf_token" value="([^"]+)"', text).group(1))


def make_test_settings(database):
    return Settings(
        database_path=str(database), session_secret="synthetic-lesson10-tests-only",
        gitea_base_url="https://example.invalid", gitea_client_id="",
        gitea_client_secret="", public_base_url="http://testserver/ml-check",
        teacher_logins=frozenset(), secure_cookie=False, testing=True,
    )


class Lesson10Publication(unittest.TestCase):
    def test_formal_content_preserves_the_approved_draft_and_ids(self):
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), SOURCE_SHA)
        self.assertEqual(FORMAL.read_bytes(), SOURCE.read_bytes())
        source = read(SOURCE)
        bank = bank_for_lesson("S08")
        self.assertEqual(source["content_version"], "sms-20261013-S08-draft-v1")
        for field in ("questions", "concepts", "durations", "title"):
            self.assertEqual(getattr(bank, field), source[field])
        self.assertEqual(bank.concept_ids, [f"S08-{n}" for n in range(11, 16)])
        self.assertEqual([q["answer"] for q in bank._by_phase("A")], [1, 0, 1, 3, 3])
        self.assertEqual([q["answer"] for q in bank._by_phase("B")], [2, 3, 2, 0, 1])

    def test_registered_formal_numbers_are_scoped_and_legacy_default_remains(self):
        active = active_ids(INSTRUCTOR, "instructor")
        self.assertIn("S08", active)
        self.assertNotIn("S08", read(INSTRUCTOR / "active_lessons.json")["offline_instructor_lessons"])
        numbers = formal_question_numbers(INSTRUCTOR, active)
        self.assertEqual(numbers, {"S08": [11, 12, 13, 14, 15], "S09": [21, 22, 23, 24, 25]})
        report = Report(INSTRUCTOR, "instructor")
        check_question_set(read(FORMAL), FORMAL, report, "S08", numbers["S08"])
        self.assertFalse(report.failed(True), report.issues)
        legacy = Report(INSTRUCTOR, "instructor")
        check_question_set(read(FORMAL), FORMAL, legacy, "S08")
        self.assertTrue(legacy.failed())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for metadata in ({"S07": [11, 12, 13, 14, 15]}, {"S08": [1, 2, 3, 4, 5]}, {"S08": [11, 12, 13, 14, True]}):
                (root / "active_lessons.json").write_text(json.dumps({"formal_question_numbers": metadata}))
                with self.assertRaises(ValueError):
                    formal_question_numbers(root, active)

    def test_complete_instructor_structure_accepts_the_published_lesson(self):
        report = check_repo(INSTRUCTOR, "instructor")
        self.assertFalse(report.failed(True), report.issues)

    def test_deployment_bank_changes_only_S08_and_preserves_immutable_archive(self):
        old_path = BANKS / "archive/ml-v20-reviewed-01-09-2026-10-12.lessons.json"
        self.assertEqual(hashlib.sha256(old_path.read_bytes()).hexdigest(), "d8b6d197cf8a0bdfe92bea246e9e220db3bd47c7b8d921b61ac08de91d98f3aa")
        old = read(old_path)
        current = read(BANKS / "lessons-lesson10-20261013.json")
        self.assertEqual(current["version"], VERSION)
        self.assertEqual(len(current["lessons"]), 32)
        self.assertEqual([x["lesson_id"] for x in current["lessons"]], [x["lesson_id"] for x in old["lessons"]])
        differences = [a["lesson_id"] for a, b in zip(old["lessons"], current["lessons"]) if a != b]
        self.assertEqual(differences, ["S08"])
        old_S08 = next(x for x in old["lessons"] if x["lesson_id"] == "S08")
        self.assertEqual(read(BANKS / "archive/ml-v20-reviewed-01-09-2026-10-12.S08.json"), old_S08)
        new_S08 = next(x for x in current["lessons"] if x["lesson_id"] == "S08")
        self.assertEqual(new_S08, {**read(SOURCE), "module": old_S08["module"]})
        for lesson in current["lessons"]:
            self.assertIsInstance(as_bank(lesson), LessonBank)
        manifest = read(BANKS / "lesson10-release-manifest.json")
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((BANKS / name).read_bytes()).hexdigest(), digest)

    def test_synthetic_teacher_and_student_A_learning_B_flow_uses_new_bank(self):
        release = read(BANKS / "lessons-lesson10-20261013.json")
        loaded = [as_bank(item) for item in release["lessons"]]
        lookup = {bank.lesson_id: bank for bank in loaded}
        source = read(SOURCE)
        with tempfile.TemporaryDirectory() as folder, patch.multiple(
            main, CURRENT_BANKS=loaded, DEFAULT_BANK=loaded[0],
            BANK_VERSION=VERSION, bank_for_lesson=lambda key: lookup[str(key).upper()],
        ):
            database = Path(folder) / "synthetic.sqlite3"
            app = main.create_app(make_test_settings(database))
            old = read(BANKS / "archive/ml-v20-reviewed-01-09-2026-10-12.S08.json")
            historical = db.create_session(str(database), "S08", old["title"], "ml-v20-reviewed-01-09-2026-10-12", bank_snapshot(as_bank(old)))
            old_student = db.upsert_user(str(database), gitea_id=800001, login="synthetic-old", display_name="synthetic-old", role="student")
            db.save_response(str(database), session_id=historical["id"], user_id=old_student["id"], concept_id=old["concepts"][0]["concept_id"], phase="a", option_id="0", confidence="sure", correct=False)
            frozen_session = dict(db.get_session(str(database), historical["id"]))
            frozen_answers = [dict(row) for row in db.responses_for_user(str(database), historical["id"], old_student["id"])]
            with TestClient(app) as teacher, TestClient(app) as student, TestClient(app) as wrong:
                teacher.get("/ml-check/test-login?login=synthetic-l10-teacher&role=teacher")
                page = teacher.get("/ml-check/teacher")
                self.assertIn("第 10 课（S08） · " + source["title"], html.unescape(page.text))
                self.assertEqual(teacher.post("/ml-check/teacher/session", data={"csrf_token": csrf(page.text), "lesson_id": "S08"}, follow_redirects=False).status_code, 303)
                session = db.current_session(str(database))
                self.assertEqual(session["phase"], "closed")
                self.assertEqual(session["bank_version"], VERSION)
                bank = bank_from_snapshot(session["bank_json"])
                self.assertEqual(bank.questions, source["questions"])
                student.get("/ml-check/test-login?login=synthetic-l10-all-correct&role=student")
                wrong.get("/ml-check/test-login?login=synthetic-l10-wrong&role=student")
                public = student.get("/ml-check/api/lessons/S08").json()
                for row in public["questions"]:
                    self.assertEqual(set(row), {"id", "phase", "prompt", "options"})
                self.assertEqual(student.get("/ml-check/healthz").json(), {"status": "ok", "lesson_count": 32, "bank_version": VERSION})

                def phase(value):
                    controls = teacher.get("/ml-check/teacher")
                    changed = teacher.post("/ml-check/teacher/phase", data={"csrf_token": csrf(controls.text), "session_id": session["id"], "phase": value}, follow_redirects=False)
                    self.assertEqual(changed.status_code, 303)

                def submit(client, question, choice=None, submitted_phase=None):
                    attempt = client.get("/ml-check/current")
                    data = {"csrf_token": csrf(attempt.text), "session_id": session["id"], "concept_id": question["concept_id"], "phase": submitted_phase or question["phase"].lower(), "option_id": str(question["answer"] if choice is None else choice), "confidence": "sure"}
                    return client.post("/ml-check/answer", data=data, follow_redirects=False)

                for round_name in ("a", "b"):
                    phase(round_name)
                    for index, q in enumerate(bank._by_phase(round_name)):
                        attempt = student.get("/ml-check/current")
                        visible = html.unescape(attempt.text)
                        self.assertIn(q["id"], visible)
                        self.assertIn(q["prompt"], visible)
                        for option in q["options"]:
                            self.assertIn(option, visible)
                        for secret in source["questions"]:
                            self.assertNotIn(secret["explanation"], visible)
                        self.assertNotIn('name="answer"', visible)
                        if index == 0:
                            self.assertEqual(submit(student, q, submitted_phase="b" if round_name == "a" else "a").status_code, 409)
                        self.assertEqual(submit(student, q).status_code, 303)
                        self.assertEqual(submit(student, q).status_code, 409)
                        if index == 0:
                            self.assertEqual(submit(wrong, q, choice=(q["answer"] + 1) % 4).status_code, 303)
                    if round_name == "a":
                        phase("learn")
                        learning = student.get("/ml-check/current")
                        for q in source["questions"]:
                            self.assertNotIn(q["prompt"], html.unescape(learning.text))
                        self.assertEqual(student.post("/ml-check/learn/complete", data={"csrf_token": csrf(learning.text), "session_id": session["id"]}, follow_redirects=False).status_code, 303)
                phase("result")
                feedback = html.unescape(student.get("/ml-check/current").text)
                for q in source["questions"]:
                    self.assertIn(q["prompt"], feedback)
                    self.assertIn(q["explanation"], feedback)
                rows = {row["login"]: dict(row) for row in db.export_rows(str(database), session["id"])}
                correct = rows["synthetic-l10-all-correct"]
                self.assertEqual((correct["a_count"], correct["a_correct"], correct["learned"], correct["b_count"], correct["b_correct"]), (5, 5, 1, 5, 5))
                incorrect = rows["synthetic-l10-wrong"]
                self.assertEqual((incorrect["a_count"], incorrect["a_correct"], incorrect["b_count"], incorrect["b_correct"]), (1, 0, 1, 0))
                self.assertEqual(dict(db.get_session(str(database), historical["id"])), frozen_session)
                self.assertEqual([dict(row) for row in db.responses_for_user(str(database), historical["id"], old_student["id"])], frozen_answers)
                history = teacher.get(f"/ml-check/teacher?session_id={historical['id']}")
                self.assertIn(old["title"], html.unescape(history.text))
                self.assertEqual(db.missing_snapshot_count(str(database)), 0)


if __name__ == "__main__":
    unittest.main()

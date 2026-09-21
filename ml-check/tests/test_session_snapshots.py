import json
import html
import re
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from app import db
from app.config import Settings
from app.main import create_app
from app.questions import (
    BANK_VERSION,
    DEFAULT_BANK,
    bank_from_snapshot,
    bank_for_lesson,
    bank_snapshot,
)


def settings_for(database: str) -> Settings:
    return Settings(
        database_path=database,
        session_secret="snapshot-tests-only",
        gitea_base_url="https://example.invalid",
        gitea_client_id="",
        gitea_client_secret="",
        public_base_url="http://testserver/ml-check",
        teacher_logins=frozenset(),
        secure_cookie=False,
        testing=True,
    )


def csrf(text: str) -> str:
    return html.unescape(
        re.search(r'name="csrf_token" value="([^"]+)"', text).group(1)
    )
from app.main import lesson_display_label


class SessionSnapshots(unittest.TestCase):
    def test_display_label_includes_human_class_number(self):
        self.assertEqual(lesson_display_label("C01"), "第 01 课（C01）")
        self.assertEqual(lesson_display_label("S01"), "第 03 课（S01）")
        self.assertEqual(lesson_display_label("S30"), "第 32 课（S30）")

    def test_new_sessions_keep_the_exact_lesson_bank(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "ml-check.sqlite3")
            snapshot = bank_snapshot(DEFAULT_BANK)
            db.initialize(
                database,
                DEFAULT_BANK.lesson_id,
                DEFAULT_BANK.title,
                BANK_VERSION,
                snapshot,
            )
            first = db.current_session(database)
            self.assertEqual(first["bank_version"], BANK_VERSION)
            self.assertEqual(first["bank_json"], snapshot)

            restored = bank_from_snapshot(first["bank_json"])
            self.assertEqual(restored.lesson_id, DEFAULT_BANK.lesson_id)
            self.assertEqual(restored.questions, DEFAULT_BANK.questions)

            altered = json.loads(snapshot)
            altered["title"] = "历史场次标题"
            altered["questions"][0]["prompt"] = "历史场次当时显示的题干。"
            historical = json.dumps(altered, ensure_ascii=False)
            row = db.create_session(
                database,
                altered["lesson_id"],
                altered["title"],
                "historical-bank",
                historical,
            )
            restored = bank_from_snapshot(row["bank_json"])
            self.assertEqual(restored.title, "历史场次标题")
            self.assertEqual(restored.questions[0]["prompt"], "历史场次当时显示的题干。")

    def test_initialize_migrates_legacy_session_table_without_deleting_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "legacy.sqlite3")
            connection = sqlite3.connect(database)
            connection.execute(
                """
                CREATE TABLE course_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    phase_started_at TEXT,
                    phase_ends_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    gitea_id INTEGER NOT NULL UNIQUE,
                    login TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    last_login_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE responses (
                    id INTEGER PRIMARY KEY,
                    session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    concept_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    option_id TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    correct INTEGER NOT NULL,
                    submitted_at TEXT NOT NULL,
                    UNIQUE(session_id,user_id,concept_id,phase)
                )
                """
            )
            connection.execute(
                "INSERT INTO course_sessions (lesson_id,title,phase,created_at) VALUES ('S02','旧课','result','2026-09-21T00:00:00+00:00')"
            )
            connection.execute(
                "INSERT INTO users VALUES (3,3003,'legacy-student','旧学生','student','2026-09-21')"
            )
            connection.execute(
                "INSERT INTO responses VALUES (7,1,3,'S02-01','a','2','sure',1,'2026-09-21')"
            )
            connection.commit()
            connection.close()

            db.initialize(
                database,
                DEFAULT_BANK.lesson_id,
                DEFAULT_BANK.title,
                BANK_VERSION,
                bank_snapshot(DEFAULT_BANK),
            )
            row = db.current_session(database)
            self.assertEqual(row["lesson_id"], "S02")
            self.assertIsNone(row["bank_version"])
            self.assertIsNone(row["bank_json"])
            with db.connect(database) as migrated:
                columns = {item["name"] for item in migrated.execute("PRAGMA table_info(course_sessions)")}
                answer = migrated.execute(
                    "SELECT session_id,user_id,concept_id,option_id,correct FROM responses WHERE id=7"
                ).fetchone()
            self.assertIn("bank_version", columns)
            self.assertIn("bank_json", columns)
            self.assertEqual(tuple(answer), (1, 3, "S02-01", "2", 1))

    def test_two_workers_can_migrate_the_same_legacy_database(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "workers.sqlite3")
            connection = sqlite3.connect(database)
            connection.execute(
                """
                CREATE TABLE course_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    phase_started_at TEXT,
                    phase_ends_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT INTO course_sessions (lesson_id,title,phase,created_at) VALUES ('S02','旧课','result','2026-09-21')"
            )
            connection.commit()
            connection.close()

            def migrate():
                db.initialize(
                    database,
                    DEFAULT_BANK.lesson_id,
                    DEFAULT_BANK.title,
                    BANK_VERSION,
                    bank_snapshot(DEFAULT_BANK),
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(migrate) for _ in range(2)]
                for future in futures:
                    future.result()
            with db.connect(database) as migrated:
                columns = {
                    item["name"]
                    for item in migrated.execute("PRAGMA table_info(course_sessions)")
                }
                count = migrated.execute("SELECT COUNT(*) FROM course_sessions").fetchone()[0]
            self.assertIn("bank_version", columns)
            self.assertIn("bank_json", columns)
            self.assertEqual(count, 1)

    def test_database_rejects_half_a_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "pair.sqlite3")
            with self.assertRaisesRegex(ValueError, "bank_json must be non-empty"):
                db.initialize(database, "C01", "错误起点", BANK_VERSION, None)
            snapshot = bank_snapshot(DEFAULT_BANK)
            db.initialize(
                database, "C01", "有快照的单元测试起点", BANK_VERSION, snapshot
            )
            with self.assertRaisesRegex(ValueError, "bank_version must be non-empty"):
                db.create_session(database, "C01", "错误场次", None, "{}")
            with self.assertRaisesRegex(ValueError, "valid lesson snapshot"):
                db.create_session(database, "C01", "损坏快照", BANK_VERSION, "{}")
            with self.assertRaisesRegex(ValueError, "must match"):
                db.create_session(
                    database,
                    "S02",
                    "课号不符",
                    BANK_VERSION,
                    bank_snapshot(DEFAULT_BANK),
                )

    def test_snapshot_parser_rejects_broken_content_and_keeps_legacy_timing(self):
        raw = json.loads(bank_snapshot(DEFAULT_BANK))
        raw["questions"][0]["options"] = ["只有一项"]
        with self.assertRaisesRegex(ValueError, "four distinct options"):
            bank_from_snapshot(json.dumps(raw, ensure_ascii=False))

        raw = json.loads(bank_snapshot(DEFAULT_BANK))
        raw["questions"][0].pop("explanation")
        with self.assertRaisesRegex(ValueError, "explanation"):
            bank_from_snapshot(json.dumps(raw, ensure_ascii=False))

        raw = json.loads(bank_snapshot(DEFAULT_BANK))
        raw.pop("durations")
        restored = bank_from_snapshot(json.dumps(raw, ensure_ascii=False))
        self.assertEqual(
            restored.durations,
            {"attempt_a": 600, "learn": 900, "attempt_b": 600},
        )

    def test_teacher_created_session_saves_the_current_bank(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "route.sqlite3")
            with TestClient(create_app(settings_for(database))) as client:
                client.get("/ml-check/test-login?login=snapshot-teacher&role=teacher")
                page = client.get("/ml-check/teacher")
                result = client.post(
                    "/ml-check/teacher/session",
                    data={
                        "csrf_token": csrf(page.text),
                        "lesson_id": "S07",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(result.status_code, 303)
            session = db.current_session(database)
            expected = bank_for_lesson("S07")
            self.assertEqual(session["bank_version"], BANK_VERSION)
            self.assertEqual(session["bank_json"], bank_snapshot(expected))
            restored = bank_from_snapshot(session["bank_json"])
            self.assertEqual(restored.lesson_id, "S07")
            self.assertEqual(restored.questions, expected.questions)

    def test_result_and_timer_use_the_saved_bank_instead_of_current_globals(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "frozen.sqlite3")
            app = create_app(settings_for(database))
            raw = json.loads(bank_snapshot(DEFAULT_BANK))
            raw["questions"][0]["prompt"] = "历史 A 题干，只应出现在这个场次。"
            raw["questions"][1]["prompt"] = "历史 B 题干，只应出现在这个场次。"
            raw["questions"][1]["explanation"] = "历史 B 解析已经固定。"
            raw["durations"] = {"attempt_a": 7, "learn": 8, "attempt_b": 9}
            snapshot = json.dumps(raw, ensure_ascii=False)
            session = db.create_session(
                database,
                DEFAULT_BANK.lesson_id,
                "历史场次",
                "old-frozen-bank",
                snapshot,
            )
            with TestClient(app) as client:
                client.get("/ml-check/test-login?login=snapshot-student&role=student")
                db.set_phase(database, int(session["id"]), "result", None)
                page = client.get("/ml-check/current")
                self.assertEqual(page.status_code, 200)
                visible = html.unescape(page.text)
                self.assertIn("历史 A 题干，只应出现在这个场次。", visible)
                self.assertIn("历史 B 解析已经固定。", visible)
                self.assertNotIn(DEFAULT_BANK.questions[0]["prompt"], visible)

                client.get("/ml-check/test-login?login=snapshot-teacher&role=teacher")
                teacher = client.get("/ml-check/teacher")
                changed = client.post(
                    "/ml-check/teacher/phase",
                    data={
                        "csrf_token": csrf(teacher.text),
                        "session_id": session["id"],
                        "phase": "a",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(changed.status_code, 303)
                updated = db.get_session(database, int(session["id"]))
                elapsed = datetime.fromisoformat(
                    updated["phase_ends_at"]
                ) - datetime.fromisoformat(updated["phase_started_at"])
                self.assertEqual(elapsed.total_seconds(), 7)

    def test_answer_is_graded_against_the_saved_question(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "historical-answer.sqlite3")
            app = create_app(settings_for(database))
            raw = json.loads(bank_snapshot(DEFAULT_BANK))
            concept_id = raw["concepts"][0]["concept_id"]
            historical_question = next(
                question
                for question in raw["questions"]
                if question["concept_id"] == concept_id and question["phase"] == "A"
            )
            current_answer = historical_question["answer"]
            historical_answer = (current_answer + 1) % 4
            historical_question["answer"] = historical_answer
            historical_question["explanation"] = "历史场次专用解析。"
            session = db.create_session(
                database,
                DEFAULT_BANK.lesson_id,
                "历史答案场次",
                "old-answer-bank",
                json.dumps(raw, ensure_ascii=False),
            )
            db.set_phase(database, int(session["id"]), "a", 60)

            with TestClient(app) as client:
                client.get("/ml-check/test-login?login=historical-student&role=student")
                page = client.get("/ml-check/current")
                submitted = client.post(
                    "/ml-check/answer",
                    data={
                        "csrf_token": csrf(page.text),
                        "session_id": session["id"],
                        "concept_id": concept_id,
                        "phase": "a",
                        "option_id": str(historical_answer),
                        "confidence": "sure",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(submitted.status_code, 303)
            with db.connect(database) as connection:
                stored = connection.execute(
                    "SELECT option_id, correct FROM responses WHERE session_id = ?",
                    (session["id"],),
                ).fetchone()
            self.assertEqual(tuple(stored), (str(historical_answer), 1))

    def test_health_rejects_missing_corrupt_and_mismatched_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            database = str(Path(folder) / "health.sqlite3")
            app = create_app(settings_for(database))
            with db.connect(database) as connection:
                connection.execute(
                    """
                    INSERT INTO course_sessions
                        (lesson_id,title,phase,created_at)
                    VALUES ('S02','未回填','closed','2026-09-21')
                    """
                )
            with TestClient(app) as client:
                response = client.get("/ml-check/healthz")
                self.assertEqual(response.status_code, 500)
                self.assertIn("尚未完成", response.json()["detail"])

            with db.connect(database) as connection:
                connection.execute("DELETE FROM course_sessions WHERE title = '未回填'")
                connection.execute(
                    "UPDATE course_sessions SET bank_json = '{', bank_version = 'broken'"
                )
            with TestClient(app) as client:
                response = client.get("/ml-check/healthz")
                self.assertEqual(response.status_code, 500)
                self.assertIn("无法读取", response.json()["detail"])

            # A valid newest session must not hide corruption in history.
            with db.connect(database) as connection:
                connection.execute(
                    "UPDATE course_sessions SET bank_json = '{', bank_version = 'broken' WHERE id = 1"
                )
                connection.execute(
                    """
                    INSERT INTO course_sessions
                        (lesson_id,title,phase,bank_version,bank_json,created_at)
                    VALUES ('S02','最新正常场次','closed',?,?, '2026-09-22')
                    """,
                    (BANK_VERSION, bank_snapshot(bank_for_lesson("S02"))),
                )
            with TestClient(app) as client:
                response = client.get("/ml-check/healthz")
                self.assertEqual(response.status_code, 500)
                self.assertIn("无法读取", response.json()["detail"])

            wrong = json.loads(bank_snapshot(bank_for_lesson("S02")))
            with db.connect(database) as connection:
                connection.execute(
                    "UPDATE course_sessions SET bank_json = ?, bank_version = 'wrong'",
                    (json.dumps(wrong, ensure_ascii=False),),
                )
            with TestClient(app) as client:
                response = client.get("/ml-check/healthz")
                self.assertEqual(response.status_code, 500)
                self.assertIn("无法读取", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

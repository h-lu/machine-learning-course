import importlib.util
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.questions import bank_for_lesson, bank_from_snapshot, bank_snapshot


SCRIPT = Path(__file__).parents[1] / "deploy/backfill_session_snapshots.py"
PRODUCTION_MAP = SCRIPT.parent / "session-snapshot-map-2026-09-21.json"
SPEC = importlib.util.spec_from_file_location("snapshot_backfill", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_bank(
    path: Path,
    lesson_ids=("S02",),
    *,
    durations=True,
    version="old-v1",
    title_marker="回填时的旧标题",
) -> None:
    lessons = []
    for lesson_id in lesson_ids:
        item = json.loads(bank_snapshot(bank_for_lesson(lesson_id)))
        item["title"] = f"{lesson_id} {title_marker}"
        if not durations:
            item.pop("durations")
        lessons.append(item)
    path.write_text(
        json.dumps({"version": version, "lessons": lessons}, ensure_ascii=False),
        encoding="utf-8",
    )


def write_manifest(path: Path, entries: dict[int, tuple[str, Path, str]]) -> None:
    sessions = {}
    for session_id, (lesson_id, bank, version) in entries.items():
        sessions[str(session_id)] = {
            "lesson_id": lesson_id,
            "bank": str(bank.relative_to(path.parent)),
            "bank_version": version,
            "bank_sha256": hashlib.sha256(bank.read_bytes()).hexdigest(),
        }
    path.write_text(json.dumps({"sessions": sessions}), encoding="utf-8")


def legacy_database(path: Path, rows=((11, "S02"),)) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE course_sessions (
            id INTEGER PRIMARY KEY,
            lesson_id TEXT,
            title TEXT,
            phase TEXT,
            created_at TEXT
        )
        """
    )
    for session_id, lesson_id in rows:
        connection.execute(
            "INSERT INTO course_sessions VALUES (?, ?, ?, 'result', '2026-09-21')",
            (session_id, lesson_id, f"课堂标题 {session_id}"),
        )
    connection.commit()
    connection.close()


class SnapshotBackfill(unittest.TestCase):
    def test_production_map_pins_the_four_observed_historical_sessions(self):
        sessions = json.loads(PRODUCTION_MAP.read_text(encoding="utf-8"))["sessions"]
        self.assertEqual(
            {
                session_id: (entry["lesson_id"], entry["bank_version"])
                for session_id, entry in sessions.items()
            },
            {
                "7": ("C01", "ml-v4-2026-09-14"),
                "8": ("C02", "ml-v6-2026-09-16"),
                "9": ("S01", "ml-v11-s01-s02-review-2026-09-20"),
                "11": ("S02", "ml-v11-s01-s02-review-2026-09-20"),
            },
        )
        self.assertEqual(
            sessions["9"]["bank_sha256"],
            "c044440b1d2efe5a5f485632567502a758835004de334ae9f49e240e12cb7f81",
        )
        self.assertEqual(sessions["11"]["bank_sha256"], sessions["9"]["bank_sha256"])

    def test_backfills_matching_lesson_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "legacy.sqlite3"
            bank = root / "bank.json"
            write_bank(bank)
            legacy_database(database)

            self.assertEqual(MODULE.inspect(database, bank), (1, 1))
            self.assertEqual(MODULE.backfill(database, bank), (1, 1))
            self.assertEqual(MODULE.backfill(database, bank), (0, 1))
            connection = sqlite3.connect(database)
            row = connection.execute(
                "SELECT title, bank_version, bank_json FROM course_sessions WHERE id = 11"
            ).fetchone()
            connection.close()
            self.assertEqual(row[0], "课堂标题 11")
            self.assertEqual(row[1], "old-v1")
            restored = bank_from_snapshot(row[2])
            self.assertEqual(restored.title, "S02 回填时的旧标题")

    def test_old_bank_without_durations_preserves_the_old_default_schedule(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "legacy.sqlite3"
            bank = root / "bank.json"
            write_bank(bank, durations=False)
            legacy_database(database)
            MODULE.backfill(database, bank)
            connection = sqlite3.connect(database)
            value = connection.execute(
                "SELECT bank_json FROM course_sessions WHERE id = 11"
            ).fetchone()[0]
            connection.close()
            self.assertEqual(
                bank_from_snapshot(value).durations,
                {"attempt_a": 600, "learn": 900, "attempt_b": 600},
            )

    def test_error_rolls_back_every_row_and_schema_change(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "legacy.sqlite3"
            bank = root / "bank.json"
            write_bank(bank, ("S02",))
            legacy_database(database, ((11, "S02"), (12, "S03")))

            with self.assertRaisesRegex(ValueError, "S03 不在题库中"):
                MODULE.backfill(database, bank)
            connection = sqlite3.connect(database)
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(course_sessions)")
            }
            rows = connection.execute("SELECT id, lesson_id FROM course_sessions ORDER BY id").fetchall()
            connection.close()
            self.assertNotIn("bank_json", columns)
            self.assertEqual(rows, [(11, "S02"), (12, "S03")])

    def test_existing_snapshots_are_preserved_and_corruption_stops_the_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "snapshots.sqlite3"
            bank = root / "bank.json"
            write_bank(bank, ("S02", "S03"))
            legacy_database(database, ((11, "S02"), (12, "S03")))
            connection = sqlite3.connect(database)
            connection.execute("ALTER TABLE course_sessions ADD COLUMN bank_version TEXT")
            connection.execute("ALTER TABLE course_sessions ADD COLUMN bank_json TEXT")
            frozen = bank_snapshot(bank_for_lesson("S02"))
            connection.execute(
                "UPDATE course_sessions SET bank_version='frozen-v0', bank_json=? WHERE id=11",
                (frozen,),
            )
            connection.execute(
                "UPDATE course_sessions SET bank_version='broken-v0', bank_json='{' WHERE id=12"
            )
            connection.commit()
            connection.close()

            with self.assertRaisesRegex(ValueError, "已有题库快照无法读取"):
                MODULE.backfill(database, bank)
            connection = sqlite3.connect(database)
            rows = connection.execute(
                "SELECT id, bank_version, bank_json FROM course_sessions ORDER BY id"
            ).fetchall()
            connection.close()
            self.assertEqual(rows[0], (11, "frozen-v0", frozen))
            self.assertEqual(rows[1], (12, "broken-v0", "{"))

    def test_missing_database_and_duplicate_lessons_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            missing = root / "missing.sqlite3"
            bank = root / "bank.json"
            write_bank(bank)
            with self.assertRaises(FileNotFoundError):
                MODULE.backfill(missing, bank)
            self.assertFalse(missing.exists())

            raw = json.loads(bank.read_text(encoding="utf-8"))
            raw["lessons"].append(raw["lessons"][0])
            bank.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            database = root / "legacy.sqlite3"
            legacy_database(database)
            with self.assertRaisesRegex(ValueError, "重复课次"):
                MODULE.backfill(database, bank)

    def test_mapped_backfill_uses_each_historical_bank_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "legacy.sqlite3"
            bank_s02 = root / "bank-s02.json"
            bank_s03 = root / "bank-s03.json"
            manifest = root / "sessions.json"
            write_bank(
                bank_s02,
                ("S02",),
                version="historical-v2",
                title_marker="第一份历史题库",
            )
            write_bank(
                bank_s03,
                ("S03",),
                version="historical-v3",
                title_marker="第二份历史题库",
            )
            write_manifest(
                manifest,
                {
                    11: ("S02", bank_s02, "historical-v2"),
                    12: ("S03", bank_s03, "historical-v3"),
                },
            )
            legacy_database(database, ((11, "S02"), (12, "S03")))

            self.assertEqual(MODULE.inspect_mapped(database, manifest), (2, 2))
            self.assertEqual(MODULE.backfill_mapped(database, manifest), (2, 2))
            # A retry validates the already stored snapshots and writes none.
            self.assertEqual(MODULE.backfill_mapped(database, manifest), (0, 2))

            connection = sqlite3.connect(database)
            rows = connection.execute(
                "SELECT id, bank_version, bank_json FROM course_sessions ORDER BY id"
            ).fetchall()
            connection.close()
            self.assertEqual([row[1] for row in rows], ["historical-v2", "historical-v3"])
            self.assertEqual(
                bank_from_snapshot(rows[0][2]).title, "S02 第一份历史题库"
            )
            self.assertEqual(
                bank_from_snapshot(rows[1][2]).title, "S03 第二份历史题库"
            )

    def test_mapping_rejects_missing_unknown_or_mismatched_metadata_atomically(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bank_s02 = root / "bank-s02.json"
            bank_s03 = root / "bank-s03.json"
            write_bank(bank_s02, ("S02",), version="historical-v2")
            write_bank(bank_s03, ("S03",), version="historical-v3")

            good_entries = {
                11: ("S02", bank_s02, "historical-v2"),
                12: ("S03", bank_s03, "historical-v3"),
            }
            cases = {
                "missing": (good_entries | {12: good_entries[12]}, lambda raw: raw["sessions"].pop("12"), "缺少待回填场次"),
                "unknown": (good_entries, lambda raw: raw["sessions"].update({"13": raw["sessions"]["12"]}), "不存在的场次"),
                "lesson": (good_entries, lambda raw: raw["sessions"]["11"].update({"lesson_id": "S03"}), "映射却写为"),
                "version": (good_entries, lambda raw: raw["sessions"]["11"].update({"bank_version": "wrong"}), "期望题库 wrong"),
                "digest": (good_entries, lambda raw: raw["sessions"]["11"].update({"bank_sha256": "0" * 64}), "SHA-256 不符"),
            }
            for name, (entries, mutate, message) in cases.items():
                with self.subTest(name=name):
                    database = root / f"{name}.sqlite3"
                    manifest = root / f"{name}.json"
                    legacy_database(database, ((11, "S02"), (12, "S03")))
                    write_manifest(manifest, entries)
                    raw = json.loads(manifest.read_text(encoding="utf-8"))
                    mutate(raw)
                    manifest.write_text(json.dumps(raw), encoding="utf-8")

                    with self.assertRaisesRegex(ValueError, message):
                        MODULE.backfill_mapped(database, manifest)
                    connection = sqlite3.connect(database)
                    columns = {
                        row[1]
                        for row in connection.execute("PRAGMA table_info(course_sessions)")
                    }
                    connection.close()
                    self.assertNotIn("bank_json", columns)

    def test_mapping_never_overwrites_an_existing_different_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "legacy.sqlite3"
            original = root / "original.json"
            changed = root / "changed.json"
            manifest = root / "sessions.json"
            write_bank(original, version="same-version", title_marker="原始内容")
            write_bank(changed, version="same-version", title_marker="另一份内容")
            legacy_database(database)
            write_manifest(manifest, {11: ("S02", original, "same-version")})
            MODULE.backfill_mapped(database, manifest)
            connection = sqlite3.connect(database)
            before = connection.execute(
                "SELECT bank_version, bank_json FROM course_sessions WHERE id=11"
            ).fetchone()
            connection.close()

            write_manifest(manifest, {11: ("S02", changed, "same-version")})
            with self.assertRaisesRegex(ValueError, "内容不同，拒绝覆盖"):
                MODULE.backfill_mapped(database, manifest)
            connection = sqlite3.connect(database)
            after = connection.execute(
                "SELECT bank_version, bank_json FROM course_sessions WHERE id=11"
            ).fetchone()
            connection.close()
            self.assertEqual(after, before)

    def test_cli_is_read_only_by_default_and_apply_requires_a_new_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "legacy.sqlite3"
            bank = root / "bank.json"
            backup = root / "backup.sqlite3"
            write_bank(bank)
            legacy_database(database)

            planned = subprocess.run(
                [sys.executable, str(SCRIPT), "--database", str(database), "--bank", str(bank)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            self.assertIn("未修改数据库", planned.stdout)
            connection = sqlite3.connect(database)
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(course_sessions)")
            }
            connection.close()
            self.assertNotIn("bank_json", columns)

            applied = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--database",
                    str(database),
                    "--bank",
                    str(bank),
                    "--apply",
                    "--confirm-uniform-bank",
                    "--backup",
                    str(backup),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertTrue(backup.is_file())
            backup_connection = sqlite3.connect(backup)
            backup_columns = {
                row[1] for row in backup_connection.execute(
                    "PRAGMA table_info(course_sessions)"
                )
            }
            backup_connection.close()
            self.assertNotIn("bank_json", backup_columns)

            repeated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--database",
                    str(database),
                    "--bank",
                    str(bank),
                    "--apply",
                    "--confirm-uniform-bank",
                    "--backup",
                    str(backup),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("备份目标已存在", repeated.stderr)

    def test_cli_refuses_unconfirmed_uniform_write_and_accepts_session_map(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            database = root / "legacy.sqlite3"
            bank = root / "bank.json"
            manifest = root / "sessions.json"
            backup = root / "backup.sqlite3"
            write_bank(bank, version="historical-v2")
            write_manifest(manifest, {11: ("S02", bank, "historical-v2")})
            legacy_database(database)

            refused = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--database",
                    str(database),
                    "--bank",
                    str(bank),
                    "--apply",
                    "--backup",
                    str(backup),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("--confirm-uniform-bank", refused.stderr)
            self.assertFalse(backup.exists())

            applied = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--database",
                    str(database),
                    "--session-map",
                    str(manifest),
                    "--apply",
                    "--backup",
                    str(backup),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertTrue(backup.is_file())


if __name__ == "__main__":
    unittest.main()

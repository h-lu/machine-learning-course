"""Attach the deployed lesson bank to sessions created before snapshots existed.

Production procedure:

1. Stop ml-check so no session can be created during the backup/backfill window.
2. Collect the exact historical ``lessons.json`` files used by old sessions.
3. Run this command without ``--apply`` and inspect the planned counts.
4. Run it again with ``--apply`` and a new ``--backup`` path.
5. Only after a successful backfill, deploy the new bank and application.

When every old session used one bank, ``--bank`` plus
``--confirm-uniform-bank`` is available.  If sessions span releases, use a
``--session-map`` that assigns each session id to its exact historical bank.

Existing answers and session titles are not changed.  Every write runs in one
``BEGIN IMMEDIATE`` transaction.  Existing non-empty snapshots are validated
and preserved rather than silently overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))
from app.questions import LEGACY_DURATIONS, bank_from_snapshot, bank_snapshot


def _require_database(database: Path) -> None:
    if not database.is_file():
        raise FileNotFoundError(f"数据库文件不存在：{database}")


def _load_bank(bank_file: Path) -> tuple[str, dict[str, str], str]:
    if not bank_file.is_file():
        raise FileNotFoundError(f"题库文件不存在：{bank_file}")
    content = bank_file.read_bytes()
    raw = json.loads(content)
    if not isinstance(raw, dict) or not isinstance(raw.get("version"), str) or not raw["version"].strip():
        raise ValueError("题库缺少非空 version")
    rows = raw.get("lessons")
    if not isinstance(rows, list) or not rows:
        raise ValueError("题库没有课次")

    lessons: dict[str, str] = {}
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("题库课次必须是对象")
        lesson_id = item.get("lesson_id")
        if not isinstance(lesson_id, str) or not lesson_id:
            raise ValueError("题库课次缺少 lesson_id")
        if lesson_id in lessons:
            raise ValueError(f"题库包含重复课次 {lesson_id}")
        payload = {
            "lesson_id": lesson_id,
            "title": item.get("title"),
            "module": item.get("module", ""),
            "questions": item.get("questions"),
            "concepts": item.get("concepts"),
            # Older deployed banks omitted durations for lessons that used the
            # original 10/15/10-minute schedule.  Preserve that exact meaning.
            "durations": item.get("durations", LEGACY_DURATIONS),
        }
        try:
            lessons[lesson_id] = bank_snapshot(
                bank_from_snapshot(json.dumps(payload, ensure_ascii=False))
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"题库课次 {lesson_id} 无法构成有效快照") from error
    return raw["version"], lessons, hashlib.sha256(content).hexdigest()


def _session_rows(connection: sqlite3.Connection, columns: set[str]) -> list[sqlite3.Row]:
    version = "bank_version" if "bank_version" in columns else "NULL AS bank_version"
    snapshot = "bank_json" if "bank_json" in columns else "NULL AS bank_json"
    return connection.execute(
        f"SELECT id, lesson_id, {version}, {snapshot} FROM course_sessions ORDER BY id"
    ).fetchall()


def _validate_and_plan(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    missing = []
    for row in rows:
        lesson_id = str(row["lesson_id"])
        raw_snapshot = row["bank_json"]
        raw_version = row["bank_version"]
        if raw_snapshot is None or not str(raw_snapshot).strip():
            if raw_version is not None and str(raw_version).strip():
                raise ValueError(f"场次 {row['id']} 只有 bank_version，却没有 bank_json")
            missing.append(row)
            continue
        if raw_version is None or not str(raw_version).strip():
            raise ValueError(f"场次 {row['id']} 已有 bank_json，却没有 bank_version")
        try:
            saved = bank_from_snapshot(str(raw_snapshot))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"场次 {row['id']} 的已有题库快照无法读取") from error
        if saved.lesson_id != lesson_id:
            raise ValueError(
                f"场次 {row['id']} 的课次 {lesson_id} 与快照 {saved.lesson_id} 不一致"
            )
    return missing


def _uniform_assignments(
    missing: list[sqlite3.Row], version: str, lessons: dict[str, str]
) -> dict[int, tuple[str, str]]:
    assignments = {}
    for row in missing:
        lesson_id = str(row["lesson_id"])
        if lesson_id not in lessons:
            raise ValueError(f"场次 {row['id']} 的课次 {lesson_id} 不在题库中")
        assignments[int(row["id"])] = (version, lessons[lesson_id])
    return assignments


def _mapped_assignments(
    rows: list[sqlite3.Row],
    missing: list[sqlite3.Row],
    manifest_file: Path,
) -> dict[int, tuple[str, str]]:
    if not manifest_file.is_file():
        raise FileNotFoundError(f"场次映射文件不存在：{manifest_file}")
    raw = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries = raw.get("sessions") if isinstance(raw, dict) else None
    if not isinstance(entries, dict) or not entries:
        raise ValueError("场次映射必须包含非空 sessions 对象")
    parsed: dict[int, dict] = {}
    for raw_id, entry in entries.items():
        try:
            session_id = int(raw_id)
        except (TypeError, ValueError) as error:
            raise ValueError(f"场次映射 id 无效：{raw_id}") from error
        if str(session_id) != str(raw_id) or session_id <= 0:
            raise ValueError(f"场次映射 id 无效：{raw_id}")
        if not isinstance(entry, dict):
            raise ValueError(f"场次 {session_id} 的映射必须是对象")
        if session_id in parsed:
            raise ValueError(f"场次映射重复 id：{session_id}")
        parsed[session_id] = entry

    rows_by_id = {int(row["id"]): row for row in rows}
    missing_ids = {int(row["id"]) for row in missing}
    unknown = sorted(set(parsed) - set(rows_by_id))
    absent = sorted(missing_ids - set(parsed))
    if absent or unknown:
        raise ValueError(
            f"场次映射与数据库不一致；缺少待回填场次 {absent}，"
            f"数据库中不存在的场次 {unknown}"
        )

    bank_cache: dict[Path, tuple[str, dict[str, str], str]] = {}
    assignments = {}
    for session_id, entry in parsed.items():
        row = rows_by_id[session_id]
        lesson_id = str(row["lesson_id"])
        declared_lesson = entry.get("lesson_id")
        if declared_lesson != lesson_id:
            raise ValueError(
                f"场次 {session_id} 数据库课次为 {lesson_id}，映射却写为 {declared_lesson}"
            )
        raw_path = entry.get("bank")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"场次 {session_id} 缺少 bank 路径")
        bank_path = Path(raw_path)
        if not bank_path.is_absolute():
            bank_path = manifest_file.parent / bank_path
        bank_path = bank_path.resolve()
        if bank_path not in bank_cache:
            bank_cache[bank_path] = _load_bank(bank_path)
        version, lessons, digest = bank_cache[bank_path]
        if lesson_id not in lessons:
            raise ValueError(
                f"场次 {session_id} 的课次 {lesson_id} 不在 {bank_path} 中"
            )
        expected_version = entry.get("bank_version")
        if not isinstance(expected_version, str) or not expected_version.strip():
            raise ValueError(f"场次 {session_id} 缺少非空 bank_version")
        if expected_version != version:
            raise ValueError(
                f"场次 {session_id} 期望题库 {expected_version}，文件实际为 {version}"
            )
        expected_digest = entry.get("bank_sha256")
        if (
            not isinstance(expected_digest, str)
            or len(expected_digest) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in expected_digest)
        ):
            raise ValueError(f"场次 {session_id} 缺少有效的 bank_sha256")
        if expected_digest.lower() != digest:
            raise ValueError(
                f"场次 {session_id} 的题库 SHA-256 不符；"
                f"期望 {expected_digest.lower()}，实际 {digest}"
            )

        snapshot = lessons[lesson_id]
        if session_id in missing_ids:
            assignments[session_id] = (version, snapshot)
            continue

        # A repeated run may include sessions that were filled by an earlier
        # run.  Verify their exact historical source and preserve the stored
        # bytes; never turn a mapping file into an overwrite mechanism.
        if str(row["bank_version"]) != version:
            raise ValueError(
                f"场次 {session_id} 已有快照版本 {row['bank_version']}，"
                f"映射题库版本为 {version}，拒绝覆盖"
            )
        saved = bank_snapshot(bank_from_snapshot(str(row["bank_json"])))
        if saved != snapshot:
            raise ValueError(
                f"场次 {session_id} 已有快照与映射题库内容不同，拒绝覆盖"
            )
    return assignments


def _read_plan(database: Path) -> tuple[set[str], list[sqlite3.Row]]:
    uri = f"file:{quote(str(database.resolve()))}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(course_sessions)")
        }
        if not columns:
            raise ValueError("数据库没有 course_sessions 表")
        return columns, _session_rows(connection, columns)
    finally:
        connection.close()


def inspect(database: Path, bank_file: Path) -> tuple[int, int]:
    """Validate a read-only plan and return ``(missing, total)``."""
    _require_database(database)
    version, lessons, _digest = _load_bank(bank_file)
    _, rows = _read_plan(database)
    missing = _validate_and_plan(rows)
    _uniform_assignments(missing, version, lessons)
    return len(missing), len(rows)


def inspect_mapped(database: Path, manifest_file: Path) -> tuple[int, int]:
    """Validate a per-session historical bank plan without writing."""
    _require_database(database)
    _, rows = _read_plan(database)
    missing = _validate_and_plan(rows)
    _mapped_assignments(rows, missing, manifest_file)
    return len(missing), len(rows)


def _apply_backfill(database: Path, assignment_builder) -> tuple[int, int]:
    connection = sqlite3.connect(database, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    try:
        connection.execute("BEGIN IMMEDIATE")
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(course_sessions)")
        }
        if not columns:
            raise ValueError("数据库没有 course_sessions 表")
        rows = _session_rows(connection, columns)
        missing = _validate_and_plan(rows)
        assignments = assignment_builder(rows, missing)
        if set(assignments) != {int(row["id"]) for row in missing}:
            raise ValueError("内部错误：回填分配未覆盖全部待回填场次")
        if "bank_version" not in columns:
            connection.execute("ALTER TABLE course_sessions ADD COLUMN bank_version TEXT")
        if "bank_json" not in columns:
            connection.execute("ALTER TABLE course_sessions ADD COLUMN bank_json TEXT")
        for row in missing:
            session_id = int(row["id"])
            version, snapshot = assignments[session_id]
            connection.execute(
                "UPDATE course_sessions SET bank_version = ?, bank_json = ? WHERE id = ?",
                (version, snapshot, session_id),
            )
        connection.commit()
        return len(missing), len(rows)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def backfill(database: Path, bank_file: Path) -> tuple[int, int]:
    """Atomically add and populate snapshot columns for all legacy sessions."""
    _require_database(database)
    version, lessons, _digest = _load_bank(bank_file)
    return _apply_backfill(
        database,
        lambda _rows, missing: _uniform_assignments(missing, version, lessons),
    )


def backfill_mapped(database: Path, manifest_file: Path) -> tuple[int, int]:
    """Atomically backfill each session from its mapped historical bank."""
    _require_database(database)
    return _apply_backfill(
        database,
        lambda rows, missing: _mapped_assignments(rows, missing, manifest_file),
    )


def backup_database(database: Path, destination: Path) -> None:
    """Create a consistent SQLite backup and refuse to overwrite a file."""
    _require_database(database)
    if destination.exists():
        raise FileExistsError(f"备份目标已存在：{destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    uri = f"file:{quote(str(database.resolve()))}?mode=ro"
    source = None
    target = None
    try:
        source = sqlite3.connect(uri, uri=True, timeout=10)
        target = sqlite3.connect(destination)
        source.backup(target)
        result = target.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"SQLite 备份完整性检查失败：{result}")
    except Exception:
        if target is not None:
            target.close()
        destination.unlink(missing_ok=True)
        raise
    else:
        target.close()
    finally:
        if source is not None:
            source.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--bank", type=Path)
    source.add_argument("--session-map", type=Path)
    parser.add_argument(
        "--confirm-uniform-bank",
        action="store_true",
        help="确认所有待回填场次当时确实使用同一份 --bank",
    )
    parser.add_argument(
        "--apply", action="store_true", help="实际写入；省略时只做只读检查"
    )
    parser.add_argument(
        "--backup", type=Path, help="--apply 前创建的 SQLite 备份；目标必须不存在"
    )
    args = parser.parse_args()

    if args.session_map is not None and args.confirm_uniform_bank:
        parser.error("--confirm-uniform-bank 只能与 --bank 同时使用")
    if not args.apply and args.backup is not None:
        parser.error("--backup 只能与 --apply 同时使用")
    if args.apply and args.bank is not None and not args.confirm_uniform_bank:
        parser.error("用 --bank 写入时必须显式提供 --confirm-uniform-bank")

    try:
        if args.session_map is not None:
            missing, total = inspect_mapped(args.database, args.session_map)
        else:
            missing, total = inspect(args.database, args.bank)
    except (OSError, RuntimeError, json.JSONDecodeError, sqlite3.Error, ValueError) as error:
        parser.exit(1, f"只读检查失败：{error}\n")
    if not args.apply:
        print(
            f"只读检查通过：{missing} 个场次需要回填，数据库共 {total} 个场次。"
            "未修改数据库；停止服务后使用 --apply --backup <新文件> 执行。"
        )
        return 0
    if args.backup is None:
        parser.error("--apply 必须同时提供 --backup")
    try:
        backup_database(args.database, args.backup)
        if args.session_map is not None:
            updated, total = backfill_mapped(args.database, args.session_map)
        else:
            updated, total = backfill(args.database, args.bank)
    except (OSError, RuntimeError, json.JSONDecodeError, sqlite3.Error, ValueError) as error:
        parser.exit(1, f"回填失败：{error}\n")
    print(
        f"已创建备份 {args.backup}；为 {updated} 个旧场次保存题目快照；"
        f"数据库共 {total} 个场次。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

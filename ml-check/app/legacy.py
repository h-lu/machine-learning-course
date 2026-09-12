"""Small local HTTP service with anonymous A/B completion receipts.

There is no login, grading session or submitted-code execution. Receipts are
optional metadata for a teacher's classroom snapshot, never an automatic grade.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from app import pages

BANK = Path(__file__).parent / "question_bank/lessons.json"


def load_bank(path: Path = BANK) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def public_lesson(lesson: dict) -> dict:
    # Allow-list fields: teacher answers/explanations never reach this GET API.
    return {"lesson_id": lesson["lesson_id"], "title": lesson["title"],
            "module": lesson["module"], "questions": [
                {key: q[key] for key in ("id", "phase", "prompt", "options")}
                for q in lesson["questions"]]}


def response(path: str, bank: dict, receipts=None) -> tuple[int, object]:
    path = urlsplit(path).path.rstrip("/")
    lessons = bank["lessons"]
    if path == "/ml-check/healthz":
        return 200, {"status": "ok", "lesson_count": len(lessons), "bank_version": bank["version"]}
    if path == "/ml-check/api/lessons":
        return 200, [{key: lesson[key] for key in ("lesson_id", "title", "module")} for lesson in lessons]
    if path.startswith("/ml-check/api/receipts/") and receipts is not None:
        receipt_id = path.rsplit("/", 1)[-1]
        value = receipts.get(receipt_id)
        return (200, value) if value is not None else (404, {"detail": "未找到该练习凭据。"})
    prefix = "/ml-check/api/lessons/"
    if path.startswith(prefix):
        lesson_id = path[len(prefix):].upper()
        for lesson in lessons:
            if lesson["lesson_id"] == lesson_id:
                return 200, public_lesson(lesson)
    return 404, {"detail": "未找到该课次或接口。"}


class ReceiptStore:
    """Tiny append-only SQLite store for A/B completion evidence.

    Receipts contain score metadata and a hash of answers, never the answer values.
    The anonymous service deliberately does not claim that a receipt identifies a
    student; teachers pair it with their own classroom record when needed.
    """

    def __init__(self, path: str | Path | None = None):
        configured = path or os.getenv("ML_CHECK_DB", ":memory:")
        self.path = str(configured)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.connection:
            self.connection.execute(
                """CREATE TABLE IF NOT EXISTS receipts (
                   id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL, phase TEXT NOT NULL,
                   correct INTEGER NOT NULL, total INTEGER NOT NULL,
                   answer_sha256 TEXT NOT NULL, submitted_at TEXT NOT NULL)"""
            )

    def add(self, lesson_id: str, phase: str, answers: dict, questions: list[dict]) -> dict:
        correct = sum(answers[q["id"]] == q["answer"] for q in questions)
        answer_sha = hashlib.sha256(
            json.dumps(answers, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        receipt = {
            "receipt_id": uuid.uuid4().hex,
            "lesson_id": lesson_id,
            "phase": phase,
            "correct": correct,
            "total": len(questions),
            "answer_sha256": answer_sha,
            "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?)",
                tuple(receipt.values()),
            )
        return receipt

    def get(self, receipt_id: str) -> dict | None:
        with self.lock:
            row = self.connection.execute(
                "SELECT id, lesson_id, phase, correct, total, answer_sha256, submitted_at FROM receipts WHERE id = ?",
                (receipt_id,),
            ).fetchone()
        if row is None:
            return None
        return {"receipt_id": row["id"], **{key: row[key] for key in ("lesson_id", "phase", "correct", "total", "answer_sha256", "submitted_at")}}


def make_handler(bank: dict, db_path: str | Path | None = None):
    lessons = {lesson["lesson_id"]: lesson for lesson in bank["lessons"]}
    receipts = ReceiptStore(db_path)

    class Handler(BaseHTTPRequestHandler):
        timeout = 15

        def send_body(self, status, body, content_type="text/html; charset=utf-8"):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            url = urlsplit(self.path)
            path = url.path.rstrip("/")
            if path == "/ml-check":
                return self.send_body(200, pages.home(bank))
            if path == "/ml-check/assets/site.css":
                return self.send_body(200, (Path(__file__).parent / "static/site.css").read_bytes(), "text/css; charset=utf-8")
            prefix = "/ml-check/lessons/"
            if path.startswith(prefix):
                lesson = lessons.get(path[len(prefix):].upper())
                if lesson is None:
                    return self.send_body(404, pages.error_page("未找到该课次。"))
                try:
                    query = parse_qs(url.query, max_num_fields=16)
                    phase = query.get("phase", ["A"])
                    if len(phase) != 1 or phase[0] not in ("A", "B"):
                        raise ValueError("phase")
                except ValueError:
                    return self.send_body(400, pages.error_page("请选择 A 轮或 B 轮练习。"))
                return self.send_body(200, pages.lesson_page(lesson, phase[0]))
            status, payload = response(self.path, bank, receipts)
            self.send_body(status, json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8")

        def do_POST(self):
            path = urlsplit(self.path).path.rstrip("/")
            parts = path.split("/")
            lesson = lessons.get(parts[3].upper()) if len(parts) == 5 and parts[1:3] == ["ml-check", "lessons"] and parts[4] == "check" else None
            if lesson is None:
                return self.send_body(404, pages.error_page("未找到该课次。"))
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192 or self.headers.get("Transfer-Encoding"):
                    raise ValueError("length")
                if self.headers.get_content_type() != "application/x-www-form-urlencoded":
                    raise ValueError("type")
                form = parse_qs(self.rfile.read(length).decode("utf-8"), max_num_fields=16)
                phase_values = form.get("phase", [])
                if len(phase_values) != 1 or phase_values[0] not in ("A", "B"):
                    raise ValueError("phase")
                phase = phase_values[0]
                questions = [q for q in lesson["questions"] if q["phase"] == phase]
                answers = {}
                for question in questions:
                    values = form.get(question["id"], [])
                    if len(values) != 1 or values[0] not in ("0", "1", "2", "3"):
                        raise ValueError("answer")
                    answers[question["id"]] = int(values[0])
            except (ValueError, UnicodeError):
                return self.send_body(400, pages.error_page("请为本轮每道题选择一个选项后再提交。"))
            receipt = receipts.add(lesson["lesson_id"], phase, answers, questions)
            self.send_body(200, pages.lesson_page(lesson, phase, answers, receipt))
    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="概念练习服务；记录匿名 A/B 完成凭据，不执行学生代码。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8896)
    parser.add_argument("--db", default=os.getenv("ML_CHECK_DB", ":memory:"), help="SQLite 路径；默认生产路径可由 ML_CHECK_DB 覆盖")
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(load_bank(), args.db))
    print(f"概念练习服务：http://{args.host}:{args.port}/ml-check", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

"""Small local HTTP service. No login, grading session or submitted-code execution."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

BANK = Path(__file__).parent / "question_bank/lessons.json"


def load_bank(path: Path = BANK) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def public_lesson(lesson: dict) -> dict:
    # Allow-list fields: teacher answers/explanations never reach this GET API.
    return {"lesson_id": lesson["lesson_id"], "title": lesson["title"],
            "module": lesson["module"], "questions": [
                {key: q[key] for key in ("id", "phase", "prompt", "options")}
                for q in lesson["questions"]]}


def response(path: str, bank: dict) -> tuple[int, object]:
    path = urlsplit(path).path.rstrip("/")
    lessons = bank["lessons"]
    if path == "/ml-check/healthz":
        return 200, {"status": "ok", "lesson_count": len(lessons), "bank_version": bank["version"]}
    if path == "/ml-check/api/lessons":
        return 200, [{key: lesson[key] for key in ("lesson_id", "title", "module")} for lesson in lessons]
    prefix = "/ml-check/api/lessons/"
    if path.startswith(prefix):
        lesson_id = path[len(prefix):].upper()
        for lesson in lessons:
            if lesson["lesson_id"] == lesson_id:
                return 200, public_lesson(lesson)
    return 404, {"detail": "未找到该课次或接口。"}


def make_handler(bank: dict):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, payload = response(self.path, bank)
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="本地概念题读取服务；不含登录与答题存储。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8896)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(load_bank()))
    print(f"概念题读取服务：http://{args.host}:{args.port}/ml-check/api/lessons", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

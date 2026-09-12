"""汇总机器学习课程课末提交状态；只读 Gitea，不评价模型或报告质量。"""
from __future__ import annotations

import argparse
import base64
import binascii
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

LESSONS = ["C01", "C02"] + [f"S{n:02d}" for n in range(1, 31)]
# Keep a numeric tag convention so the 32 lesson snapshots sort chronologically.
TAG_BY_LESSON = {lesson: f"v2-l{index:02d}-final" for index, lesson in enumerate(LESSONS, 1)}
STATUS_FILE_BY_TAG = {tag: f"lessons/{lesson}/submission.json" for lesson, tag in TAG_BY_LESSON.items()}
# Accept the short legacy spelling used by early classroom notes.
for lesson, tag in TAG_BY_LESSON.items():
    STATUS_FILE_BY_TAG[f"{lesson.lower()}-final"] = STATUS_FILE_BY_TAG[tag]


def lesson_for(value: str) -> str:
    """Resolve a lesson id or a supported final-tag spelling."""
    raw = str(value).strip()
    if raw in TAG_BY_LESSON:
        return raw
    for lesson, tag in TAG_BY_LESSON.items():
        if raw == tag or raw == f"{lesson.lower()}-final":
            return lesson
    raise ValueError(f"未知课次或标签：{value}")


def api_get(base_url: str, token: str, path: str) -> tuple[int, object | None]:
    request = Request(
        f"{base_url.rstrip('/')}/api/v1{path}",
        headers={"Authorization": f"token {token}", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return 404, None
        raise


def read_roster(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"student_id", "gitea_login", "repo_owner", "repo_name"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"名单必须包含：{', '.join(sorted(required))}")
    return rows


def repo_path(row: dict[str, str]) -> str:
    owner = quote(row["repo_owner"], safe="")
    repo = quote(row["repo_name"], safe="")
    return f"/repos/{owner}/{repo}"


def _missing() -> dict[str, str]:
    return {"light": "RED", "tag": "missing", "signed": "-", "sha": "-", "ci": "-"}


def status_for(base_url: str, token: str, row: dict[str, str], lesson: str) -> dict[str, str]:
    """Read repository, final tag, status file and combined CI state for one lesson."""
    lesson = lesson_for(lesson)
    tag = TAG_BY_LESSON[lesson]
    path = repo_path(row)
    repo_code, _ = api_get(base_url, token, path)
    if repo_code == 404:
        result = _missing()
        result["tag"] = "missing repo"
        return result
    tag_code, refs = api_get(base_url, token, f"{path}/git/refs/{quote('tags/' + tag, safe='')}")
    if tag_code == 404 or not refs:
        return _missing()

    status_file = STATUS_FILE_BY_TAG[tag]
    content_code, content_payload = api_get(
        base_url, token, f"{path}/contents/{quote(status_file, safe='/')}?ref={quote(tag, safe='')}"
    )
    signed = "missing"
    if content_code == 200 and isinstance(content_payload, dict):
        try:
            encoded = str(content_payload["content"]).replace("\n", "")
            submission = json.loads(base64.b64decode(encoded).decode("utf-8"))
            signed = str(submission.get("status", "missing"))
            if submission.get("lesson_id") != lesson:
                signed = "wrong_lesson"
        except (KeyError, ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
            signed = "invalid"

    status_code, combined = api_get(base_url, token, f"{path}/commits/{quote(tag, safe='')}/status")
    if status_code == 404 or not isinstance(combined, dict):
        return {
            "light": "RED" if signed != "complete" else "YELLOW",
            "tag": "present", "signed": signed, "sha": "-", "ci": "none",
        }
    state = str(combined.get("state") or "unknown")
    sha = str(combined.get("sha") or "-")
    if signed != "complete":
        light = "RED"
    else:
        light = "GREEN" if state == "success" else "YELLOW"
    return {"light": light, "tag": "present", "signed": signed, "sha": sha, "ci": state}


def print_table(rows: list[dict[str, str]]) -> None:
    fields = ("checked_at", "light", "student_id", "gitea_login", "repository", "tag", "signed", "sha", "ci")
    widths = {field: max(len(field), *(len(str(row[field])) for row in rows)) for field in fields}
    print("  ".join(field.ljust(widths[field]) for field in fields))
    print("  ".join("-" * widths[field] for field in fields))
    for row in rows:
        print("  ".join(str(row[field]).ljust(widths[field]) for field in fields))


def main() -> int:
    parser = argparse.ArgumentParser(description="保存 ML 课末完成快照；不是课中进度或自动迟交判定器")
    parser.add_argument("lesson", choices=LESSONS)
    parser.add_argument("--roster", type=Path, default=Path("roster/roster.csv"))
    parser.add_argument("--base-url", default=os.getenv("GITEA_BASE_URL", "https://hblu.top/gitea"))
    parser.add_argument("--csv", action="store_true", help="输出 CSV")
    args = parser.parse_args()
    token = os.getenv("GITEA_TOKEN", "").strip()
    if not token:
        parser.error("请通过环境变量 GITEA_TOKEN 提供只读或教师令牌")
    try:
        roster = read_roster(args.roster)
        checked_at = datetime.now().astimezone().isoformat(timespec="seconds")
        output = []
        for student in roster:
            result = status_for(args.base_url, token, student, args.lesson)
            output.append({
                "checked_at": checked_at,
                "light": result["light"],
                "student_id": student["student_id"],
                "gitea_login": student["gitea_login"],
                "repository": f"{student['repo_owner']}/{student['repo_name']}",
                "tag": result["tag"], "signed": result["signed"],
                "sha": result["sha"], "ci": result["ci"],
            })
    except (OSError, ValueError, HTTPError, URLError) as error:
        print(f"状态汇总失败：{error}", file=sys.stderr)
        return 1
    if args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(output[0]))
        writer.writeheader(); writer.writerows(output)
    else:
        print(f"课次：{args.lesson}  final tag：{TAG_BY_LESSON[args.lesson]}")
        print_table(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Apply only the checksum-reviewed S01 text edits; execute no course code."""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import json
import lzma
import os
import shutil
import subprocess
import tempfile

EXPECTED_TREE = "76bd01a81c0d15eb5f575938de352e46b0dd390b"
EXPECTED_PAYLOAD = "8dc0f81c456e02f4bcf9d4399a15df290e825d3a6657f1e868401f565097f430"
ALLOWED = set("""course-instructor/RELEASE.md
course-instructor/lessons/S01/REFERENCE.md
course-instructor/lessons/S01/RUNBOOK.md
course-instructor/lessons/S01/questions.json
course-instructor/reviews/s01-focused-review-2026-09-19.md
course-student-template/lesson-03/LEARN.md
course-student-template/lesson-03/README.md
course-student-template/lesson-03/SUPPORT.md
course-student-template/lesson-03/data/DATA.md
course-student-template/lesson-03/report.md
course-student-template/mlcourse/foundations.py
course-student-template/tests/test_foundations.py
course-student-template/tests/test_s01_review.py
ml-check/README.md
ml-check/app/question_bank/lessons.json
ml-check/deploy/README.md
ml-check/tests/test_foundation_bank.py
ml-check/tests/test_intro_bank.py
ml-check/tests/test_review_readiness.py
ml-check/tests/test_s01_walkthrough.py
tools/sync_question_bank.py""".splitlines())
assert os.environ.get("GITHUB_REF") == "refs/heads/course/s01-focused-review"
root = Path.cwd().resolve()
encoded = "".join((root / f".review-s01-transfer/part-{i}.b64").read_text() for i in range(3))
raw = lzma.decompress(base64.b64decode(encoded, validate=True), memlimit=128 * 1024 * 1024)
assert hashlib.sha256(raw).hexdigest() == EXPECTED_PAYLOAD
payload = json.loads(raw)
assert payload["tree"] == EXPECTED_TREE
assert len(payload["files"]) == len(ALLOWED)
assert {f["path"] for f in payload["files"]} == ALLOWED
pending = []
for item in payload["files"]:
    name = item["path"]
    relative = PurePosixPath(name)
    assert not relative.is_absolute() and ".." not in relative.parts
    path = root / name
    assert path.resolve().is_relative_to(root) and not path.is_symlink()
    if item["base_sha256"] is None:
        assert not path.exists()
        before = b""
    else:
        before = path.read_bytes()
        assert hashlib.sha256(before).hexdigest() == item["base_sha256"], name
    lines = before.decode("utf-8").splitlines(keepends=True)
    for start, end, replacement in reversed(item["edits"]):
        assert 0 <= start <= end <= len(lines)
        lines[start:end] = replacement.splitlines(keepends=True)
    after = "".join(lines).encode("utf-8")
    assert hashlib.sha256(after).hexdigest() == item["sha256"], name
    pending.append((path, after))
for path, content in pending:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
subprocess.run(["git", "add", "--", *sorted(ALLOWED)], check=True)
subprocess.run(["git", "diff", "--cached", "--check"], check=True)
# A separate index verifies the final tree without deleting the transfer files
# from this intermediate commit or changing any workflow with the runner token.
index = Path(subprocess.check_output(["git", "rev-parse", "--git-path", "index"], text=True).strip()).resolve()
with tempfile.TemporaryDirectory() as tmp:
    alternate = Path(tmp) / "index"
    shutil.copy2(index, alternate)
    env = {**os.environ, "GIT_INDEX_FILE": str(alternate)}
    subprocess.run(["git", "rm", "-r", "--cached", "--ignore-unmatch", "--", ".review-s01-transfer", ".github/workflows/prepare-s01-review.yml"], env=env, check=True)
    actual = subprocess.check_output(["git", "write-tree"], env=env, text=True).strip()
    assert actual == EXPECTED_TREE, (actual, EXPECTED_TREE)
print("Verified S01 source tree:", EXPECTED_TREE)

"""Small, transparent course workflow. Checks delivery, never authorship or reasoning."""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"not_started", "in_progress", "complete"}
TAG = re.compile(r"^v2-l(\d{2})-(?:final|revision-[1-9]\d*)$")


def lesson_name(value: str | int) -> str:
    raw = str(value).removeprefix("lesson-")
    if not raw.isdigit() or not 1 <= int(raw) <= 32:
        raise ValueError("课次必须为01—32")
    return f"lesson-{int(raw):02d}"


def active_lessons(root: Path) -> list[str]:
    path = root / "active_lessons.json"
    if not path.is_file():
        return [lesson_name(i) for i in range(1, 33)]
    values = json.loads(path.read_text(encoding="utf-8"))["active_student_lessons"]
    if not isinstance(values, list) or not values or values != list(dict.fromkeys(values)):
        raise ValueError("active_lessons.json 应列出不重复的活跃课次")
    if any(not isinstance(value, str) or lesson_name(value) != value for value in values):
        raise ValueError("活跃课次应使用 lesson-NN 格式")
    return values


def inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip() or Path(relative).is_absolute():
        raise ValueError("提交文件的路径必须是非空的仓库相对路径")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"路径超出仓库：{relative}")
    return path


def manifest(root: Path, lesson: str) -> dict:
    if lesson not in active_lessons(root):
        raise ValueError(f"{lesson} 尚无本轮活跃课包；旧材料已归档，当前请使用active_lessons.json中列出的课次")
    path = root / lesson / "submission.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("lesson") != lesson:
        raise ValueError(f"{lesson}：submission.json课次不符")
    if obj.get("status") not in STATUSES:
        raise ValueError(f"{lesson}：status应为not_started、in_progress或complete")
    inside(root, obj.get("report", ""))
    paths = obj.get("artifacts")
    if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
        raise ValueError(f"{lesson}：artifacts必须为文件路径列表")
    if len(set(paths)) != len(paths):
        raise ValueError(f"{lesson}：artifacts有重复路径")
    for item in paths:
        inside(root, item)
    command = obj.get("run")
    if not isinstance(command, list) or not command or any(not isinstance(p, str) or not p for p in command):
        raise ValueError(f"{lesson}：run必须为非空命令参数列表")
    return obj


def start(root: Path, lesson: str) -> None:
    obj = manifest(root, lesson)
    if obj["status"] == "complete":
        print(f"{lesson}已有完成声明；继续修订时保留原标签。")
        return
    obj["status"] = "in_progress"
    (root / lesson / "submission.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已开始{lesson}。请阅读本课README和LEARN。")


def run(root: Path, lesson: str) -> None:
    command = list(manifest(root, lesson)["run"])
    if command[0] in {"python", "python3"}:
        command[0] = sys.executable
    print(f"运行{lesson}：{' '.join(command)}", flush=True)
    subprocess.run(command, cwd=root, check=True, timeout=600)


def check(root: Path, lesson: str) -> dict:
    obj = manifest(root, lesson)
    if obj["status"] != "complete":
        raise ValueError(f"{lesson}：尚未标记complete；请先完成项目，再检查提交文件")
    report = inside(root, obj["report"])
    if not report.is_file() or report.stat().st_size == 0:
        raise ValueError(f"{lesson}：报告不存在或为空")
    if not obj["artifacts"]:
        raise ValueError(f"{lesson}：请列出支持报告结论的结果文件；仅运行示例代码不等于完成项目")
    for value in obj["artifacts"]:
        evidence = inside(root, value)
        if not evidence.is_file() or evidence.stat().st_size == 0:
            raise ValueError(f"{lesson}：结果文件不存在或为空：{value}")
        if value == obj["report"] or evidence.name == "submission.json":
            raise ValueError(f"{lesson}：结果文件应包含分析结果，不能填写完成声明或报告本身")
    print(f"{lesson}提交文件检查通过；仍需核对分析问题、计算结果和结论。")
    return obj


def digest(root: Path, paths: list[str]) -> dict[str, str]:
    return {p: hashlib.sha256(inside(root, p).read_bytes()).hexdigest() for p in paths}


def reproduce(root: Path, lesson: str) -> None:
    obj = check(root, lesson)
    before = digest(root, obj["artifacts"])
    # Work on a disposable copy: a no-op must not pass by reusing old outputs,
    # and a failed reproduction must not destroy the student's submitted files.
    with tempfile.TemporaryDirectory(prefix="ml-reproduce-") as temp:
        scratch = (Path(temp) / "project").resolve()
        shutil.copytree(root, scratch, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
        artifacts = [inside(scratch, path) for path in obj["artifacts"]]
        for path in artifacts:
            path.unlink()
        # Fresh-output helpers reject existing directories. Remove only empty
        # parents of listed outputs; rmdir preserves any unlisted files there.
        for path in artifacts:
            parent = path.parent
            while parent != scratch:
                try:
                    parent.rmdir()
                except FileNotFoundError:
                    break
                except OSError as error:
                    if error.errno not in {errno.ENOTEMPTY, errno.EEXIST}:
                        raise
                    break
                parent = parent.parent
        run(scratch, lesson)
        check(scratch, lesson)
        if before != digest(scratch, obj["artifacts"]):
            raise ValueError(f"{lesson}：重新运行得到的结果与已提交文件不同；请检查随机种子，或重新生成结果后提交")


def ci(root: Path, ref: str = "") -> None:
    objects = {lesson: manifest(root, lesson) for lesson in active_lessons(root)}
    selected = None
    if ref.startswith("refs/tags/v2-"):
        match = TAG.fullmatch(ref.removeprefix("refs/tags/"))
        if not match:
            raise ValueError("V2标签应为v2-lNN-final或v2-lNN-revision-N")
        selected = lesson_name(match.group(1))
        check(root, selected)
    for lesson, obj in objects.items():
        if selected and lesson != selected:
            continue
        if obj["status"] == "complete":
            reproduce(root, lesson)
        elif obj["status"] == "in_progress":
            run(root, lesson)
    print("检查结束。尚未开始的项目未计为完成；统计质量由成果评价。")



RELEASE_URL = "ssh://git@hblu.top:2222/machine-learning-2026/course-student-release-2026.git"
# This release only adds lesson09; do not sync later or existing lesson packages.
LESSON09_SHARED = (
    "mlcourse/__init__.py", "mlcourse/bike_starter.py",
    "mlcourse/bike_models09.py", "mlcourse/lesson_io.py",
    "data/bike/hour.csv", "data/bike/LICENSE_AND_SOURCE.md", "data/bike/Readme.txt",
)


def sync(root: Path) -> None:
    """Add missing lesson09/support files, preserving existing student content."""
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=root)

    manifest_path = inside(root, "active_lessons.json")
    if (root / "active_lessons.json").is_symlink():
        raise ValueError("active_lessons.json须为本地普通文件")
    config = json.loads(manifest_path.read_text(encoding="utf-8"))
    current = active_lessons(root)  # Validate before changing any content.
    if "course-release" not in git("remote").decode().splitlines():
        git("remote", "add", "course-release", RELEASE_URL)
    git("fetch", "course-release", "main")
    ref = "course-release/main"
    lesson = root / "lesson-09"
    prefixes = list(LESSON09_SHARED)
    if not lesson.exists() and not lesson.is_symlink():
        entry = git("ls-tree", ref, "--", "lesson-09").decode()
        if not entry.startswith("040000 tree "):
            raise ValueError("发布仓库尚未提供第09课")
        prefixes.insert(0, "lesson-09")
    else:
        print("已存在，跳过整个lesson-09；不替换代码、报告或结果。")
    pending = []
    for entry in git("ls-tree", "-r", ref, "--", *prefixes).decode().splitlines():
        metadata, relative = entry.split("\t", 1)
        mode, kind, _ = metadata.split()
        target = root / relative
        if target.exists() or target.is_symlink():
            continue
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"发布内容须为普通文件：{relative}")
        target = inside(root, relative)
        pending.append((target, git("show", f"{ref}:{relative}")))
    for target, content in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(content)
    registered = False
    if lesson.is_dir() and not lesson.is_symlink() and "lesson-09" not in current:
        config["active_student_lessons"].append("lesson-09")
        manifest_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        registered = True
    print(f"已补齐{len(pending)}个缺失文件；" + ("已登记第09课。" if registered else "课次清单无需改变。"))
    print("已有内容保持不变。请用git status与git diff查看；不会自动提交或推送。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "run", "check", "sync", "ci"])
    parser.add_argument("lesson", nargs="?")
    args = parser.parse_args()
    try:
        if args.action == "sync":
            sync(ROOT)
        elif args.action == "ci":
            ci(ROOT, os.getenv("GITHUB_REF", ""))
        else:
            if args.lesson is None:
                parser.error("请填写课次，如：python scripts/course.py run 03")
            name = lesson_name(args.lesson)
            {"start": start, "run": run, "check": check}[args.action](ROOT, name)
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"检查未通过：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

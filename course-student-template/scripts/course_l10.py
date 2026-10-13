"""Independent missing-only lesson10 updater; never replaces an old course.py."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RELEASE_URL = "ssh://git@hblu.top:2222/machine-learning-2026/course-student-release-2026.git"
LESSON10_SHARED = (
    "scripts/course_l10.py", "mlcourse/__init__.py", "mlcourse/sms_course.py",
    "data/sms/train.csv", "data/sms/dev.csv", "data/sms/split_manifest.csv",
    "data/sms/provenance.json", "data/sms/DATA.md",
)


def inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip() or Path(relative).is_absolute():
        raise ValueError("同步文件须使用非空仓库相对路径")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"路径超出仓库：{relative}")
    return path


def active_lessons(root: Path) -> list[str]:
    value = json.loads((root / "active_lessons.json").read_text(encoding="utf-8"))
    lessons = value.get("active_student_lessons") if isinstance(value, dict) else None
    if not isinstance(lessons, list) or not lessons or lessons != list(dict.fromkeys(lessons)):
        raise ValueError("active_lessons.json须列出不重复的活跃课次")
    allowed = {f"lesson-{n:02d}" for n in range(1, 33)}
    if any(not isinstance(name, str) or name not in allowed for name in lessons):
        raise ValueError("活跃课次应使用lesson-NN格式")
    return lessons


def sync(root: Path) -> None:
    selected = "lesson-10"
    """Add one missing lesson/support set, preserving existing student content."""

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
    lesson = root / selected
    shared = LESSON10_SHARED
    prefixes = list(shared)
    if not lesson.exists() and not lesson.is_symlink():
        entry = git("ls-tree", ref, "--", selected).decode()
        if not entry.startswith("040000 tree "):
            raise ValueError(f"发布仓库尚未提供{selected}")
        prefixes.insert(0, selected)
    else:
        print(f"已存在，跳过整个{selected}；不替换代码、报告或结果。")
    source_files = {}
    for entry in git("ls-tree", "-r", ref, "--", *prefixes).decode().splitlines():
        metadata, relative = entry.split("\t", 1)
        mode, kind, _ = metadata.split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"发布内容须为普通文件：{relative}")
        inside(root, relative)  # Validate all paths before adding any content.
        source_files[relative] = git("show", f"{ref}:{relative}")
    if selected == "lesson-10":
        missing = [relative for relative in shared if relative not in source_files]
        if missing:
            raise ValueError("发布仓库第10课支持文件不完整：" + ", ".join(missing))
        # A different same-named module must never silently run the new lesson.
        for relative in ("scripts/course_l10.py", "mlcourse/__init__.py", "mlcourse/sms_course.py"):
            target = root / relative
            if target.exists() or target.is_symlink():
                if target.is_symlink() or not target.is_file() or target.read_bytes() != source_files[relative]:
                    raise ValueError(f"已有共享代码与第10课发布版本不同，无法确认兼容：{relative}；未覆盖、未新增，请保留本地版本并核对兼容性")
        source_meta = json.loads(source_files["data/sms/provenance.json"])
        expected = source_meta.get("file_sha256") if isinstance(source_meta, dict) else None
        if not isinstance(expected, dict):
            raise ValueError("发布第10课来源清单缺少file_sha256对象")
        data_names = ("data/sms/train.csv", "data/sms/dev.csv", "data/sms/split_manifest.csv")
        for relative in data_names:
            key = "course-student-template/" + relative
            if expected.get(key) != hashlib.sha256(source_files[relative]).hexdigest():
                raise ValueError(f"发布第10课数据哈希与来源清单不符：{relative}")
            target = root / relative
            if target.exists() or target.is_symlink():
                if target.is_symlink() or not target.is_file() or target.read_bytes() != source_files[relative]:
                    raise ValueError(f"已有第10课数据与发布字节不同：{relative}；未覆盖、未新增")
        local_meta = root / "data/sms/provenance.json"
        if local_meta.exists() or local_meta.is_symlink():
            if local_meta.is_symlink() or not local_meta.is_file():
                raise ValueError("已有第10课来源清单须为普通文件；未覆盖、未新增")
            local_value = json.loads(local_meta.read_text(encoding="utf-8"))
            local_hashes = local_value.get("file_sha256") if isinstance(local_value, dict) else None
            if not isinstance(local_hashes, dict):
                raise ValueError("已有第10课来源清单缺少file_sha256对象；未覆盖、未新增")
            if any(local_hashes.get("course-student-template/" + p) != expected.get("course-student-template/" + p) for p in data_names):
                raise ValueError("已有第10课来源清单的数据哈希不兼容；未覆盖、未新增")
    pending = []
    for relative, content in source_files.items():
        target = root / relative
        if target.exists() or target.is_symlink():
            continue
        target = inside(root, relative)
        pending.append((target, content))
    for target, _ in pending:
        parent = target.parent
        while parent != root.resolve():
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"新增文件的上级路径不是目录：{parent}；未新增")
            parent = parent.parent
    for target, content in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(content)
    registered = False
    if lesson.is_dir() and not lesson.is_symlink() and selected not in current:
        config["active_student_lessons"].append(selected)
        manifest_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        registered = True
    print(f"已补齐{len(pending)}个缺失文件；" + (f"已登记{selected}。" if registered else "课次清单无需改变。"))
    print("已有内容保持不变。请用git status与git diff查看；不会自动提交或推送。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["sync"])
    parser.add_argument("--destination", type=Path, default=ROOT,
                        help="existing student repository; defaults to this script's student root")
    args = parser.parse_args()
    try:
        sync(args.destination.resolve())
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"第10课同步未通过：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

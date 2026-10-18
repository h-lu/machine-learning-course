"""Independent missing-only lesson11 updater; never replaces an old course.py."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RELEASE_URL = "ssh://git@hblu.top:2222/machine-learning-2026/course-student-release-2026.git"
LESSON11_SHARED = (
    "scripts/course_l11.py", "docs/LESSON11_UPDATE.md", "mlcourse/__init__.py",
    "mlcourse/sms_course.py", "mlcourse/text_representations.py",
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


EXACT_SHARED = (
    "scripts/course_l11.py", "mlcourse/__init__.py", "mlcourse/sms_course.py",
    "mlcourse/text_representations.py", "data/sms/train.csv", "data/sms/dev.csv",
    "data/sms/split_manifest.csv", "data/sms/provenance.json",
)
LESSON11_REQUIRED = (
    "lesson-11/analysis.py", "lesson-11/config.json", "lesson-11/contract.json",
    "lesson-11/submission.json", "lesson-11/README.md", "lesson-11/LEARN.md",
)



def _plain_target(root: Path, relative: str) -> Path:
    """Reject symlinks anywhere along a destination before considering a write."""
    target = root / relative
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"同步路径包含符号链接：{relative}；已有内容保持不变")
    checked = inside(root, relative)
    if checked.exists() and not checked.is_file():
        raise ValueError(f"共享文件路径不是普通文件：{relative}")
    parent = checked.parent
    while parent != root:
        if parent.exists() and not parent.is_dir():
            raise ValueError(f"新增文件的上级路径不是目录：{relative}")
        parent = parent.parent
    return checked


def sync(root: Path) -> None:
    """Only add lesson11 and explicitly required missing files; never replace work."""
    root = root.resolve()

    def _git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=root)

    top = Path(_git("rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != root:
        raise ValueError("同步目标须为已有学生Git仓库的根目录")
    manifest_path = _plain_target(root, "active_lessons.json")
    config = json.loads(manifest_path.read_text(encoding="utf-8"))
    current = active_lessons(root)
    remote = "course-release"
    if remote not in _git("remote").decode().splitlines():
        _git("remote", "add", remote, RELEASE_URL)
    _git("fetch", remote, "main")
    source_ref = _git("rev-parse", f"{remote}/main").decode().strip()
    selected = "lesson-11"
    tree = _git("ls-tree", source_ref, "--", selected).decode()
    if not tree.startswith("040000 tree "):
        raise ValueError("发布仓库尚未提供第11课；未新增课包")
    lesson = root / selected
    if lesson.is_symlink() or (lesson.exists() and not lesson.is_dir()):
        raise ValueError("已有lesson-11不是普通目录；未新增、未覆盖")
    include_lesson = not lesson.exists()
    prefixes = [selected, *LESSON11_SHARED]
    source_files: dict[str, bytes] = {}
    for entry in _git("ls-tree", "-r", source_ref, "--", *prefixes).decode().splitlines():
        metadata, relative = entry.split("\t", 1)
        mode, kind, _ = metadata.split()
        if relative not in LESSON11_SHARED and not relative.startswith(selected + "/"):
            raise ValueError(f"发布路径超出第11课范围：{relative}")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"发布文件须为普通文件：{relative}")
        # An existing lesson is skipped as a whole, even if it is incomplete.
        if include_lesson or not relative.startswith(selected + "/"):
            _plain_target(root, relative)
        source_files[relative] = _git("show", f"{source_ref}:{relative}")
    required = (*LESSON11_SHARED, *LESSON11_REQUIRED)
    missing = [name for name in required if name not in source_files]
    if missing:
        raise ValueError("发布仓库第11课依赖不完整：" + ", ".join(missing))
    for relative in EXACT_SHARED:
        target = _plain_target(root, relative)
        if target.exists() and target.read_bytes() != source_files[relative]:
            raise ValueError(f"已有共享代码或固定数据与发布字节不同：{relative}；未新增、未覆盖，请保留个人版本并先核对兼容性")
    source_meta = json.loads(source_files["data/sms/provenance.json"])
    hashes = source_meta.get("file_sha256") if isinstance(source_meta, dict) else None
    if not isinstance(hashes, dict):
        raise ValueError("发布SMS来源清单缺少file_sha256；未新增")
    for relative in ("data/sms/train.csv", "data/sms/dev.csv", "data/sms/split_manifest.csv"):
        key = "course-student-template/" + relative
        if hashes.get(key) != hashlib.sha256(source_files[relative]).hexdigest():
            raise ValueError(f"发布SMS数据与固定来源清单不符：{relative}；未新增")
    pending: list[tuple[Path, bytes]] = []
    for relative, content in source_files.items():
        if relative.startswith(selected + "/") and not include_lesson:
            continue
        target = _plain_target(root, relative)
        if not target.exists():
            pending.append((target, content))
    for target, content in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(content)
    if selected not in current:
        config["active_student_lessons"].append(selected)
        manifest_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("已在active_student_lessons末尾登记lesson-11；其他清单字段和旧课次顺序保持不变。")
    print(f"已补齐{len(pending)}个第11课缺失文件；已有课目录、旧脚本、工作流和结果未覆盖。")
    if not include_lesson:
        print("已存在，跳过整个lesson-11；未用发布文件填补或替换个人课目录。")
    print("查看git status与git diff后，按原提交流程自行提交；本助手不会提交、推送或开放测验场次。")


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
        print(f"第11课同步未通过：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

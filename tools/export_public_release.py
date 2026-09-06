"""Export the author's public course release without nested Git databases or local archives."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists() and any(target.iterdir()):
        parser.error("输出应为新建空目录，避免覆盖已有文件。")
    target.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".venv", "artifacts", "build", "*.egg-info")
    for name in ["machine-learning-course", "course-student-template", "course-instructor", "ml-check", "tools"]:
        shutil.copytree(ROOT / name, target / name, ignore=ignore)
    for name in ["README.md", "AGENTS.md", "REDESIGN_NOTES.md", "PUBLISHING.md"]:
        shutil.copy2(ROOT / name, target / name)
    # These are historical measurements, not evidence that GitHub or Gitea runs a service.
    for name in ["latest.json", "clean_environment.json"]:
        data = (ROOT / "validation" / name).read_text(encoding="utf-8")
        (target / "validation").mkdir(exist_ok=True)
        (target / "validation" / name).write_text(data.replace(str(ROOT), "."), encoding="utf-8")
    archive = target / "archives/2026-09-06-before-redesign"
    archive.mkdir(parents=True)
    for name in ["repositories.json", "SHA256SUMS"]:
        shutil.copy2(ROOT / "archives/2026-09-06-before-redesign" / name, archive / name)
    (archive / "README.md").write_text(
        "# 重建前归档说明\n\n2026-09-06 重建前的完整工作区与四个 Git 历史已经在作者本机归档，"
        "压缩包逐文件校验了 2,439 个普通文件。旧稿不作为现行教材。\n\n"
        "本公开仓库提供当前完整课程和归档提交编号，不包含本机旧稿副本、压缩包或 Git 对象数据库。"
        "`SHA256SUMS` 记录本机压缩包摘要；压缩包不在本公开仓库中，不能在这里执行对应校验命令。\n\n"
        "归档版本见 [repositories.json](repositories.json)。Gitea 的独立仓库保留原有提交历史及归档标签。\n",
        encoding="utf-8",
    )
    (target / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n.venv/\n**/artifacts/\n.publish/\nbuild/\n*.egg-info/\n", encoding="utf-8")
    forbidden = []
    for p in target.rglob("*"):
        if p.name == ".git" or p.suffix in (".sqlite", ".db", ".pem", ".key") or p.name == ".env":
            forbidden.append(str(p.relative_to(target)))
    if forbidden:
        raise RuntimeError(f"导出包含非课程文件：{forbidden}")
    print(json.dumps({"output": str(target), "files": sum(p.is_file() for p in target.rglob('*')), "teacher_materials": "included by author request", "nested_git": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()

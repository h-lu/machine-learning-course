"""Run trusted authoring checks; never point this at arbitrary student submissions."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    py = sys.executable
    commands = [
        ("题库同步", ROOT, [py, "tools/sync_question_bank.py"]),
        ("学生实验测试", ROOT / "course-student-template", [py, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        ("32课教师参考覆盖", ROOT / "course-instructor", [py, "scripts/validate_reference_coverage.py"]),
        ("检查器与API测试", ROOT / "ml-check", [py, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ]
    for profile, repo in [("student", "course-student-template"), ("instructor", "course-instructor"), ("planning", "machine-learning-course")]:
        commands.append((f"{profile}严格检查", ROOT / "ml-check", [py, "-m", "ml_check", "--repo", str(ROOT / repo), "--profile", profile, "--strict", "--json"]))
    results = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    for name, cwd, command in commands:
        print(f"正在验证：{name}", flush=True)
        started = time.monotonic()
        try:
            run = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=300)
            item = dict(name=name, exit_code=run.returncode, seconds=round(time.monotonic() - started, 3), output=run.stdout + run.stderr)
        except subprocess.TimeoutExpired:
            item = dict(name=name, exit_code=124, seconds=300, output="超过五分钟，验证未完成。")
        results.append(item)
        print(f"{name}：{'通过' if item['exit_code'] == 0 else '失败'}（{item['seconds']} 秒）", flush=True)
        if item["exit_code"]:
            print(item["output"][-18000:], flush=True)
    target = ROOT / "validation/latest.json"
    target.parent.mkdir(exist_ok=True)
    data = dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(), python=sys.version, executable=py,
                platform=platform.platform(), cpu_threads=os.cpu_count(), notes="作者本机；限制数值库为单线程。不是普通学生电脑试教，也未执行未知学生代码。", checks=results)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return int(any(item["exit_code"] for item in results))


if __name__ == "__main__":
    raise SystemExit(main())

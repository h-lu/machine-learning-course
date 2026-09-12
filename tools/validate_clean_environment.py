"""Re-run trusted course sources in an isolated, pre-provisioned Python environment."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 31)]


def main():
    parser = argparse.ArgumentParser(description="用已安装NumPy的独立Python环境重跑32课。安装不计入课堂实验时间。")
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    # Keep the venv executable path: resolving its symlink would select the base interpreter.
    py = str(args.python.absolute())
    environment = json.loads(subprocess.check_output([py, "-c", "import sys,numpy,json; print(json.dumps(dict(python=sys.version,prefix=sys.prefix,base_prefix=sys.base_prefix,numpy=numpy.__version__,numpy_path=numpy.__file__)))"], text=True))
    if environment["prefix"] == environment["base_prefix"] or not Path(environment["numpy_path"]).is_relative_to(environment["prefix"]):
        parser.error("请选择NumPy安装在其中的独立虚拟环境，不能借用系统site-packages。")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONNOUSERSITE="1")
    records = []
    with tempfile.TemporaryDirectory(prefix="ml-course-source-") as tmp:
        copy = Path(tmp)
        for name in ["course-student-template", "course-instructor", "machine-learning-course", "ml-check", "tools"]:
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".venv", "artifacts", "build", "*.egg-info"))
        student = copy / "course-student-template"
        assert not list(student.glob("lesson-*/artifacts/summary.json"))
        for lesson in LESSONS:
            number = int(lesson[1:]) if lesson.startswith("C") else int(lesson[1:]) + 2
            folder = f"lesson-{number:02d}"
            cmd = [py, f"{folder}/analysis.py"]
            usage = copy / "process-usage.txt"
            measured = Path("/usr/bin/time").exists()
            if measured:
                cmd = ["/usr/bin/time", "-f", "%M", "-o", str(usage), *cmd]
            start = time.monotonic()
            proc = subprocess.run(cmd, cwd=student, env=env, capture_output=True, text=True, timeout=180)
            seconds = time.monotonic() - start
            record = dict(lesson=lesson, exit_code=proc.returncode, seconds=round(seconds, 4), max_rss_kib=int(usage.read_text().strip()) if measured and proc.returncode == 0 else None)
            if proc.returncode:
                record["output"] = proc.stdout + proc.stderr
            else:
                result = json.loads((student / folder / "artifacts/summary.json").read_text())
                record["result_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                record["metrics"] = result["metrics"]
                record["input_hash"] = result["provenance"]["data_sha256"]
                if record["max_rss_kib"] and record["max_rss_kib"] > 8 * 1024 * 1024:
                    record["exit_code"] = 1
                    record["output"] = "峰值内存超过8GiB目标。"
            records.append(record)
            print(f"{lesson}: {'通过' if not record['exit_code'] else '失败'}，{seconds:.3f}秒", flush=True)
        check = subprocess.run([py, "tools/validate_course.py"], cwd=copy, env=env, text=True, capture_output=True, timeout=300)
        suite = json.loads((copy / "validation/latest.json").read_text()) if (copy / "validation/latest.json").exists() else {"output": check.stdout + check.stderr}
    inventory = {}
    for name in ["course-student-template", "course-instructor", "machine-learning-course", "ml-check", "tools"]:
        for p in (ROOT / name).rglob("*"):
            if p.is_file() and not any(x in (".git", "__pycache__", ".pytest_cache", ".venv", "artifacts") for x in p.parts):
                inventory[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    result = dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(), environment=environment,
                  notes="独立venv；NumPy从预先下载的wheel离线安装；新源码副本不含Git、缓存和旧产物；数值库单线程。未模拟8GB机器或禁用操作系统网络。",
                  lesson_runs=records, maximum_seconds=max(x["seconds"] for x in records), total_lesson_seconds=round(sum(x["seconds"] for x in records), 4),
                  suite_exit_code=check.returncode, suite=suite, source_sha256=hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest())
    target = ROOT / "validation/clean_environment.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return int(check.returncode != 0 or any(x["exit_code"] for x in records))


if __name__ == "__main__":
    raise SystemExit(main())

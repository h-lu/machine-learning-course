"""Run active real-data packages in a disposable source copy.
Uses an already provisioned Python/NumPy interpreter; installs nothing and
reports its actual environment rather than assuming students share it.
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "validation/clean_environment.json")
    args = parser.parse_args()
    py = str(args.python.absolute())
    probe = "import sys,numpy,json; print(json.dumps(dict(python=sys.version,prefix=sys.prefix,base_prefix=sys.base_prefix,numpy=numpy.__version__,numpy_path=numpy.__file__)))"
    environment = json.loads(subprocess.check_output([py, "-c", probe], text=True))
    environment["independent_virtual_environment"] = environment["prefix"] != environment["base_prefix"]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONNOUSERSITE="1")
    with tempfile.TemporaryDirectory(prefix="ml-redesign-clean-source-") as tmp:
        copy = Path(tmp)
        ignore = shutil.ignore_patterns(".git", "archives", "__pycache__", ".pytest_cache", ".venv", "artifacts", "build", "*.egg-info")
        for name in ["course-student-template", "course-instructor", "machine-learning-course", "ml-check", "tools"]:
            shutil.copytree(ROOT / name, copy / name, ignore=ignore)
        shutil.copy2(ROOT / "active_lessons.json", copy / "active_lessons.json")
        validator = copy / "tools/validate_redesign.py"
        if not validator.is_file():
            parser.error("新版真实数据验收入口 tools/validate_redesign.py 尚未提供")
        output = copy / "redesign-result.json"
        run = subprocess.run([py, str(validator), "--output", str(output)], cwd=copy, env=env, capture_output=True, text=True, timeout=300)
        evidence = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else None
    data = dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=environment,
                notes="一次性源码副本；不含旧课归档、Git、缓存与旧产物；使用预配置解释器，未安装依赖。未模拟学生电脑或禁用操作系统网络。",
                exit_code=run.returncode,evidence=evidence,output=run.stdout+run.stderr)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(exit_code=run.returncode,report=str(args.output),environment=environment),ensure_ascii=False))
    return run.returncode
if __name__ == "__main__":
    raise SystemExit(main())

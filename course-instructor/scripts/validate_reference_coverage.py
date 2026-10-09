"""Validate new active references through the real-data redesign validator.
The old 32-lesson config_patch/shared-toy validator is archived and cannot
certify rewritten 01–08 real-data packages.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    active = json.loads((ROOT / "active_lessons.json").read_text(encoding="utf-8"))["active_instructor_lessons"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson", choices=active)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    validator = ROOT.parent / "tools/validate_redesign.py"
    if not validator.is_file():
        parser.error("新版科学数据参考验证入口尚未提供；旧toy参考不能用于验收新课")
    command = [sys.executable, str(validator), "--references-only"]
    if args.lesson:
        command.extend(["--lesson", args.lesson])
    if args.output:
        command.extend(["--output", str(args.output.absolute())])
    return subprocess.run(command, cwd=ROOT.parent, check=False).returncode
if __name__ == "__main__":
    raise SystemExit(main())

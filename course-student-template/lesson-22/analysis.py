"""第 22 课：调用本地工具并核对参数与返回值。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.workflow import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

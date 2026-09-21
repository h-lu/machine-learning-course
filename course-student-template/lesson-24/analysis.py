"""第 24 课：把资料文字与系统权限分开。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.workflow import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

"""第 31 课：换一个场景，原来的方案还能用吗。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.operations import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

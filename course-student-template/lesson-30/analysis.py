"""第 30 课：更高效果值得多少等待和计算。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.operations import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

"""第 32 课：怎样交付作品，并说明下一轮该学什么。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.operations import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

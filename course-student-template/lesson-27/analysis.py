"""第 27 课：反馈怎样帮助学习，又会遗漏什么。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.operations import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

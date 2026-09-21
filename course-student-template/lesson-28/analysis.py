"""第 28 课：一个好分数会不会鼓励错误行为。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.operations import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

"""第 26 课：比较原流程与一个有依据的改进。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.workflow import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

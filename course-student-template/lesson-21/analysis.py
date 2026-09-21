"""第 21 课：把请求拆成可核对的多步流程。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.workflow import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

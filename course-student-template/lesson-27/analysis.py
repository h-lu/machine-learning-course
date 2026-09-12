"""本课可替换的起步入口；默认输出仅为示例实验。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.runtime import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

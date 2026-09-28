"""第 06 课的程序入口：读取本课数据和配置，生成供比较的结果。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.runtime import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)

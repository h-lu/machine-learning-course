"""开放起点：只准备数据；在这里或自己的文件构建研究。"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mlcourse.bike_starter import main
if __name__ == "__main__":
    main(Path(__file__).resolve().parent, 4)
# 可修改本文件，或另写my_analysis.py；自己定义问题/比较/保存证据。

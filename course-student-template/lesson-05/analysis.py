"""起点代码：读取数据并检查文件；在这里或自己的程序中继续分析。"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mlcourse.bike_starter import main
if __name__ == "__main__":
    main(Path(__file__).resolve().parent, 5)
# 可修改本文件，或另写 my_analysis.py；自行定义问题、比较方案并保存结果。

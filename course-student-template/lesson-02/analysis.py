"""第02课可编辑数据起点；默认不完成正式项目。"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import main
# 可扩写本文件或另写脚本；load_development/mae/fit_simple_line/write_csv只帮助读取与核算。
# 模型、输入、评价与检查由你决定，保存实际逐条证据；不能只提交起点。
if __name__ == "__main__":
    main(Path(__file__).resolve().parent, 2)

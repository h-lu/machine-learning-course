# 环境准备

课前需要 Python 3.10 或更高版本，以及 NumPy。先在学生仓库根目录打开终端，检查已经准备好的环境：

```bash
python3 --version
python3 -c "import numpy; print(numpy.__version__)"
python3 lesson-01/analysis.py
```

打开 `lesson-01/artifacts/summary.json`，对照第 1 课学习卡核对一条计算。这个文件是程序输出，可以删除后重跑；你写的分析应放在 `report.md`，不要混进程序生成文件。

如果课前尚未安装依赖，可以在联网时建立环境：

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
```

没有网络的课堂由教师预先提供适配操作系统和 Python 版本的安装包，或提前配好环境。课堂实验本身读取仓库内的数据，不需要网络。

修改之前，先在 `contract.json` 写下问题、使用者和预计结果。选好一项改动后，把原参数复制到另一份文件，便于比较。所有运行命令从学生仓库根目录执行。

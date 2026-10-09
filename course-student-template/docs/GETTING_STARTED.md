# 环境准备

课前需要 Python 3.10 或更高版本，以及 NumPy。完整目录和启动命令见[环境说明](../ENVIRONMENT.md)。下面以 `python3` 为例；若教师准备的环境用 `python` 或 `py`，替换命令开头即可。在学生仓库根目录打开终端，检查已经准备好的环境：

```bash
python3 --version
python3 -c "import numpy; print(numpy.__version__)"
python3 lesson-01/analysis.py
```

打开 `lesson-01/artifacts/starter/summary.json`，核对准备好的训练、验证记录数；再打开同目录的 `sample.csv`，对照第1课学习页理解一条记录。默认程序只准备数据，不代表已经完成研究。自己的分析写入 `lesson-01/report.md`，程序生成文件用于保存实际运行证据。

如果课前尚未安装依赖，可以在联网时建立环境。以下激活命令适用于 Linux/macOS 的终端；Windows 使用教师提供的激活方式：

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
```

没有网络的课堂由教师预先提供适配操作系统和 Python 版本的安装包，或提前配好环境。课堂实验本身读取仓库内的数据，不需要网络。

修改之前，先在 `contract.json` 写下问题、使用者和预计结果。选好一项改动后，把原参数复制到另一份文件，便于比较。所有运行命令从学生仓库根目录执行。

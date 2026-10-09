# 离线环境与第一次运行

先打开完整学生目录：应能看到 `scripts/`（运行与检查工具）、`mlcourse/`（共享代码）、`data/bike/`（真实数据）和 `lesson-01/` 至 `lesson-08/`（各课材料）。下文的“学生仓库根目录”就是同时包含这些目录的位置。只复制某一课的 `analysis.py` 会缺少共享代码和数据。数据随包提供，课堂无需下载。

需要已准备的Python3.10或以上与NumPy。不同电脑启动命令可能是python、python3或Windows的py；沿用教师已验证的环境。本机2026-10-09使用python3（Python3.14.4、NumPy2.5.2），没有python命令；本次没有安装软件。先在终端运行：

```bash
python3 --version
python3 -c "import numpy; print(numpy.__version__)"
```

若你的电脑使用python或py，把下面命令开头替换成该命令；不要在Python的>>>提示符输入这些终端命令。若未装NumPy，保留报错给教师处理，先做手算；不能将手算写成实验已运行。

所有课程命令从学生目录根运行。例如：

```bash
python3 lesson-01/analysis.py --config lesson-01/config.json --output lesson-01/artifacts/first
```

命令中的 `--config` 指定配置文件，`--output` 指定保存结果的目录。以 `lesson-01/` 开头的相对路径从学生仓库根目录查找；只写 `config.json` 则从本课目录查找。各课 `SUPPORT.md` 列出完整命令。成功后打开本课指定的 CSV/JSON 文件。CSV 以逗号分列，可用文本或表格软件查看；JSON 是带字段名的结构化记录，可用文本编辑器查看。

显式指定 `--output` 时，使用学生仓库内尚不存在的新目录，避免覆盖证据；再次运行可换成 `lesson-01/artifacts/first-2`。各课 `submission.json` 的 `run` 字段记录重新生成正式主结果的命令。如果改写了程序或结果路径，也要更新这份清单。自动复现检查在临时副本中重建清单列出的结果，具体见[提交流程](docs/WORKFLOW.md)；它不会替你运行所有候选或填写报告。

前1–7课不使用最后测试数据。第8课在验证前保存自己的实验计划，验证后保存选定方案；可以用文字记录。只有采用可选示例工具时，才需使用该工具规定的 JSON 格式。

找不到文件：核对当前目录及文件名，不追加.txt。配置格式错误：按报错行检查英文引号、逗号和数字。运行失败：保留命令与报错，旧输出不能冒充此次成功。普通CPU即可，代码不需要GPU或付费模型；AI辅导和线上概念检查的网络安排按教师通知，和离线计算分开。

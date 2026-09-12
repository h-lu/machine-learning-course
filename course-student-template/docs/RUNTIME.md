# 小实验的运行办法

在学生仓库根目录运行。需要 Python 3.10 以上和 NumPy；开课前安装依赖，课堂运行不联网。

```bash
python3 -m pip install -r requirements.txt
python3 lesson-09/analysis.py --output artifacts/S07-demo
python3 lesson-09/analysis.py --config lesson-09/config.json --data lesson-09/data/base.json --output artifacts/S07-trial
```

`--output` 是输出目录。程序在其中生成 `summary.json`；不传参数时写到本课 `artifacts/summary.json`。`--config` 和 `--data` 都接受一个 JSON 文件路径；相对路径从运行命令所在目录解释。默认读取本课 `config.json` 和 `data/base.json`。

每课起步实验已经能运行。它展示一种方法、产生实际数值并运行一种条件变化，不能代表学生已经完成任务。学生还要自行界定用途、设计对比和失败输入，并根据结果说明是否采用。你可以修改配置、换数据或重写 `analysis.py`；不要求使用起步程序中的模型、阈值或最终结论。

## 文件和输出

- `config.json`：本课可调整的参数。`seed` 控制随机数；其余参数随课次变化。修改前另存一份配置，便于比较。
- `data/base.json`：随仓库提供的小数据。`kind` 说明数据类型；`source` 说明数据如何生成及限制。具体字段见同目录 `DATA.md`。
- `analysis.py`：可替换的运行入口；`mlcourse/` 提供起步实现和基础计算。
- `artifacts/summary.json`：机器可读的实际结果，包括 `lesson`、`status`、`data`、`config`、`metrics`、`comparison`、`stress_test`、`details` 和 `provenance`。默认 `status` 是 `example_only`，不替学生填写采用决定。

`metrics` 是本次结果；`comparison` 是一个起步对比；`stress_test` 是已运行的条件变化，包含改了什么及结果；`details` 保存检查数值所需的预测、计数、曲线或轨迹。不要把起步测试直接当作自己的失败案例。

如果你选择继续使用 `summary.json`，建议保留课次编号 `lesson`、说明运行性质的 `status`、数据来源 `data`、数值结果 `metrics`、实际运行的失败或条件变化 `stress_test`、追溯信息 `provenance`，便于比较。你也可以改用 CSV、图表和其他报告格式，并在提交说明中指出运行入口与产物。检查工具不依据模型名称、阈值或结论判分。

本工具的 JSON 不写入 NaN 或 Infinity；暂时没有定义的指标用 null，并解释原因。`provenance` 记录输入内容、配置和执行源码的哈希。命令行运行还记录输入文件原始字节与本课入口文件的哈希；它们能发现文件变化，不能证明数据来源真实。

起步入口调用 `mlcourse/experiments.py` 中与课次编号对应的函数（例如 S07 对应 `s07`）。基础算法在 `mlcourse/mathops.py`。可以从这里阅读计算过程，也可以将自己的方法直接写入本课 `analysis.py`，或使用其他入口并在提交说明中注明。

## 验证与限制

```bash
python3 -m unittest discover -s tests -v
```

这些测试用于确认发布的起步工具计算和输入处理正常；你替换方法后，可以为新方法设计相应检查。它不评价你的任务是否值得做，也不证明模型可在现实中上线。数据均为本课程生成的教学数据，不代表真实人口、机构或线上业务。普通 CPU 上每课目标三分钟内；从头重跑目标五分钟内。没有 GPU、付费 API 或课堂下载模型的要求。

神经网络课使用小型 NumPy 实现；表示、语言模型和问答课会明确区分人工生成表示、微型模型、固定候选输出与真实预训练模型。使用缓存只能评价已有候选，不能据此声称测试了未运行的提示或新模型。

要检查教学数据如何生成，可读 `scripts/build_example_data.py`。以下命令在一个新的空目录重建示例，不覆盖当前课次的修改：

```bash
python3 scripts/build_example_data.py --output /tmp/ml-example-data
```

这个目录包含重建的数据、配置和入口样例；运行仍需完整学生仓库中的 `mlcourse/`，它不是独立安装包。

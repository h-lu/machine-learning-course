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

## C01–C02 入门案例

C01–C02 使用 `mlcourse/intro.py` 中的取餐等待时间案例，公共运行入口和文件名不变。C01 的规则参数人为设定；C02 的均值基线与一元线性回归只使用训练集，默认在验证集上评价。只有 C02 接受 `--split validation` 或 `--split test`，也可在配置中选择；测试集不用于选择方案。

两课额外生成 `predictions.csv`，逐条保存特征、真实值、预测值与绝对误差。默认提交清单列出 JSON 和 CSV，当前配置与清单命令应能重新生成主要结果。模型的主要数值显示在 `summary.json`，学习所需术语见 [术语表](TERMINOLOGY.md)。

## S01–S06 的结果表

`lesson-03` 至 `lesson-08` 对应问题与评价模块。默认输出为 `summary.json`、`comparison.csv` 和 `records.csv`；S05 另有 `added_samples.csv`。终端显示方法名、单位与分母，JSON 保留模型参数、样本编号和分组检查。具体字段见各课 `data/DATA.md`。

S01、S03–S06 支持 `--split validation` 或 `--split test`，只改变评价部分，模型和预处理仍只从训练数据学习。S03 先保留原测试编号，再在开发部分比较划分；不同划分评价的对象不同。S02 没有这个选项，用 `observation_day` 控制可见标签。

每次修改配置或数据后使用新的 `--output` 目录，不复用旧输出充当新实验。默认结构中的 `metrics` 是为兼容工具保留的主方案指标，不是程序的采用建议。逐条表是长表：同一个样本在不同方法下各占一行。空白/`null` 表示未知或未定义，不表示零。

输入、代码和配置哈希帮助复核文件变化，不证明数据真实。本模块的代理标签、采集池与合成标签都有明确模拟来源；数据生成和使用步骤见 [模块说明](FOUNDATIONS.md)。

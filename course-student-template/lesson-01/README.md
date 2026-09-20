# 第 01 课（C01）：从一行数据得到第一个预测

## 本课要解决什么问题

你准备在食堂排队，想知道大约还要等几分钟。本课先做一个很小的作品：输入“前面有几个人”，程序用一条人工写定的规则计算预计等待时间，再和已经发生的一次真实等待记录核对。

本课只要求跑通“数据 → 预测 → 核对 → 保存”的完整流程。它不训练机器学习模型，也不能证明真实食堂应该使用这条规则。第一次操作时，请直接按 [入门支持](SUPPORT.md) 完成；第一项任务只需手算一条记录。

遇到程序错误时，保留完整报错和已经生成的文件。暂时不能运行，可以先完成手算并在报告中写“尚未运行”，修复后再补跑。

## 本课要学会什么

| 概念 | 学完后你能做什么 |
|---|---|
| 样本（sample）与数据集（dataset） | 说明一行数据代表一次排队经历，多行组成数据集 |
| 特征（feature）与标签（label / target） | 区分预测时知道的前面人数和事后才知道的实际等待时间 |
| 回归（regression）与预测值（prediction） | 知道预测分钟数属于数值预测，并能核对一条计算 |
| 参数（parameter）与训练 | 区分“人写定规则参数”和“程序从数据中学习参数” |
| 可复现性与输入检查 | 保存数据、配置、命令和结果，并判断新输入能说明什么 |

这些词在 [LEARN.md](LEARN.md) 中都有数字例子。本课不要求推导算法，也不要求先会 JSON。

## 90 分钟安排

- 0–15 分钟：读一行数据，区分特征、标签和预测值。
- 15–30 分钟：运行给定程序，打开 `predictions.csv` 核对 `train-03`。
- 30–50 分钟：只改规则斜率，先预计再运行对照。
- 50–65 分钟：选择一个新人数，解释有标签和无标签的区别。
- 65–78 分钟：完成报告、任务说明和文件检查。
- 78–90 分钟：按教师通知完成概念检查。

## 完成步骤

所有命令都在学生仓库根目录运行，也就是能同时看到 `scripts`、`lesson-01` 和 `mlcourse` 的文件夹。下面写 `python`；电脑提示找不到该命令时，整套命令统一改用 `python3`。

### 1. 先写一句任务和一个预计

打开 `lesson-01/report.md`。写清楚谁会看预测、输入是什么、输出是什么；再写下运行前预计：前面 2 人时，规则会预测几分钟。

人工规则是：

```text
预测分钟数 = 1 + 2 × 前面人数
```

因此 `train-03` 的输入是 2 人，先在纸上计算预测值。不要先抄程序答案。

### 2. 运行给定起点

```bash
python scripts/course.py start 01
python scripts/course.py run 01
```

第一条只记录本课开始；第二条读取 `lesson-01/data/base.json` 和 `lesson-01/config.json`，生成：

- `lesson-01/artifacts/predictions.csv`：逐条输入、实际值、预测和误差；
- `lesson-01/artifacts/summary.json`：本次配置、汇总和新输入检查。

终端显示“结果写入”后，先打开 `predictions.csv`。找 `id=train-03`，核对 `queue_length=2`、`actual=4`、`prediction_rule=5`、`absolute_error_rule=1`。单位分别是人和分钟。

再回到 `data/base.json` 看同一行的 `staff_count`、`service_mode` 和 `rain`。这些是现场背景信息，默认规则没有使用它们。写一句预计：如果两条记录人数相同但背景条件不同，只看人数可能漏掉什么。

### 3. 只改一个参数做对照

把 `config.json` 另存为 `lesson-01/config-trial.json`，使用下面的完整内容。这里仅把 `rule_slope` 从 2.0 改成 1.5：

```json
{
  "seed": 7,
  "rule_intercept": 1.0,
  "rule_slope": 1.5,
  "stress_queue": 10,
  "evaluation_split": "train"
}
```

`rule_intercept` 是固定加入的分钟数；`rule_slope` 是前面每增加 1 人，预测增加多少分钟。先在报告写预计，再运行：

```bash
python lesson-01/analysis.py --config lesson-01/config-trial.json --output lesson-01/artifacts/trial
```

打开 `trial/predictions.csv`，再次找 `train-03`。新预测应为 `1 + 1.5 × 2 = 4` 分钟。它在这一条记录上误差为 0，只说明这一条更接近，不能证明规则对所有情况都更好。

### 4. 检查一个自己选择的新输入

在 `config-trial.json` 中只改 `stress_queue`，例如改成 6。先写下为什么检查这个人数和预计预测，再用上一步相同命令重跑到 `artifacts/trial/`。

本数据记录的人数范围是 0–3。6 人可以代入规则，但没有对应的实际等待标签，因此只能说明“规则会预测多少”，不能计算误差，也不能判断可靠。结果中的 `null` 表示没有值，不是 0。

若想检查无效输入，可另存 `config-invalid.json`，把人数设为 -1，并使用新输出目录。程序明确报错就是输入检查结果；不要把旧结果当作这次成功输出。

### 5. 保存报告和提交文件

将最后保留的合法参数写入 `config.json`，再运行 `python scripts/course.py run 01`。填写 `contract.json` 的六项任务说明：问题、使用者、数据来源、指标、数据使用安排和运行前预计。确认结果确实来自本次运行后，再把 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py check 01
```

检查通过只表示文件齐全。提交时还要保存报告、配置和实际结果；具体 Git 命令见 [第一次运行指南](../docs/FIRST_RUN.md)。

## 必须提交什么

- 能重新运行的程序和最终 `config.json`；
- 已填写的 `contract.json` 和 `report.md`；
- `artifacts/summary.json` 与 `artifacts/predictions.csv`；
- 报告引用的 `config-trial.json` 和对应结果；
- 完整的 `submission.json`。

报告要写出一条预测的算式、一次只改一个参数的比较、一个新输入检查，以及当前证据不能证明什么。C01 不计平时分，但要完成这次入门流程。

## 不同起点怎么做

### 必做任务（Core）：跑通并核对一条预测

运行起点，核对 `train-03`，只改一个参数做对照，再检查一个新输入并保存证据。

### 入门支持（Support）：按 SUPPORT.md 完成

[SUPPORT.md](SUPPORT.md) 提供第一项手算、完整命令、第一份要看的文件和卡住时的处理方法。它是完成必做任务的一条路径，不需要再重复交一份 Core。

### 提高任务（Upgrade）：换一条有理由的规则

改变截距或斜率，并说明改变服务什么用途。仍需逐条检查，不按代码量或规则数量评价。

### 换数据重测（Transfer）：换一个数值预测情境

例如用距离预测配送分钟数。重新说明一行数据代表什么、特征和标签是什么、单位是什么，不能只替换字段名。

### 自选拓展（Open extension）：增加清楚的输入提示

为超出已知范围的输入增加提示，并用合法与非法输入各检查一次。不要把“程序能计算”写成“结果可靠”。

## 运行限制

需要 Python 3.10 以上、NumPy 和仓库内的 8 条人工数据。普通 CPU 即可，不需要显卡、付费 API 或联网下载模型。单次运行目标不超过 3 分钟。实验离线运行；AI 辅助和在线概念检查按教师安排使用网络。

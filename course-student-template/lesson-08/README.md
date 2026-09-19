# 第 08 课（S06）：一次小实验能否改变最初的问题

## 本课要解决什么问题

回到 S01 的任务：当前问题到底出在数据记录还是遗漏的特征？本课先写出两种可能解释，选择一次只改变一个因素的实验，再用同一批样本比较原方案和候选。

你将提交自己的任务说明、程序生成的比较表和逐条记录，以及解释选择的简短报告。AI 可以帮助提出方案、编程和解释，但不能用一段流畅说明代替实际比较。出错时按报错核对字段；不会操作文件时先查 [第一次运行指南](../docs/FIRST_RUN.md)，可以从原始小数据重新开始。

## 本课要学会什么

| 通用术语 | 学完后能做什么 |
|---|---|
| 假设与诊断 | 提出两种解释并选择有区分力的实验 |
| 控制变量 | 每次只改变一个重要因素 |
| 缺失值填补 | 只从训练集计算填补参数 |
| 预处理流水线 | 用一致的处理预测验证集和测试集 |
| 基于证据的修订 | 保留原方案与候选的比较，不编造成功 |

先读 [LEARN.md](LEARN.md) 的情境和小计算，陌生词再查 [术语表](../docs/TERMINOLOGY.md)。不要求预先会算法推导；本课读懂计算与比较，比背下英文名更重要。

## 90 分钟安排

20 分钟理解本课关系和一个小例子；35 分钟运行并构建自己的比较；20 分钟核对失败案例、保留证据和写建议；最后 15 分钟做 A/AI 学习/B 概念检查与提交。环境在课前准备，网络接入按教师安排。

## 完成步骤

### 1. 从用途开始，运行原始实验

在 `report.md` 先写使用者、用途和预计结果。在学生仓库根目录运行，也就是能看到 `scripts/` 与 `lesson-08/` 的目录。只识别 `python3` 的电脑，把命令中的 `python` 换为 `python3`。

```bash
python scripts/course.py start 08
python lesson-08/analysis.py --output lesson-08/artifacts/original
```

程序读取本课 `data/base.json` 和 `config.json`。先看终端的中文比较，再打开 `artifacts/original/comparison.csv` 找方法名称与分母；`records.csv` 用于逐条核对，`summary.json` 保存完整结果。文件、字段和参数对应见 [数据说明](data/DATA.md)。

### 2. 核对一项计算，再运行一个配置副本

先打开你自己的 S01 报告，保留当时的用途和选择。结合 S02–S05 的检查，写出至少两种失败解释，例如“缺失人数处理有问题”与“遗漏时段特征”。报告说明旧文件位置或提交版本，不用交完整 AI 对话。

程序在当前带缺失值的数据上重跑“人数缺失填 0 的回归”作为原方案。默认候选只把填补改为训练均值，不能直接与 S01 不同数据版本的旧 MAE 作差。

下面的副本改为检验“增加时段特征”，填补仍是 0。每个实验都比较该候选与相同原方案，不是把前一次候选当本次原方案。检查 `queue_after_imputation`、训练 MAE 和验证 MAE，说明哪项证据能区分你的解释。

把 `config.json` 另存为 `lesson-08/config-trial.json`。下面是可以完整复制的示例副本；JSON 使用英文双引号、逗号和冒号。它是操作起点，不是所有人必须选择的方案。

```json
{
  "seed": 7,
  "evaluation_split": "validation",
  "change": "period_feature",
  "stress_queue_shift": 3
}
```

运行：

```bash
python lesson-08/analysis.py --config lesson-08/config-trial.json --output lesson-08/artifacts/trial
```

### 3. 作出自己的选择，设计一次检查

再选择一种合理的输入变化，用配置中的 `stress_queue_shift` 检查记录错误的影响；它不是现实因果实验。报告展示原方案与候选在同一批样本上的结果，解释保留、修改或暂停的理由。

AI 可以帮你提出不同解释和实现改法。至少一项选择要真正影响比较，不仅把示例改写成自己的话。允许换问题、数据和实现，但要说明为什么仍需要本课知识；不要只改字段名称却保留原结论。进一步运行请使用新输出目录，避免覆盖旧证据。

### 4. 保留比较，确定本课建议

在仍使用验证集时，把选定配置另存为 `lesson-08/config-validation.json`，先运行并保留下面这份验证结果：

```bash
python lesson-08/analysis.py --config lesson-08/config-validation.json --split validation --output lesson-08/artifacts/chosen-validation
```

在报告记下选择与理由，再把同样参数写回 `config.json` 并把 `evaluation_split` 改为 `test`。运行 `python scripts/course.py run 08`，测试输出位于主 `artifacts/`，不会覆盖前面的验证子目录。

默认验证与试验输出都要保留。报告补上下面的验证重算命令，再描述事先选中方案的测试结果，不能看完测试分数后换成另一个候选：

```bash
python lesson-08/analysis.py --config lesson-08/config-validation.json --split validation --output lesson-08/artifacts/recheck-validation
```

若测试后又修改方法，这次结果转为开发证据，需要新的未参与修改的数据继续评价。

主目录结果应能由当前 `config.json` 和 `python scripts/course.py run 08` 重算；提交时不要又换回另一配置。程序的 `example_only` 仍表示起步计算，不会替你选择模型、写建议或把作业改成已完成。原方案可胜出，失败也可成为有依据的结论。

### 5. 核对提交文件

将 `report.md` 的提示替换成自己的回答，在 `contract.json` 填写任务说明，再把 `submission.json` 的 `status` 改为 `complete`。六个任务字段、结果保存和提交命令见 [本模块操作说明](../docs/FOUNDATIONS.md)。不要更改清单里的课号。

```bash
python scripts/course.py check 08
```

清单默认包含主结果的 JSON 与 CSV。报告引用的原始和试验结果、配置副本也要一起保留。`artifacts/` 被 Git 忽略，提交时需要显式加入；具体命令和验证方法在模块说明中。检查通过不等于文件已经上传。

## 必须提交什么

提交程序与配置、`summary.json`、`comparison.csv`、`records.csv`、任务说明和报告；保留报告引用的配置副本、原始与试验输出，以及对应运行命令。不要手填程序结果来代替计算。

报告回答：我在研究什么；什么是输入和标签；比较是否使用了正确的分母与数据；自己检查了什么；哪些证据支持保留、修改或暂停。还要引用 S01 的原用途，展示一次前后修订和测试前选择。

## 不同起点怎么做

入门支持：使用给定小数据，从一条记录和一次手算开始；仍须选择用途、提出自己的检查并解释结果。提高任务：更换有理由的数据或方法，增加一种独立核对，而不是只增加模型数量。所选难度不改变本课必须理解的关系。

## 运行限制

使用 Python 3.10 以上与已安装的 NumPy，最多 28 条人工教学样本，普通 CPU 即可；约 8 GB 可用内存，单次运行目标不超过 3 分钟、从头重跑目标不超过 5 分钟。必做实验不联网、不调用付费模型；AI 学习和在线概念检查的接入或补做另按教师安排。人工数据只能支持本次机制练习，不能证明真实人群、行动效果或 AI 能力。

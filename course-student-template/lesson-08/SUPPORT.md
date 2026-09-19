# S06 入门支持：只改一个因素，比较原方案与候选

这是 [本课任务](README.md) 的详细做法，不是额外作业。完成下面的比较、自己的检查和解释，就覆盖必做任务；不用再把 README 的另一条路径重复一遍。你可以使用现成程序和教师帮助，不需要先会写训练代码。**先做第一项小任务：找到 A05 的缺失人数，核对填补前后的值。**

## 1. 先知道今天在检查什么

**缺失值填补**是在输入缺失时用指定数值替代；**特征**是模型使用的输入。**控制变量**要求在一项比较中保持其他条件相同。本课不要求你从头编写回归算法。

先读 [LEARN.md](LEARN.md) 的对应例子。术语表按需查，不要为了开始上课把整张表背完。在 `report.md` 先写一句你的用途和预计结果；其余栏目等拿到结果再填写。

## 2. 不改代码，先跑通并找到结果

在学生仓库根目录运行，那里同时有 `scripts` 和 `lesson-08`。不知道终端或根目录在哪里，按 [第一次运行指南](../docs/FIRST_RUN.md) 的目录与环境检查操作；不要在 Python 的 `>>>` 中输入命令。只能识别 `python3` 的电脑，将以下 `python` 换成 `python3`。

```bash
python scripts/course.py start 08
python lesson-08/analysis.py --config lesson-08/config-start.json --output lesson-08/artifacts/support-start
```

`config-start.json` 是随课准备的起始配置，先不要改；数据仍来自本课 `data/base.json`。终端出现“结果写入”后，在 `lesson-08/artifacts/support-start/` 找到 `comparison.csv`、`records.csv` 和 `summary.json`。CSV 可以用表格软件或文本编辑器打开；文本编辑器中每行是记录，逗号隔开列。先看下面点名的列，不要求一次看懂所有指标。

## 3. 停下来核对，不只看运行成功

先打开 S01 的 `lesson-03/report.md`，找当时写的用途。没有自己的报告时，先在本课补写“给加入队伍前的同学估计等待时间”，并注明这是补写，不冒充旧实验结论。

在本课报告写两种解释：“人数缺失处理可能影响预测”“遗漏时段可能影响预测”。只需选其中一种先检查。

本程序不会读取 S01 的个人配置。这里的 `original` 专指本课提供的“缺失人数填 0 后拟合一元线性回归”，不一定是你在 S01 选择的模型。入门路径可以用它作为本次改进的起点，但报告要说明这个起点与 S01 方案是否相同；若不同，不能把本次差异说成自己原方案的提升。

起始实验在当前数据上运行本课给定的原方案：人数缺失填 0，再做回归；候选只改为训练集均值填补。训练集 12 条，缺失 3 条；剩下 9 个值之和为 13，均值为 `13/9≈1.444`。这是填补数，可以不是整数，不表示真的数到了 1.444 个人。

在 `records.csv` 找 A05 的 original、candidate 两行，核对 `queue_length` 留空、`queue_missing=True`，以及 `queue_after_imputation` 分别为 0、约 1.444。

| 比较表的方法 | 验证 MAE（分钟，约） |
|---|---:|
| original：当前数据上的原方案 | 3.284 |
| candidate：只改均值填补 | 3.224 |

平均误差略小不代表每条都改善：A05 的误差反而变大。再找 B06 核对另一条，说明两者有何不同。不要把这些分数和 S01 不同数据版本的旧分数直接相减。

以上数值是给定数据和起始配置的**自查参考**，四舍五入造成的小差异正常。它们不是必须达到的评分标准。先自己算或数，再对照；出现较大差异时检查方法名、配置路径和输出目录，不手改结果文件。

## 4. 跑一个已经准备好的对照

`config-support.json` 已经准备好，不用从空白文件写 JSON。

这个副本只把 `change` 从 `imputation` 改为 `period_feature`。这次候选恢复填 0，只增加“是否晚间”特征；原方案仍是同一个 original，不是把上次候选接着改。两次各自与 original 比，才能分别检查填补和特征。候选验证 MAE 约 1.254，但不能只凭这个数确定真实原因。

```bash
python lesson-08/analysis.py --config lesson-08/config-support.json --output lesson-08/artifacts/support-compare
```

并排打开两次结果，把“改了什么、哪项结果变了、哪项不变”记在报告。两个输出目录分开，不覆盖第一份。

## 5. 做一次有理由的个人选择

从你选中的配置另存 `config-mine.json`，自己选一个人数偏移，只改 `stress_queue_shift`（如 1 或 2）。在 `summary.json` 搜索 `stress_test`：它给已知人数加上这个数，保持标签和已拟合参数不变。对照该段的 original/candidate MAE，说明这是输入记录错误检查，不是给队伍加人后的因果效果。

另存文件时在编辑器中使用“另存为”，文件名是 `lesson-08/config-mine.json`。只改刚才点名的字段值，保留英文双引号、逗号和冒号，其他字段先不动。文件名不要多出 `.txt` 后缀。检查格式，再运行：

```bash
python -m json.tool lesson-08/config-mine.json
python lesson-08/analysis.py --config lesson-08/config-mine.json --output lesson-08/artifacts/my-check
```

这次填写自己的预计、实际结果和理由，不照抄例子中的采用建议。允许结果支持保留原方案，也允许暂不使用。需要 AI 帮助时，可以提问：“请只解释这条命令和这一行数据，先让我计算，再帮我核对；不要替我填最终建议。”

### S06：验证结果先保存，再进行最后评价

在报告写下选中 original 还是某条 candidate，以及评价方法。先把选中实验的参数另存为 `config-validation.json`，保持 `evaluation_split` 为 `validation`。保留它和下面命令生成的验证结果：

```bash
python lesson-08/analysis.py --config lesson-08/config-validation.json --split validation --output lesson-08/artifacts/chosen-validation
```

再将相同参数写回 `config.json`，只将 `evaluation_split` 改为 `test`。后面的 `run 08` 将生成主目录测试结果，不覆盖验证子目录。程序仍输出 original 和 candidate；报告解释事先选中的那一个，不能看完测试重新挑。测试后再修改方案，需要新的独立测试数据。公开教学样本只用来练习流程。

## 6. 写完报告，确认文件已保存

在 `report.md` 回答本课的问题，每项几句话；删除模板提示语，写出配置和结果路径。最少保留：用途与预计、一项手算或计数、同条件比较、自己的检查及原因、仍不能得出的结论。按上一段保存同一方案的测试配置，不要在提交前又换成另一候选。

`contract.json` 是任务说明，保留 `lesson` 并填其余六项：`question` 写问题，`user` 写使用者，`data_source` 写人工数据来源，`metric` 写指标和单位/分母，`split_plan` 写数据用途，`initial_expectation` 写实验前预计。完成实际工作后再将 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py run 08
python scripts/course.py check 08
git add lesson-08
git add -f lesson-08/artifacts
git diff --cached --name-only
```

最后一条只列出准备提交的文件；确认报告、任务说明、配置副本和引用的结果都在。你改过共享代码时，还要保存相应代码。上面没有提交到远程，接着按 [操作与提交步骤](../docs/WORKFLOW.md) 创建提交和本课 `v2-l08-final` 标签；不要覆盖已存在的标签。

## 卡住时先这样做

找不到脚本：回到学生仓库根目录。找不到 `config-mine.json`：检查是否另存到了本课目录或多了 `.txt`。JSON 报错：先运行上面的格式检查，修正显示的行列。运行失败后旧输出可能还在，不能当作新结果；换新目录重跑并确认成功提示。

环境仍不能运行时，先用第 3 节表格完成手算、计数和一段解释，明确注明“仅手算，尚未运行”，把命令与报错交给教师处理，之后补跑。这是不中断学习的办法，不是用给定答案冒充已完成实验。已完成核心比较后再选提高或拓展任务；不需要把全部层次做一遍。

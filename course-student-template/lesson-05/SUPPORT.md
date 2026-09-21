# S03 入门支持：先选使用对象，再选数据划分

这是 [本课任务](README.md) 的详细做法，不是额外作业。完成下面的比较、自己的检查和解释，就覆盖必做任务；不用再把 README 的另一条路径重复一遍。你可以使用现成程序和教师帮助，不需要先会写训练代码。本课的难点不是把命令跑通，而是判断同一个模型评价的到底是哪一种未来使用。**先做第一项小任务：写下“已有窗口的未来日期”和“新窗口”两个用途，再找到 time、group 两行，先数训练与验证样本，不急着比 MAE。**

## 1. 先知道今天在检查什么

**训练集**用于拟合参数，**验证集**用于开发比较，**测试集**留到方案确定后。**分组划分**中的组是同一个窗口，不是随便分几堆数据。A、B、C 是三个虚构窗口。

先读 [LEARN.md](LEARN.md) 的对应例子。术语表按需查，不要为了开始上课把整张表背完。在 `report.md` 先分别写两个用途和你的预计：哪个用途更接近 time，哪个更接近 group？不要先看 MAE 再倒推答案；其余栏目等拿到结果再填写。

## 2. 不改代码，先跑通并找到结果

在学生仓库根目录运行，那里同时有 `scripts` 和 `lesson-05`。不知道终端或根目录在哪里，按 [第一次运行指南](../docs/FIRST_RUN.md) 的目录与环境检查操作；不要在 Python 的 `>>>` 中输入命令。只能识别 `python3` 的电脑，将以下 `python` 换成 `python3`。

```bash
python scripts/course.py start 05
python lesson-05/analysis.py --config lesson-05/config-start.json --output lesson-05/artifacts/support-start
```

`config-start.json` 是随课准备的起始配置，先不要改；数据仍来自本课 `data/base.json`。终端出现“结果写入”后，在 `lesson-05/artifacts/support-start/` 找到 `comparison.csv`、`records.csv` 和 `summary.json`。CSV 可以用表格软件或文本编辑器打开；文本编辑器中每行是记录，逗号隔开列。先看下面点名的列，不要求一次看懂所有指标。

## 3. 停下来核对，不只看运行成功

先看 `comparison.csv`，只读下列两行。`train_n` 是训练条数，`n` 是当前验证条数，`shared_sites` 是两部分共同出现的窗口数。

| `method` | 训练样本数 | 验证样本数 | 共有窗口数 |
|---|---:|---:|---:|
| time：时间划分 | 12 | 6 | 3 |
| group：按窗口分组 | 6 | 6 | 0 |

对照 [学习卡中的划分表](LEARN.md)：时间方案用 A/B/C 第 1–4 天训练、第 5–6 天验证；分组方案用 A 的前 6 天训练、B 的前 6 天验证。要核对编号，在 `summary.json` 搜索 `train_ids`、`evaluation_ids`，注意它们位于各自的 `time` 或 `group` 段内。

再在 `records.csv` 找 `id=B05`、`method=time`。正常特征是排队时的人数；`leaked_prediction_demo=8` 却是用了事后才得到的小票数 `8.25−0.25`。比较表中的 `leaked_mae_demo=0` 是**数据泄漏反例**，不是可选的优秀模型。分组划分并不能让事后信息变成事前可用信息。把 B05 的正常预测误差和泄漏示范误差都写进报告，并说明两者差异来自哪个字段。

以上数值是给定数据和起始配置的**自查参考**，四舍五入造成的小差异正常。它们不是必须达到的评分标准。先自己算或数，再对照；出现较大差异时检查方法名、配置路径和输出目录，不手改结果文件。

## 4. 跑一个已经准备好的对照

`config-support.json` 已经准备好，不用从空白文件写 JSON。

这个副本只把 `train_through_day` 从 4 改为 3。time 行训练从 12 变为 9、验证从 6 变为 9；group、random 两行不受这个参数影响。第 4 天的 A04/B04/C04 从训练转为验证，保留测试行仍不进入开发。比较的是评价安排，不是同一测试上的模型性能提升。

```bash
python lesson-05/analysis.py --config lesson-05/config-support.json --output lesson-05/artifacts/support-compare
```

并排打开两次结果，把“改了什么、哪项结果变了、哪项不变”记在报告。特别记录 time 的训练数从 12 变为 9、验证数从 6 变为 9，以及验证编号如何变化；group 和 random 为什么不随这个日期设置改变也要写一句。两个输出目录分开，不覆盖第一份。

## 5. 做一次有理由的个人选择

从 `config-start.json` 另存 `config-mine.json`。选择另一个训练截止日（如 2），只改 `train_through_day`，保持验证最晚日为 6。核对 time 的训练与验证编号。报告选择“旧窗口未来”或“新窗口”，据用途解释时间或分组方法，不按最低 MAE 决定。

另存文件时在编辑器中使用“另存为”，文件名是 `lesson-05/config-mine.json`。只改刚才点名的字段值，保留英文双引号、逗号和冒号，其他字段先不动。文件名不要多出 `.txt` 后缀。检查格式，再运行：

```bash
python -m json.tool lesson-05/config-mine.json
python lesson-05/analysis.py --config lesson-05/config-mine.json --output lesson-05/artifacts/my-check
```

这次填写自己的预计、实际结果和理由，不照抄例子中的采用建议。允许结果支持保留原方案，也允许暂不使用。个人检查必须改变评价对象或检验随机波动：改日期时核对训练/验证编号和分母；改种子时至少运行三个种子并全部保存。需要 AI 帮助时，可以提问：“请只解释这条命令和这一行数据，先让我计算，再帮我核对；不要替我填最终建议。”

## 6. 写完报告，确认文件已保存

在 `report.md` 回答本课的问题，每项几句话；删除模板提示语，写出配置和结果路径。最少保留：两个用途与预计、time/group 的训练和验证证据、一项 MAE 手算或计数、泄漏反例、自己的检查及原因、仍不能得出的结论。把想保留的参数写回本课 `config.json`，不要改课次字段。

`contract.json` 是任务说明，保留 `lesson` 并填其余六项：`question` 写问题，`user` 写使用者，`data_source` 写人工数据来源，`metric` 写指标和单位/分母，`split_plan` 写数据用途，`initial_expectation` 写实验前预计。完成实际工作后再将 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py run 05
python scripts/course.py check 05
git add lesson-05
git add -f lesson-05/artifacts
git diff --cached --name-only
```

最后一条只列出准备提交的文件；确认报告、任务说明、配置副本和引用的结果都在。你改过共享代码时，还要保存相应代码。上面没有提交到远程，接着按 [操作与提交步骤](../docs/WORKFLOW.md) 创建提交和本课 `v2-l05-final` 标签；不要覆盖已存在的标签。

## 卡住时先这样做

找不到脚本：回到学生仓库根目录。找不到 `config-mine.json`：检查是否另存到了本课目录或多了 `.txt`。JSON 报错：先运行上面的格式检查，修正显示的行列。运行失败后旧输出可能还在，不能当作新结果；换新目录重跑并确认成功提示。

环境仍不能运行时，先用第 3 节表格完成手算、计数和一段解释，明确注明“仅手算，尚未运行”，把命令与报错交给教师处理，之后补跑。这是不中断学习的办法，不是用给定答案冒充已完成实验。已完成核心比较后再选提高或拓展任务；不需要把全部层次做一遍。

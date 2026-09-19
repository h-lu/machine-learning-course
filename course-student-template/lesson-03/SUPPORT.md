# S01 入门支持：预测与提醒是两件事

这是 [本课任务](README.md) 的详细做法，不是额外作业。完成下面的比较、自己的检查和解释，就覆盖必做任务；不用再把 README 的另一条路径重复一遍。你可以使用现成程序和教师帮助，不需要先会写训练代码。**先做第一项小任务：找到 B05 的人工规则预测，手算 3 与 8 相差多少分钟。**

## 1. 先知道今天在检查什么

只需先记住：**特征**是预测时的输入，本课是人数；**目标值**是实际等待分钟数；**预测值**由规则或模型算出。**阈值**是发提醒的界限，不是模型训练参数。

先读 [LEARN.md](LEARN.md) 的对应例子。术语表按需查，不要为了开始上课把整张表背完。在 `report.md` 先写一句你的用途和预计结果；其余栏目等拿到结果再填写。

## 2. 不改代码，先跑通并找到结果

在学生仓库根目录运行，那里同时有 `scripts` 和 `lesson-03`。不知道终端或根目录在哪里，按 [第一次运行指南](../docs/FIRST_RUN.md) 的目录与环境检查操作；不要在 Python 的 `>>>` 中输入命令。只能识别 `python3` 的电脑，将以下 `python` 换成 `python3`。

```bash
python scripts/course.py start 03
python lesson-03/analysis.py --config lesson-03/config-start.json --output lesson-03/artifacts/support-start
```

`config-start.json` 是随课准备的起始配置，先不要改；数据仍来自本课 `data/base.json`。终端出现“结果写入”后，在 `lesson-03/artifacts/support-start/` 找到 `comparison.csv`、`records.csv` 和 `summary.json`。CSV 可以用表格软件或文本编辑器打开；文本编辑器中每行是记录，逗号隔开列。先看下面点名的列，不要求一次看懂所有指标。

## 3. 停下来核对，不只看运行成功

先看 `comparison.csv` 的 `method_name`（方法名）、`n`（本方法评价了几条）、`mae`（平均绝对误差，分钟）和 `alerts`（提醒条数）。三种预测方法的 `n` 都是 6，不提醒路线没有分钟预测，MAE 留空，不能读成 0。

再打开 `records.csv`，同时找 `id=B05`、`method=rule`。同一编号出现多次是不同方法的预测，不是多名同学。

| 要核对的内容 | 起始配置下的值 |
|---|---:|
| `queue_length`：人数 | 1 |
| `actual`：实际分钟数 | 8 |
| `prediction`：人工规则预测 | 3 |
| `absolute_error`：绝对误差 | 5 |

手算 `1 + 2 × 1 = 3`，再算 `|8 − 3| = 5`。现在只说明规则少报了 5 分钟，不说明提醒能节省 5 分钟。回到比较表，核对三种方法使用的是同样 6 条样本。

以上数值是给定数据和起始配置的**自查参考**，四舍五入造成的小差异正常。它们不是必须达到的评分标准。先自己算或数，再对照；出现较大差异时检查方法名、配置路径和输出目录，不手改结果文件。

## 4. 跑一个已经准备好的对照

`config-support.json` 已经准备好，不用从空白文件写 JSON。

这个副本只把 `alert_minutes` 从 8 改成 10，其他不变。比较 linear 行：MAE 仍约 2.556，但提醒数从 3 变成 1。再找 B06 的 `alert`：True 变 False，预测却没变。写一句“我改的是提醒条件，不是模型”。

```bash
python lesson-03/analysis.py --config lesson-03/config-support.json --output lesson-03/artifacts/support-compare
```

并排打开两次结果，把“改了什么、哪项结果变了、哪项不变”记在报告。两个输出目录分开，不覆盖第一份。

## 5. 做一次有理由的个人选择

从 `config-start.json` 另存 `config-mine.json`，自己选一个提醒阈值（例如 9 或 12 分钟），只改 `alert_minutes`。先写为什么适合你的用途，再运行。选一条提醒状态变化或没有变化的记录，解释原因。提醒数不能写成节省时间。

另存文件时在编辑器中使用“另存为”，文件名是 `lesson-03/config-mine.json`。只改刚才点名的字段值，保留英文双引号、逗号和冒号，其他字段先不动。文件名不要多出 `.txt` 后缀。检查格式，再运行：

```bash
python -m json.tool lesson-03/config-mine.json
python lesson-03/analysis.py --config lesson-03/config-mine.json --output lesson-03/artifacts/my-check
```

这次填写自己的预计、实际结果和理由，不照抄例子中的采用建议。允许结果支持保留原方案，也允许暂不使用。需要 AI 帮助时，可以提问：“请只解释这条命令和这一行数据，先让我计算，再帮我核对；不要替我填最终建议。”

## 6. 写完报告，确认文件已保存

在 `report.md` 回答本课的问题，每项几句话；删除模板提示语，写出配置和结果路径。最少保留：用途与预计、一项手算或计数、同条件比较、自己的检查及原因、仍不能得出的结论。把想保留的参数写回本课 `config.json`，不要改课次字段。

`contract.json` 是任务说明，保留 `lesson` 并填其余六项：`question` 写问题，`user` 写使用者，`data_source` 写人工数据来源，`metric` 写指标和单位/分母，`split_plan` 写数据用途，`initial_expectation` 写实验前预计。完成实际工作后再将 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py run 03
python scripts/course.py check 03
git add lesson-03
git add -f lesson-03/artifacts
git diff --cached --name-only
```

最后一条只列出准备提交的文件；确认报告、任务说明、配置副本和引用的结果都在。你改过共享代码时，还要保存相应代码。上面没有提交到远程，接着按 [操作与提交步骤](../docs/WORKFLOW.md) 创建提交和本课 `v2-l03-final` 标签；不要覆盖已存在的标签。

## 卡住时先这样做

找不到脚本：回到学生仓库根目录。找不到 `config-mine.json`：检查是否另存到了本课目录或多了 `.txt`。JSON 报错：先运行上面的格式检查，修正显示的行列。运行失败后旧输出可能还在，不能当作新结果；换新目录重跑并确认成功提示。

环境仍不能运行时，先用第 3 节表格完成手算、计数和一段解释，明确注明“仅手算，尚未运行”，把命令与报错交给教师处理，之后补跑。这是不中断学习的办法，不是用给定答案冒充已完成实验。已完成核心比较后再选提高或拓展任务；不需要把全部层次做一遍。

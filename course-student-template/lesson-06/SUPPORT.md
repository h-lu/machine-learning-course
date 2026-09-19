# S04 入门支持：分别看预测误差和提醒后果

这是 [本课任务](README.md) 的详细做法，不是额外作业。完成下面的比较、自己的检查和解释，就覆盖必做任务；不用再把 README 的另一条路径重复一遍。你可以使用现成程序和教师帮助，不需要先会写训练代码。**先做第一项小任务：找到 B05 的回归预测，判断它是低估还是高估。**

## 1. 先知道今天在检查什么

**绝对误差**只看预测相差多少；**非对称损失**对低估、高估赋不同权重。**误报**是提醒了却没有长等，**漏报**是长等却没提醒。先看预测误差，再看提醒决定，不同时修改两类设置。

先读 [LEARN.md](LEARN.md) 的对应例子。术语表按需查，不要为了开始上课把整张表背完。在 `report.md` 先写一句你的用途和预计结果；其余栏目等拿到结果再填写。

## 2. 不改代码，先跑通并找到结果

在学生仓库根目录运行，那里同时有 `scripts` 和 `lesson-06`。不知道终端或根目录在哪里，按 [第一次运行指南](../docs/FIRST_RUN.md) 的目录与环境检查操作；不要在 Python 的 `>>>` 中输入命令。只能识别 `python3` 的电脑，将以下 `python` 换成 `python3`。

```bash
python scripts/course.py start 06
python lesson-06/analysis.py --config lesson-06/config-start.json --output lesson-06/artifacts/support-start
```

`config-start.json` 是随课准备的起始配置，先不要改；数据仍来自本课 `data/base.json`。终端出现“结果写入”后，在 `lesson-06/artifacts/support-start/` 找到 `comparison.csv`、`records.csv` 和 `summary.json`。CSV 可以用表格软件或文本编辑器打开；文本编辑器中每行是记录，逗号隔开列。先看下面点名的列，不要求一次看懂所有指标。

## 3. 停下来核对，不只看运行成功

先在 `records.csv` 同时找 `id=B05`、`method=linear`：实际 8，预测约 6.333。它是低估，绝对误差约 1.667。低估权重为 3 时，`weighted_error` 约为 `1.667×3=5`。

再看 A05 的 linear 行：实际 2，预测约 4.333，是高估，加权误差仍约 2.333。权重是这次用途的假设，不是测得的现实成本。

| 比较表中的方法 | MAE（分钟） | `asymmetric_loss` 平均加权误差 |
|---|---:|---:|
| linear：原回归 | 2.556 | 6.111 |
| buffered：回归预测加 4 分钟 | 3.000 | 3.000 |

这说明不同指标可以支持不同选择。不要把平均加权误差叫作“实际损失分钟数”。

然后看提醒：真实等待至少 8 分钟为正类；预测达到提醒阈值后，再按预测从高到低分配最多 2 个名额。`tp/fp/fn/tn` 分别是正确提醒、误报、漏报、正确不提醒。原回归的计数为 `2/0/2/2`，合计 6 条。B05 实际长等却没提醒，是漏报。

以上数值是给定数据和起始配置的**自查参考**，四舍五入造成的小差异正常。它们不是必须达到的评分标准。先自己算或数，再对照；出现较大差异时检查方法名、配置路径和输出目录，不手改结果文件。

## 4. 跑一个已经准备好的对照

`config-support.json` 已经准备好，不用从空白文件写 JSON。

这个副本只把 `underestimate_weight` 从 3 改成 1。预测、提醒数和四类计数应不变，平均加权误差变得等于 MAE。于是原回归和缓冲方案按这个指标的顺序改变。核对 B05 的 `weighted_error` 从约 5 变为约 1.667。

```bash
python lesson-06/analysis.py --config lesson-06/config-support.json --output lesson-06/artifacts/support-compare
```

并排打开两次结果，把“改了什么、哪项结果变了、哪项不变”记在报告。两个输出目录分开，不覆盖第一份。

## 5. 做一次有理由的个人选择

从 `config-start.json` 另存 `config-mine.json`。自己选一个容量（如 1 或 3），只改 `capacity`，保持其他设置。先预计提醒数或漏报数，再核对 `tp+fp+fn+tn=6`、`alerts≤capacity`。不要同时改真实长等定义和提醒阈值。

另存文件时在编辑器中使用“另存为”，文件名是 `lesson-06/config-mine.json`。只改刚才点名的字段值，保留英文双引号、逗号和冒号，其他字段先不动。文件名不要多出 `.txt` 后缀。检查格式，再运行：

```bash
python -m json.tool lesson-06/config-mine.json
python lesson-06/analysis.py --config lesson-06/config-mine.json --output lesson-06/artifacts/my-check
```

这次填写自己的预计、实际结果和理由，不照抄例子中的采用建议。允许结果支持保留原方案，也允许暂不使用。需要 AI 帮助时，可以提问：“请只解释这条命令和这一行数据，先让我计算，再帮我核对；不要替我填最终建议。”

## 6. 写完报告，确认文件已保存

在 `report.md` 回答本课的问题，每项几句话；删除模板提示语，写出配置和结果路径。最少保留：用途与预计、一项手算或计数、同条件比较、自己的检查及原因、仍不能得出的结论。把想保留的参数写回本课 `config.json`，不要改课次字段。

`contract.json` 是任务说明，保留 `lesson` 并填其余六项：`question` 写问题，`user` 写使用者，`data_source` 写人工数据来源，`metric` 写指标和单位/分母，`split_plan` 写数据用途，`initial_expectation` 写实验前预计。完成实际工作后再将 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py run 06
python scripts/course.py check 06
git add lesson-06
git add -f lesson-06/artifacts
git diff --cached --name-only
```

最后一条只列出准备提交的文件；确认报告、任务说明、配置副本和引用的结果都在。你改过共享代码时，还要保存相应代码。上面没有提交到远程，接着按 [操作与提交步骤](../docs/WORKFLOW.md) 创建提交和本课 `v2-l06-final` 标签；不要覆盖已存在的标签。

## 卡住时先这样做

找不到脚本：回到学生仓库根目录。找不到 `config-mine.json`：检查是否另存到了本课目录或多了 `.txt`。JSON 报错：先运行上面的格式检查，修正显示的行列。运行失败后旧输出可能还在，不能当作新结果；换新目录重跑并确认成功提示。

环境仍不能运行时，先用第 3 节表格完成手算、计数和一段解释，明确注明“仅手算，尚未运行”，把命令与报错交给教师处理，之后补跑。这是不中断学习的办法，不是用给定答案冒充已完成实验。已完成核心比较后再选提高或拓展任务；不需要把全部层次做一遍。

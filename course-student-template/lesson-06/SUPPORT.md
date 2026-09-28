# 第 06 课入门支持：先核对一条预测，再比较提醒

这是 [本课任务](README.md) 的一条完整做法，完成后不用另交一份 Core 作业。先做一件能在几分钟内开始的小事：运行本课程序，在逐条结果里找到 B05，判断线性回归预测是高估还是低估。你不必先写代码或读完整术语表。

## 1. 先认清两种用途和三个方法

同一个等待时间预测可以直接显示给同学，也可以帮助值班人员决定提醒谁。显示分钟数时，要看预测与实际相差多少；用于提醒时，还要看哪些真正长等的记录被漏掉、哪些短等的记录被误报。

本课程序提供三种方法：`baseline` 是总预测训练记录平均等待时间的**均值基线**；`linear` 是用“前面排队人数”预测等待分钟数的**线性回归模型**；`buffered` 只是在 `linear` 的每个预测上加 4 分钟，**没有重新训练模型**。这些都是本课给定的起点，不是程序读取了你在第 05 课提交的模型。

现在先在 `report.md` 第 1 节各写一句：如果显示的时间偏低或偏高，会怎样？如果一轮最多只能处理 2 条提醒，会怎样？低估权重 3 和容量 2 是练习用的使用假设，不是调查得到的真实成本。

## 2. 运行起点，先打开逐条结果

在学生仓库根目录运行，也就是同时能看到 `scripts` 和 `lesson-06` 的目录。若电脑只有 `python3`，把以下 `python` 换为 `python3`。不要把命令输在 Python 的 `>>>` 提示符后。

```bash
python scripts/course.py start 06
python lesson-06/analysis.py --config lesson-06/config-start.json --output lesson-06/artifacts/support-start
```

第一条命令只把本课提交状态改为“进行中”；第二条命令读取 `lesson-06/data/base.json` 和给定的 `config-start.json`，把结果写到 `lesson-06/artifacts/support-start/`。看到终端的“结果写入”后，**先打开 `records.csv`**，再看 `comparison.csv`；`summary.json` 保存同一实验的完整信息。CSV 可以用表格软件或文本编辑器打开，第一行是列名，一行是一种方法对一条记录的结果。

在 `records.csv` 找 `id=B05` 且 `method=linear` 的那行。`id` 是记录编号，`method` 是方法代号；`actual` 是事后知道的真实等待分钟数，`prediction` 是模型事先给的预测。B05 的 `actual=8`、`prediction≈6.333`：预测比实际少，叫**低估**。如果找不到这行，先核对文件路径和这两个列名，暂时不要继续改配置。

## 3. 自己算一行，再读比较表

B05 的**绝对误差**是 `|8−6.333|≈1.667` 分钟。`config-start.json` 规定低估权重为 3，所以这条的 `weighted_error≈1.667×3=5`；它是评价分数，**不表示现实中损失了 5 分钟**。再找 `id=A05`、`method=linear`：实际 2 分钟、预测约 4.333 分钟，是高估；绝对误差及加权误差均约 2.333。先自己算，再对照文件里的 `absolute_error` 和 `weighted_error`。

现在打开 `comparison.csv`。`n=6` 表示每个方法都用同一批 6 条验证记录来评价；同一个 B05 在 `records.csv` 出现多次，是不同方法的结果，不是多条新记录。先只看这两行：

| `method` | 方案 | MAE：平均绝对误差（分钟） | `asymmetric_loss`：平均加权误差分数 |
|---|---|---:|---:|
| `linear` | 本课给定的线性回归 | 2.556 | 6.111 |
| `buffered` | 每个回归预测加 4 分钟 | 3.000 | 3.000 |

MAE 是 6 条绝对误差之和除以 6；加权误差分数也是逐条加权误差之和除以 6。按 MAE，`linear` 较小；若认为低估应乘 3，`buffered` 的加权误差分数较小。两种指标回答的问题不同，不能挑一个分数就宣布所有用途都适合它。需要再看一遍小计算时，读 [LEARN.md 的误差与权重解释](LEARN.md)。

提醒又是另一件事：事后实际等待**至少 8 分钟**算需要提醒；当时只能根据**预测至少 8 分钟**形成候选，再按预测从高到低选最多 2 条。起点里 `linear` 的 `tp/fp/fn/tn=2/0/2/2`，依次是正确提醒、误报、漏报、正确不提醒，总数为 6。B05 是实际长等却没收到提醒的漏报。想看清候选与最终提醒的区别，读 [LEARN.md 的四行例子](LEARN.md)，再回到输出文件。

表里的数值只用于核对给定数据和配置，不是你必须得到的“标准结论”。若数字差很多，检查方法名、配置路径和输出目录，不手改程序结果。

## 4. 只改评价权重，不改预测

`config-support.json` 是准备好的单项对照：它只把 `underestimate_weight` 从 3 改为 1。先预计：同一批预测的 MAE、提醒编号和误报漏报会不会变？平均加权误差分数会不会变？把预计写在报告第 3 节，再运行：

```bash
python lesson-06/analysis.py --config lesson-06/config-support.json --output lesson-06/artifacts/support-compare
```

并排看两份 `comparison.csv` 的 `linear` 和 `buffered`。权重为 1 时，平均加权误差分数分别约为 2.556 和 3.000，等于各自 MAE；两种方法按这个分数的先后顺序反转。B05 的 `weighted_error` 从约 5 变为约 1.667。权重改变的是**评价规则**，模型预测及提醒规则没有改变；报告要把这两件事分清。

## 5. 只改提醒容量，做自己的检查

这一次由你设定一个使用条件：一轮只能处理 `1` 条，或一轮最多处理 `4` 条。`capacity` 是最多能发出的提醒数，不是预测阈值。先在报告写明为什么选这个名额、预计哪些提醒或误报漏报会变化，以及什么结果会让你改变建议。

在编辑器里把 `lesson-06/config-start.json` **另存为** `lesson-06/config-mine.json`。只把 `"capacity": 2` 改成 `"capacity": 1` 或 `"capacity": 4`，其他行保持原样，包括权重、两个 8 分钟阈值和 `stress_capacity`。文件名不要多出 `.txt`。先检查 JSON 格式，再运行到新的目录：

```bash
python -m json.tool lesson-06/config-mine.json
python lesson-06/analysis.py --config lesson-06/config-mine.json --output lesson-06/artifacts/my-check
```

在新 `comparison.csv` 分别找 `linear` 和 `buffered`，读 `eligible`（达到预测阈值的候选数）、`alerts`（实际提醒数）、`tp/fp/fn/tn`。在新 `records.csv` 找这两种方法中 `alert=True` 的编号。每种方法都应满足四类计数合计为 6，且 `alerts≤capacity`。

供**数完后核对**：容量 1 时，两种方法都只提醒 C06，各有 1 次正确提醒、3 次漏报。容量 4 时，`linear` 只提醒 B06、C05、C06，漏报 B05；`buffered` 提醒 A06、B06、C05、C06，其中 A06 是误报，B05 仍是漏报。它们来自人工小数据和固定排序规则，不能推广成真实系统的效果。报告须写你的预计、实际编号与理由，不能只抄这些核对数字。

## 6. 写报告并确认文件能提交

在 `report.md` 写两个用途、一条低估和一条高估的手算、权重 3 与 1 的比较、你的容量检查及提醒编号，并分别给显示分钟数和有限提醒写建议。每条建议至少有一项支持证据和一项代价。`contract.json` 是任务说明：保留 `lesson`，在其余六个字段写问题、使用者、数据来源、指标及单位与分母、数据用途和运行前预计。把最终设置写回 `config.json`，完成实际工作后再把 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py run 06
python scripts/course.py check 06
git add lesson-06
git add -f lesson-06/artifacts
git diff --cached --name-only
```

`run` 生成主结果，`check` 检查清单和文件；最后一条只列出准备提交的文件。确认配置副本、报告、任务说明和报告引用的所有结果都在列表里。`artifacts/` 默认被 Git 忽略，所以要显式 `git add -f`。这些命令尚未提交或上传；接着按 [操作与提交步骤](../docs/WORKFLOW.md) 创建提交和本课 `v2-l06-final` 标签，不覆盖已有标签。

## 卡住时先这样做

找不到脚本时回到仓库根目录；找不到 B05 时先确认打开的是 `support-start/records.csv`，再检查 `id` 和 `method` 两列。JSON 报错时看格式检查指出的行列；文件名多出 `.txt` 时重新另存。运行失败后旧输出可能还在，要换新目录重跑并看到成功提示，不能把旧文件算作这次结果。

环境暂时不能运行时，先用第 3 节给出的两行数字完成手算，并在报告写“仅手算，尚未运行”，把命令与完整报错交给教师，之后补跑。这样可以继续学习，但不能把核对示例当作自己完成的实验。

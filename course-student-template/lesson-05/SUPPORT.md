# 第 05 课（S03）入门支持：先确定预测对象，再划分数据

这是完成本课必做任务的一条详细路径，不是额外作业。你将比较两种实际用途：

- **已有取餐窗口的较晚日期**：A、B、C 已经在训练数据中出现；
- **训练中没出现的新取餐窗口**：验证窗口没有进入训练集。

先不要按误差数值选方法。第一项小任务是在 `report.md` 第 1 节写下：“已有窗口的较晚日期”预计采用时间顺序划分（程序中写作 `time`），“训练中没出现的新窗口”预计采用分组划分（程序中写作 `group`）。然后选出本次主要准备支持的一个用途。

## 1. 先理解三个数据部分

- **模型（model）**是根据输入计算预测值的规则。**特征（feature）**是预测时使用的输入，本课是排队人数；**标签／目标值（label / target）**是希望预测的真实结果，本课是实际等待分钟数。
- **模型参数（model parameter）**是决定这条计算规则的数值，例如直线的截距和斜率。**拟合（fitting）**是用训练数据确定这些参数的过程。
- **训练集（training set）**用于拟合模型，也就是确定模型参数。
- **验证集（validation set）**用于比较候选方案，不用于拟合当前模型。
- **测试集（test set）**在方案确定后才做最后评价，本课不会打开它。

**平均绝对误差（mean absolute error，MAE）**的计算方法是：先算每条“预测值减实际值”的绝对值，再用这些绝对误差的总和除以记录数。本课单位是分钟。

本课一行数据代表某个取餐窗口某一天的一次记录。A、B、C 是三个虚构的取餐窗口。

## 2. 运行起点，先找数量和编号

在学生仓库根目录运行，也就是同时能看到 `scripts/` 和 `lesson-05/` 的目录：

```bash
python scripts/course.py start 05
python lesson-05/analysis.py --config lesson-05/config-start.json --output lesson-05/artifacts/support-start
```

如果终端找不到 `python`，但 `python3 --version` 能显示版本，把本页所有 `python` 换成 `python3`。成功时终端会显示“结果写入”。

先打开 `lesson-05/artifacts/support-start/comparison.csv`。CSV 是用行和列保存表格的文本文件；只核对下面四列：

| `method` | `train_n` 训练数 | `n` 验证数 | `shared_sites` 训练和验证共有窗口数 |
|---|---:|---:|---:|
| `time` | 12 | 6 | 3 |
| `group` | 6 | 6 | 0 |

这些数字是给定数据的排错参考，不是评分要求。你的实际文件若不同，先检查配置路径和输出目录。

然后打开 `summary.json`，依次找到：

- `details.splits.time.train_ids` 与 `evaluation_ids`；
- `details.splits.group.train_ids` 与 `evaluation_ids`；
- 两段中的 `train_sites` 与 `evaluation_sites`。

起点的 `time` 用三个窗口的第 1–4 天训练、第 5–6 天验证。`group` 用 A01–A06 训练、B01–B06 验证。第 7–8 天的记录没有用于拟合模型或选择方案。

## 3. 手算 time 的 MAE

打开 `records.csv`，筛选 `method=time`，找到 A05、A06、B05、B06、C05、C06。它们的 `absolute_error` 约为：

```text
2.3333，2.3333，1.6667，1.6667，3.6667，3.6667 分钟
```

先自己计算，再对照：

```text
(2.3333 + 2.3333 + 1.6667 + 1.6667 + 3.6667 + 3.6667) ÷ 6
≈ 2.5556 分钟
```

分母 6 是 time 验证集的记录数。MAE 表示这 6 条记录平均相差多少分钟。group 的验证对象不同，所以不能把两行 MAE 直接解释为同一批记录上的模型优劣。

## 4. 识别目标泄漏

仍在 `records.csv` 中看 B05：

- 实际等待是 8 分钟；
- 正常预测只使用加入队伍时可见的排队人数，预测约 6.3333 分钟；
- `leaked_prediction_demo` 使用结束后才出现的小票时间，预测恰好是 8 分钟。

小票时间 `receipt_minutes` 等于真实等待加 0.25 分钟，几乎直接暴露了目标值。这是**目标泄漏（target leakage）**。`leaked_mae_demo=0` 只说明错误示范偷看了事后信息，不能说明模型能够在加入队伍前准确预测。

## 5. 跑现成日期对照

`config-support.json` 只把时间划分的训练截止日从第 4 天改为第 3 天：

```bash
python lesson-05/analysis.py --config lesson-05/config-support.json --output lesson-05/artifacts/support-compare
```

成功后核对：time 的训练数从 12 变为 9，验证数从 6 变为 9；group 和 random 不变。把两次 time 的验证编号并排写在报告中。由于验证记录和分母都变了，MAE 的差不能直接称为同一样本上的性能变化。

## 6. 根据主要用途做自己的检查

运行前先写一句改变条件。例如：“如果证据只在某一个日期边界或某一个验证窗口上成立，我会限制这项建议，不把它推广到所有未来情况。”

### 路线 A：主要关心已有窗口的未来日期

在编辑器中把 `config-start.json` 另存为 `config-mine.json`，只将 `train_through_day` 从 `4` 改为 `2`。文件仍放在 `lesson-05/`，不要多出 `.txt` 后缀。

```bash
python -m json.tool lesson-05/config-mine.json
python lesson-05/analysis.py --config lesson-05/config-mine.json --output lesson-05/artifacts/my-check
```

核对 time 使用 6 条训练记录和 12 条验证记录，MAE 约为 2.9798 分钟。它和起点使用的验证记录不同；重点是日期范围是否仍接近你的用途，而不是把两个 MAE 直接相减。

### 路线 B：主要关心训练中没出现的新窗口

`config-group-check.json` 只把 group 的验证窗口从 B 换为 A：

```bash
python lesson-05/analysis.py --config lesson-05/config-group-check.json --output lesson-05/artifacts/group-check
```

在起点中，group 用 A 训练、B 验证；在这次检查中，group 用 B 训练、A 验证。两次训练集和验证集仍没有共同窗口，C 仍保留给测试。比较两次 group 的编号、分母和 MAE，并说明结果是否过度依赖某一个验证窗口。

报告只需重点解释与你主要用途相符的检查，并保留实际引用的配置和结果文件。

## 7. 写报告并完成提交检查

`report.md` 最少写清：

1. 两个用途各自对应什么划分；
2. time 与 group 的训练编号、验证编号、分母、共有窗口数和 MAE；
3. time 的一次 MAE 手算；
4. 小票字段为什么造成目标泄漏；
5. 运行前写下的改变条件；
6. 个人检查的结果、一条支持证据和一条限制证据；
7. 最终保留、限制或暂停什么建议。

填写 `contract.json` 的六个空字段。把准备保留的设置写回 `config.json`，但不要把 `evaluation_split` 改为 `test`。完成实际工作后，将 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py run 05
python scripts/course.py check 05
git add lesson-05
git add -f lesson-05/artifacts
git diff --cached --name-only
```

确认报告、任务说明、配置副本和报告引用的结果都在列表中。`artifacts/` 默认被 Git 忽略，所以需要 `git add -f`。这些命令只准备本地提交，不会自动上传；后续按 [操作与提交步骤](../docs/WORKFLOW.md) 操作。

## 卡住时怎样继续

- 找不到脚本：确认当前目录同时包含 `scripts/` 和 `lesson-05/`。
- JSON 报错：运行 `python -m json.tool lesson-05/config-mine.json`，按提示的行列检查英文双引号、逗号和冒号。
- 运行失败后仍看到旧文件：不要把旧结果当作新结果，修正后换一个新输出目录重跑。
- 暂时无法运行：先按第 2–4 节完成编号、分母和手算，明确标记“尚未运行”，保留完整报错，环境修复后再补跑。

入门支持和必做任务使用同一完成标准。完成这条路径后，不需要再做一份重复的 Core 作业。

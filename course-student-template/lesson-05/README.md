# 第 05 课（S03）：怎样划分数据，才能让验证更接近实际使用

## 本课要解决什么问题

食堂希望用排队人数预测等待时间。这里的**模型（model）**是根据输入计算预测值的规则，**预测值（prediction）**是模型给出的估计结果。输入的排队人数称为**特征（feature）**，希望预测的实际等待时间称为**标签／目标值（label / target）**。**模型参数（model parameter）**是决定模型怎样计算的数值，例如直线模型的截距和斜率。

用来确定模型中计算规则的数据称为**训练集（training set）**，用来比较方案的数据称为**验证集（validation set）**。但“将来使用”可能指两件不同的事：

1. 预测 A、B、C 这些**已经在训练数据中出现过的取餐窗口**在较晚日期的等待时间；
2. 预测一个**训练数据中没有出现过的新取餐窗口**。

这两个用途需要不同的验证方法。本课保持预测模型不变，只比较“按日期先后划分”、“按窗口分开”和“随机分配记录”三种做法；它们的标准名称和完整含义在下一节逐一解释。**平均绝对误差（mean absolute error，MAE）**是先取每条“预测值减实际值”的绝对值，再求平均，单位仍是分钟。不能因为某一行 MAE 最低，就把那种划分宣布为最好。

第一次做时，从 [入门支持](SUPPORT.md) 开始。第一项任务只是写下上面两个用途，并预计各自更适合哪种划分；随后运行现成程序，不要求先写模型代码。你最终提交实际结果、一次 MAE 手算、一项可能改变建议的检查，以及有证据的结论。运行失败时保留命令和完整报错，先按 SUPPORT 的小表继续核对，修复后再补跑。

## 本课要学会什么

| 标准术语 | 通俗解释 | 学会后的表现 |
|---|---|---|
| 训练集、验证集、测试集（training / validation / test set） | 训练集用于拟合模型，也就是用数据确定模型参数；验证集用于比较方案；测试集在方案确定后才做最后评价 | 能说明一条记录为什么进入其中一部分，并保证测试集不参与选择 |
| 时间顺序划分（time-based split） | 用较早日期训练，用较晚日期验证 | 能判断它是否接近“已有对象的未来日期” |
| 分组划分（group-based split） | 先按用户、设备或窗口等对象分组，再让同一组只进入训练集或验证集的一边 | 能判断它是否接近“训练中没出现的新对象” |
| 随机划分与随机种子（random split / random seed） | 随机种子让同一次划分可以重现，但不能保证划分符合实际用途 | 不把一次随机划分的最低 MAE 当作普遍结论 |
| 数据泄漏与目标泄漏（data leakage / target leakage） | 预测时拿不到的信息进入模型，或答案的近似值混入输入 | 能解释为什么“结束后小票时间”得到的低误差不能采用 |

本课继续使用前面已经学过的平均绝对误差（MAE）：把验证集中每条记录的绝对误差相加，再除以验证记录数。比较 MAE 前，必须先确认验证对象和分母是否相同。

## 90 分钟安排

- 0–12 分钟：读情境，写下两个使用问题和预计采用的划分。
- 12–28 分钟：运行保存起始设置的配置文件，找到 `comparison.csv` 和 `summary.json`，核对训练数、验证数和记录编号。
- 28–45 分钟：手算 time 行的 MAE，解释小票字段造成的目标泄漏。
- 45–65 分钟：根据自己选择的用途，完成日期边界检查或分组对象检查。
- 65–75 分钟：写一条支持证据、一条限制证据和最终建议。
- 75–90 分钟：完成 A 版概念检查、AI 学习、B 版概念检查和提交。

到第 30 分钟仍未生成结果时，先按 SUPPORT 中的参考表完成编号和 MAE 核对，并明确写“尚未运行”；把命令与报错交给教师，之后补跑。参考数字只用于排错，不能冒充自己的实验结果。

## 完成步骤

### 1. 先写用途和预计，再运行

在 `lesson-05/report.md` 的第 1 节先回答：

- 如果要预测已有取餐窗口的较晚日期，我预计哪种划分更合适？
- 如果要预测训练中没出现的新取餐窗口，我预计哪种划分更合适？
- 我这次主要准备支持哪一个用途？

然后在学生仓库根目录运行。根目录是同时能看到 `scripts/` 和 `lesson-05/` 的目录。

```bash
python scripts/course.py start 05
python lesson-05/analysis.py --config lesson-05/config-start.json --output lesson-05/artifacts/support-start
```

本页命令使用 `python`。如果终端提示找不到该命令，而 `python3 --version` 能显示版本，就把本页所有 `python` 改成 `python3`。不要在 Python 的 `>>>` 提示符中粘贴这些命令。

成功标志是终端出现“结果写入”。先打开 `lesson-05/artifacts/support-start/comparison.csv`。**CSV（comma-separated values）**是用行和列保存表格的文本文件，可以用电子表格软件或文本编辑器打开。先看：

- `train_n` 是训练记录数；
- `n` 是验证记录数，也是该行 MAE 的分母；
- `shared_sites` 是训练集与验证集都出现过的取餐窗口数；
- `mae` 的单位是分钟。

再打开 `summary.json`。**JSON（JavaScript Object Notation）**是使用字段名保存结构化数据的文本格式；本课只要按字段名查找，不需要背语法。在 `details.splits.time` 和 `details.splits.group` 中查看 `train_ids`、`evaluation_ids`、`train_sites` 和 `evaluation_sites`。这些字段说明每个数到底由哪些记录计算出来。

### 2. 比较两个用途，不按最低 MAE 选划分

起始结果中：

- time 用 A、B、C 的第 1–4 天训练，用同三个窗口的第 5–6 天验证；
- group 用 A 的第 1–6 天训练，用 B 的第 1–6 天验证；
- 第 7–8 天的保留测试记录不用于训练模型或选择方案。

在报告表格中分别填写 time 和 group 的训练编号、验证编号、`shared_sites`、分母和 MAE。time 更接近“已有窗口的较晚日期”；group 更接近“训练中没出现的新窗口”。它们使用的验证记录不同，因此两个 MAE 不能当作同一场比赛的名次。

### 3. 手算一次 MAE，并识别目标泄漏

在 `records.csv` 中找到 time 的 A05、A06、B05、B06、C05、C06。把六个 `absolute_error` 相加，再除以 6，与 `comparison.csv` 的 time 行核对。报告必须写出加法、分母和单位。

再看 B05。正常预测只使用加入队伍时知道的排队人数；`leaked_prediction_demo` 使用了结束后才出现的 `receipt_minutes`。这个小票时间等于真实等待时间加 0.25 分钟，因此几乎直接暴露了标签。`leaked_mae_demo=0` 是目标泄漏反例，不是优秀模型。

### 4. 运行现成对照，学会读“只改一项”

下面的配置只把时间划分的训练截止日从第 4 天提前到第 3 天：

```bash
python lesson-05/analysis.py --config lesson-05/config-support.json --output lesson-05/artifacts/support-compare
```

核对 time 的训练记录从 12 条变为 9 条、验证记录从 6 条变为 9 条。group 和 random 不应变化。两次 time 使用的验证编号和分母不同，所以不能把 MAE 的差直接写成“模型在同一批样本上提高或下降了多少”。

### 5. 根据主要用途完成一项检查

运行前先在报告中写明：什么结果会让你限制或暂停原建议。然后选择与主要用途相符的一项。

**如果主要用途是已有窗口的未来日期：检查时间边界。**

从 `config-start.json` 复制出 `config-mine.json`，只把 `train_through_day` 改为 `2`。先检查 JSON 格式，再运行：

```bash
python -m json.tool lesson-05/config-mine.json
python lesson-05/analysis.py --config lesson-05/config-mine.json --output lesson-05/artifacts/my-check
```

检查 time 的训练编号是否变为 A01–A02、B01–B02、C01–C02，验证编号是否变为各窗口的第 3–6 天。说明新的验证日期是否仍接近你准备预测的日期。

**如果主要用途是训练中没出现的新窗口：检查验证窗口。**

运行已经准备好的 `config-group-check.json`。它只把 group 的验证窗口从 B 换为 A，因此训练窗口相应从 A 换为 B；C 仍保留给测试。

```bash
python lesson-05/analysis.py --config lesson-05/config-group-check.json --output lesson-05/artifacts/group-check
```

比较两次 group 的 `train_sites`、`evaluation_sites`、验证编号和 MAE。两次 MAE 来自不同窗口，不能写成同一样本上的性能升降。若结论只在某一个验证窗口上成立，应限制“可用于所有新窗口”的说法。

### 6. 保存主结果并检查提交

把你准备保留的设置写回 `config.json`。如果主要支持新窗口，把 `split_strategy` 写为 `group`；这只决定 `summary.json` 的 `metrics` 汇总哪一行，不会自动证明 group 更好。不要把 `evaluation_split` 改成 `test`，本课保留测试集，不用它拟合模型或选择方案。

完成 `report.md` 和 `contract.json`，再把 `submission.json` 的 `status` 改为 `complete`：

```bash
python scripts/course.py run 05
python scripts/course.py check 05
git add lesson-05
git add -f lesson-05/artifacts
git diff --cached --name-only
```

最后一条命令只列出准备提交的文件。确认报告中引用的配置副本和结果目录也在列表中；检查通过不等于文件已经上传。提交与标签步骤见 [操作与提交步骤](../docs/WORKFLOW.md)。

## 必须提交什么

- `analysis.py` 和实际使用的 `config.json`；
- `artifacts/summary.json`、`comparison.csv` 和 `records.csv`；
- 本人检查使用的配置副本与对应结果目录；
- 填写完成的 `contract.json` 和 `report.md`；
- 保持课号不变、状态改为 `complete` 的 `submission.json`。

报告需要回答：两个用途分别对应什么划分；每行 MAE 使用哪些验证记录和什么分母；time 的手算如何得到；小票字段为什么构成目标泄漏；运行前写了什么改变条件；个人检查得到什么；最后保留、限制还是暂停哪项建议。

## 不同起点怎么做

### 入门支持（Support）：沿着完整路径完成必做任务

按 [SUPPORT.md](SUPPORT.md) 运行起点、现成日期对照和与你用途相符的个人检查。可以使用教师或 AI 帮助理解命令，但必须自己核对记录编号、分母和一项计算。使用支持路径不降低评分，也不用再重复做一套 Core。

### 必做任务（Core）：让用途、划分和证据对应

比较 time 与 group，手算一次 MAE，解释目标泄漏，并完成日期边界或验证窗口检查。最后分别写出“已有窗口未来日期”和“新窗口”的建议。

### 提高任务（Upgrade）：检查随机划分的波动

运行至少五个随机种子，保存每次 `random` 的训练／验证编号与 MAE，报告最小值、最大值、平均值和**极差（range，最大值减最小值）**。不能只保留最好的一次，也不能用随机划分替代新窗口的分组验证。

### 换数据重测（Transfer）：换成有重复测量的数据

**重复测量数据（repeated-measures data）**是同一用户、设备或机构拥有多条记录的数据。使用这类数据，按实际用途选择时间顺序划分或分组划分。必须说明一行数据代表什么、分组对象是什么、预测时已经知道哪些信息。

### 自选拓展（Open extension）：同时检查时间和对象变化

设计“较晚日期的新对象”评价方案，说明时间变化和对象变化是否被混在一起，以及还需要什么数据才能把两种影响分开。

## 运行限制

使用 Python 3.10 以上和仓库已安装的 NumPy 数值计算库。本课只有 24 条为教学目的生成的数据，普通 CPU 即可；单次运行通常不到 1 分钟，不需要 GPU、付费模型或联网。这些数据只能解释划分、MAE 和泄漏机制，不能证明真实食堂、真实用户或任何 AI 系统的表现。AI 学习和在线概念检查需要网络，无法连接时按教师安排补做。

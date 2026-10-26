# 第09课 · 从运行程序到读懂结果

## 1. 先运行一次完整比较

在学生仓库根目录运行。这个目录里应有 `lesson-09`、`data` 和 `scripts`。

```bash
python3 lesson-09/analysis.py --compare --output lesson-09/artifacts/first-comparison
```

程序会使用相同的训练记录，分别建立线性模型和浅树，再用相同的验证记录检查预测。默认使用五个字段，树深度为2。

如果提示结果目录不是空的，换一个新名字，例如 `second-comparison`。这样可以保留旧结果，之后知道自己改过什么。

## 2. 先打开哪个文件？

结果在命令中指定的目录里。三个文件可以按下面的顺序看。

### summary.json：先看整体

JSON（JavaScript Object Notation）是一种保存数据的格式，可以用编辑器打开，也可以请AI整理成表格。

找到两种模型的平均绝对误差（mean absolute error，MAE）。它表示每小时的预测平均偏离实际多少次租借。较小的值表示本批验证记录中平均偏差较小。

### records.csv：再看具体小时

CSV（comma-separated values，逗号分隔值）可以用表格软件打开。每行有：

|字段|含义|
|---|---|
|instant|这个小时在原数据中的编号|
|method|使用哪一种模型|
|actual|实际租借次数|
|prediction|预测租借次数|
|absolute_error|预测与实际相差多少次，不带正负号|

同一个 `instant` 会出现两行，因为两种模型都预测了这个小时。它们不是两个不同的小时。

先任选一个编号，检查“预测值与实际值相减后取绝对值”，是否等于 `absolute_error`。这样能确认自己没有读错列。

### trace.json：最后追一条预测

它记录默认第一条验证记录的预测过程。线性各项怎样相加、树怎样分组，见[LEARN第7节](LEARN.md#7-怎样核对一条真实预测)。

## 3. 想检查另一条记录，怎样选？

从 `records.csv` 找到想检查的 `instant`，在命令里加 `--trace-id`。

例如，你选中了编号14774，可以运行：

```bash
python3 lesson-09/analysis.py --compare --trace-id 14774 --output lesson-09/artifacts/trace-14774
```

这个编号只是演示命令怎样写，不要求你选它。你应选择与自己的问题有关的验证记录，并说明理由。

更换追踪编号只改变 `trace.json` 重点展示哪一条记录，不改变训练和评价用的数据。训练集或旧测试集中的编号不能用于这里。

## 4. 想看“工作日高峰”，怎样筛选？

先把条件说清楚。例如，定义为“工作日，并且小时是8、17或18”。

`records.csv` 没有小时和工作日字段。这些信息在 `data/bike/hour.csv` 中，可以按相同的 `instant` 编号把它们补到结果表旁边：

- `dteday` 是日期；
- `hr` 是小时；
- `workingday` 中1表示工作日。

可以用表格软件查找，也可以请AI写代码合并。合并后抽查一个编号，确认两边对应的是同一小时。只保留本次验证结果中的编号，不把训练或旧测试记录加进来。

然后按你的条件筛选，分别计算两种模型的MAE：


$$
\text{这一组的MAE}=\frac{\text{选中小时的绝对误差合计}}{\text{选中小时数}}.
$$

例如，某模型在三个选中小时的误差是10、20、30次，MAE就是20次/小时。另一模型也必须用这三个小时，单独求平均。

不要把两模型的六行一起平均，也不要只留下预测好的小时。报告中同时写出选中了多少个小时；一个都没选中时，应写“没有可比较记录”，而不是“误差为0”。

## 5. 想改字段或树深度，怎样做？

复制 `lesson-09/config.json`，另存为 `lesson-09/my-config.json`，再修改新文件。

- `fields` 是两种模型共同使用的输入字段；
- `depth` 是树最多经过几次分组，可选1至5。

允许使用的字段是 `hr`、`workingday`、`temp`、`hum`、`windspeed`。

不要把 `casual` 和 `registered` 放进输入：它们相加就是要预测的 `cnt`，等于提前把答案给了模型。`instant` 是记录编号，也不作为预测输入。

运行自己的配置：

```bash
python3 lesson-09/analysis.py --compare --config lesson-09/my-config.json --output lesson-09/artifacts/my-comparison
```

比较新旧设置时，先只改一项，会更容易说明结果变化的原因。如果同时改了很多项，只能比较整套方案，不能轻易说是某一项导致了改善。

## 6. 报告和两个JSON文件分别做什么？

`report.md` 是你给读者看的分析。可以直接用[现成提纲](report.md)，写问题、比较、一次预测的计算、建议和限制。

`contract.json` 是开始时的简短计划，不是另外一篇报告：

|字段|写什么|
|---|---|
|question|想弄清什么问题|
|user|结果准备给谁参考|
|data_source|使用什么数据|
|metric|主要用什么指标比较|
|split_plan|哪些记录训练，哪些记录验证|
|initial_expectation|看结果之前有什么猜想|

猜想与结果不同没有关系，在报告中解释即可。如果问题是看过结果后才提出的，也应照实说明。

`submission.json` 则供检查程序使用。它需要知道：运行哪条命令，结果在哪些文件里，报告在哪里。

例如，如果正式分析采用上面的自定义配置，`run` 应按词拆成数组：

```json
["python3", "lesson-09/analysis.py", "--compare", "--config", "lesson-09/my-config.json", "--output", "lesson-09/artifacts/my-comparison"]
```

`artifacts` 应列出这个命令生成的三个文件：该目录下的 `summary.json`、`records.csv` 和 `trace.json`。若另外生成了分组比较结果，也把相应文件及生成步骤纳入自己的正式程序和提交声明。

## 7. 提交前怎样检查？

先确认报告里的数字能在结果文件中找到，再把 `status` 改为 `complete`，运行：

```bash
python3 scripts/course.py check 09
```

还可以运行本地重现检查：

```bash
python3 scripts/course.py ci
```

它会按课程规则检查已启用的课次，并在临时副本中重新生成已完成课次声明的结果，不需要你删除原来的文件。

检查通过说明文件和运行过程符合要求，不代替对分析内容的判断。最后按[课程提交流程](../docs/WORKFLOW.md)提交即可。

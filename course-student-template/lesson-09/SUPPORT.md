# 卡住时再看：运行、选记录、提交

## 想先运行两种模型

从学生仓库根目录运行：

```bash
python3 lesson-09/analysis.py --compare --output lesson-09/artifacts/example
```

它用相同训练/验证记录，给两方相同字段，默认树深度2。它只完成拟合和预测，不替你选择失败问题、分组、评价重点或建议。若自己实现，仍保持这些公平条件。

想改设置，复制config.json为my-config.json。fields列两方共同使用的字段；允许hr、workingday、temp、hum、windspeed。depth是树一条路径最多经过几次分组，可选1–5。不要使用目标cnt的组成项casual、registered，或把instant编号当业务输入。

```bash
python3 lesson-09/analysis.py --compare --config lesson-09/my-config.json --output lesson-09/artifacts/my-comparison
```

## 不知道输出里看什么

JSON 文件可用平时写代码的编辑器打开，CSV 文件可用表格软件打开，或请 AI 帮你读取。文件名不是统计概念：`summary` 是汇总，`records` 是逐条结果，`trace` 是一次预测的计算记录。

|文件|先看什么|
|---|---|
|summary.json|两方法在相同验证记录上的MAE；值小表示平均少错一些|
|records.csv|instant是原记录编号；actual实际值、prediction预测、absolute_error绝对差|
|trace.json|linear_columns按顺序标出截距与所选字段（默认共六项）；tree给分组路径与叶均值，详见LEARN|

默认追踪第一条验证记录。若它不属于你要研究的情形，从records.csv选自己的instant，再在比较命令里加`--trace-id 你的编号`，输出到新目录。此参数只换追踪哪条记录，不改变两方训练或评价的记录。训练部分或旧测试部分的ID会被拒绝。

要算自己的分组，先写清规则，例如“工作日且小时为8、17或18”。`records.csv` 中的 `method` 区分模型；一个小时的 `instant` 在两种模型里相同。默认文件没有日期和小时，要从 `data/bike/hour.csv` 中按这个编号找回 `dteday`（日期）、`hr`（小时）和 `workingday`（是否工作日）。只保留已经出现在本次验证结果中的编号，不把其他日期的记录加进来。可以请 AI 帮你完成这一步，但要抽查一条编号是否对应正确。

对选中小时，分别将每个模型的 `absolute_error` 加起来，再除以小时数。例如三个小时的误差是10、20、30次，MAE就是20次/小时。两种模型必须用同样的小时，且分别计算，不能把两种模型的六行混在一起平均。写明一共有多少个小时；如果没有选中记录，应写“本次没有可比较的记录”，不能填误差0。不要只留下预测好的小时。算法源码在mlcourse/bike_models09.py，是否阅读由你的问题决定。

## 怎样算完成并交给别人重跑

只得到example输出尚未完成。还要有自己的两项选择、一条计算核对、公平比较和限制，写在同一份report.md。`contract.json` 是开始实验时的简短计划，不是额外一篇报告。里面的 `question` 写想弄清什么，`user` 写结果给谁用，`data_source` 写数据来源，`metric` 写主要比较什么（例如所选时段的 MAE），`split_plan` 写哪些记录用于训练、哪些用于比较，`initial_expectation` 写看结果前的猜想。猜错不等于任务失败，报告中解释结果即可。submission.json的run填从学生根目录执行的命令，artifacts列它产生的文件。

均值起点生成summary.json、records.csv；--compare还生成trace.json，三者都要列入。自己另写程序时按实际输出修改。命令要写成 `run` 数组，每个词或参数单独一项；具体格式可对照[提交流程](../docs/WORKFLOW.md)。保存结果的目录名必须与 `artifacts` 中的路径一致。完成后把status改为complete，用`python3 scripts/course.py check 09`检查文件；本地`python3 scripts/course.py ci`会在临时副本中删除清单结果再重跑。它只证明文件和重现，不评判理解或作品质量。

直接重复同一非空输出目录会报错，这是为了保留旧证据。改用新目录，或按上述临时副本流程重现；不要删除原作品来凑通过。

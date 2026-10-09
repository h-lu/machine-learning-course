# 第 8 课操作支持：按当前问题查阅

任务与交付结果集中在 [README](README.md)。这里说明怎样读取结果、实现比较、最后测试和提交；理解计算看 [LEARN](LEARN.md)，算错时看 [HINTS](HINTS.md)。

## 启动并读取结果

在学生仓库根目录运行：

```bash
python lesson-08/analysis.py
```

沿用课程中已经成功的 `python`、`python3` 或 `py`。环境检查见 [ENVIRONMENT](../ENVIRONMENT.md)。成功后打开 `lesson-08/artifacts/baseline/`：

- `comparison.csv`：查看 `method`、验证记录数 `n`、平均绝对误差 `mae`。
- `records.csv`：选一行，核对观测次数 `cnt`、预测 `prediction` 和绝对误差 `err_absolute`。

默认只有训练均值基线，没有候选或测试误差；它帮助确认数据和环境已通。程序失败时保留完整命令与报错，确认查看的是哪次输出。

可选缺失值热身：`python scripts/lesson08.py warmup --output lesson-08/artifacts/warmup`。它只用人工排队训练记录演示 `13/9` 人的填补和规则预测，不是今天的真实模型比较。字段与计算见 [DATA](data/DATA.md#人工热身)。

## 实现两个匹配的方案

`analysis.py` 的 `candidate_predictions(train_inputs, train_targets, evaluation_inputs)` 收到训练输入、训练 `cnt` 和评价输入。评价输入不含 `cnt`、`casual`、`registered`、`instant`。你可在函数里实现原方案和候选，返回 `{自定原方案名: 预测列表, 自定候选名: 预测列表}`；每列与评价记录顺序一致、长度相同。也可另写自己的程序。

从训练数据计算处理参数、拟合模型，评价记录沿用这些参数。默认 `baseline` 名称保留给均值参照。例如检查小时表示时，应另实现“单项线性小时回归”和“小时指示变量回归”，保持其他输入、算法和处理规则相同。LEARN 第 2–4 节解释两者怎样计算。

本次计划可放在 `report.md`，或用 `--plan` 指向自己的文件。说明要检查的原因、唯一改动、评价和选择依据即可；课堂没有统一阈值或外部注册要求。

`scripts/lesson08.py bike` 是已实现的可选示例工具。它有两项预设比较，可阅读或改写；它的本地计划 JSON、数值规则和命令只适用于这个接口。采用该工具时查 [DATA 完整调用资料](data/DATA.md#可选示例工具的完整调用资料)，在报告中说明给定部分与自己改变、检查的部分。

## 核对一条预测和一个分组

选一条真实记录，保存输入、处理后的数值、预测与观测值。若是回归模型，核对一列贡献并加上截距与其他贡献；若是规则模型，说明触发了哪条规则。带符号误差是预测减观测值；绝对误差取绝对值。

再选与用途有关的分组，或改变某项输入检查预测变化。核算至少 5 条记录，或选定分组的全部记录。完整小组少于 5 条也可保留检查，并说明结果可能不稳定；无记录的组写“不可评估”。抽查与整组要分别标明。

合并分组 MAE 按记录数加权。固定模型、改变输入的检查反映预测敏感性，不能直接说明现实干预的因果效果。可选工具的 `feature_trace.csv` 和 `group_metrics.csv` 字段见 DATA。

## 最后测试

根据验证结果先在报告中写选定方法、参数和理由，再运行：

```bash
python lesson-08/analysis.py --split test --decision lesson-08/report.md --selected-method 你的方法名 --output lesson-08/artifacts/test
```

把“你的方法名”换成 `comparison.csv` 的 `method` 列中已选的方法名。显式输出目录必须是新目录。起点只报告所选方法，不替你作选择；选择文件的非空检查也不验证其中理由是否正确。也可在自己的程序中读取测试并评价已选方案。

若根据测试又改了方法，这批测试已参与开发，修改后的方法需要新的独立数据评价。建议暂停使用与选一个方法作最后评价是不同判断，报告中分别说明即可。

## 保存报告与提交清单

`contract.json` 保留课号 `lesson-08`，填写问题、使用者、来源、指标与单位、划分和事前预计。报告包含计划、两方案比较、独立核算、选择与建议即可，结构可以自定。

`submission.json` 的 `run` 写重新生成**主要验证结果**的命令，`artifacts` 列这些命令能够重生成的文件。默认两项都只对应均值基线，完成自己的比较后需更新。只由验证命令重生成的清单不要混入另存的测试文件；测试结果、测试前选择和其他报告引用文件仍需保存，在报告中给路径。自动重现会先移除清单中的文件，再按 `run` 重生成并核对，不会自动判断实验是否合理。

主要结果已生成后，将 `status` 改为 `complete`，在根目录检查并保存：

```bash
python scripts/course.py check 08
git add lesson-08
git add -f lesson-08/artifacts
git diff --cached --name-only
```

已有结果不需要再运行一次 `run 08`。需要重算且命令有显式 `--output` 时，先换新结果目录并同步 `run`、`artifacts`；自动重现会在临时副本中重算清单，不覆盖原目录。

核对待提交列表包括程序、配置、报告、计划、选择和引用结果；改过的共享代码也要保存。之后按 [WORKFLOW](../docs/WORKFLOW.md) 提交并创建本课 `v2-l08-final` 标签。不会 JSON 时可用 `python -m json.tool 文件路径` 检查格式；运行尚未完成则记录实际进展和报错，修复后补跑。

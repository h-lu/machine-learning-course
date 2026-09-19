# S06 数据、参数和结果说明

数据由课程人工构造，用于练习本课方法。S01/S03/S04 共用 24 条样本；S06 只隐藏其中部分人数，不改变标签。 隐藏 A02/B03/C04/A05/B06/C07 的人数；没有在输入中保留被隐藏的数值。

JSON 用带字段名的文本保存数据，顶层 `rows` 是样本列表，共 24 条。不要用课程文件中的人工数值说明真实食堂情况。

| 字段 | 含义 |
|---|---|
| `id` | 样本编号，不作为模型特征 |
| `queue_length` | 加入队伍时前面的人数；预测特征 |
| `wait_minutes` | 实际等待分钟数；事后核对的标签 |
| `period` | 午间或晚间；分组评估，S06 可作为特征 |
| `site` | 虚构窗口 A、B、C；S03 的分组对象 |
| `day` | 记录对应的第几天；S03 用于时间划分 |
| `split` | train=训练，validation=验证，test=保留测试 |

人数必须是非负整数。本课人数允许 `null`，填补后可为小数；标签仍是已观察的非负分钟数。

## 参数怎样影响实验

`config.json` 用于最终重跑；`config-start.json` 保留入门起点；`config-support.json` 是已经准备好的单项对照。入门步骤见 [SUPPORT.md](../SUPPORT.md)。`config-trial.json` 或 `config-mine.json` 是自己的配置副本。不要整份复制其他课的配置；未知字段会明确报错。

| 参数 | 含义 |
|---|---|
| `seed` | 固定随机划分或抽样；本课无随机步骤时不改变结果；默认 `7` |
| `evaluation_split` | 指定 validation 或 test；默认只评价验证集；默认 `validation` |
| `change` | imputation=只改填补；period_feature=只加晚间特征，填补仍为 0；默认 `imputation` |
| `stress_queue_shift` | 只给已知人数加多少人，模拟记录错误；模型不重训；默认 `3` |

## 怎样读结果

`comparison.csv` 一行一种方案；`method` 是程序代号，`method_name` 是中文名称，`n` 是该行统计使用的样本数。`records.csv` 保留逐条输入与输出。同一编号出现多次，是不同方法对同一条样本计算，不是新增独立样本。

常用列：`actual` 为真实分钟数，`prediction` 为预测分钟数，`absolute_error` 为两者绝对差。`mae` 是这批绝对误差的平均。CSV 空白和 JSON `null` 表示没有值，不能自行改为零。

`original` 是当前数据上重跑的原方案，`candidate` 是只改一个因素的候选。`queue_missing` 指示原人数是否缺失，`queue_after_imputation` 为进入模型的值。`train_mae` 与当前评价 MAE 分开报告。`details.models` 记录填补值、特征和参数；`by_missing` 与 `by_period` 保存分组结果。

`summary.json` 保存完整结果和输入、配置、源码哈希；`metrics` 只是一份指定主要方案的汇总，不是自动推荐。`comparison` 保存其余方案；`stress_test` 是改变一个条件的检查。哈希帮助核对文件变化，不能证明来源真实。兼容输出中出现但本课未使用的指标不要求背诵。

每次换配置或数据使用新的 `--output` 目录。错误退出后旧文件可能还在，不能把它们算作新运行结果。程序不自动把提交状态改为完成。数据可由 `mlcourse/foundations_data.py` 的 `example_data` 重建；完整批量脚本只能输出到新的空目录，不能覆盖自己的实验。

## original 与 S01 的关系

本程序不会读取 S01 的个人配置。这里的 `original` 专指本课提供的“缺失人数填 0 后拟合一元线性回归”，不一定是你在 S01 选择的模型。入门路径可以用它作为本次改进的起点，但报告要说明这个起点与 S01 方案是否相同；若不同，不能把本次差异说成自己原方案的提升。要评价自己在 S01 选择的规则或均值基线，应在当前数据上重新运行它，并与候选使用相同的评价样本，不能直接比较两课旧分数。

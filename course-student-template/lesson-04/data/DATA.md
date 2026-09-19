# S02 数据、参数和结果说明

数据来源：人工教学数据，不代表真实人群、因果效果或 AI 能力。 available_day 是记录上传日期，不是等待了几天；代理值和复核值均人工编写，不是实际 AI 输出。

JSON 用带字段名的文本保存数据，顶层 `rows` 是样本列表，共 8 条。不要用课程文件中的人工数值说明真实食堂情况。

| 字段 | 含义 |
|---|---|
| `id` | 样本编号，不作为模型特征 |
| `queue_length` | 加入队伍时前面的人数；预测特征 |
| `wait_minutes` | 实际等待分钟数；事后核对的标签 |
| `period` | 午间或晚间；分组评估，S06 可作为特征 |
| `site` | 虚构窗口 A、B、C；S03 的分组对象 |
| `day` | 记录对应的第几天；S03 用于时间划分 |
| `available_day` | 真实标签上传日期；截止日之后的值不参与当前统计；null 表示始终未收到 |
| `proxy_minutes` | 人工估计，模拟代理标签；不是实际 AI 输出 |
| `review_minutes` | 另一份人工复核分钟数；在真实标签可见后才进行比较 |

观察截止日不能早于这批样本最晚的发生日（默认第 4 天），避免把还未发生的记录混进已发生总体。`later_day` 不得早于 `observation_day`。

人数必须是非负整数。标签是非负分钟数。本课的 `wait_minutes` 与 `available_day` 可同时为 `null`；未知不等于零。当前输出隐藏截止日后才上传的真实标签，延后截止日的比较另见 `stress_test`。

## 参数怎样影响实验

`config.json` 为默认配置，`config-trial.json` 是自己另存的副本。不要整份复制其他课的配置；未知字段会明确报错。

| 参数 | 含义 |
|---|---|
| `seed` | 固定随机划分或抽样；本课无随机步骤时不改变结果；默认 `7` |
| `observation_day` | 统计截止到第几天已上传的标签；默认 `4` |
| `later_day` | 用来比较的更晚截止日，不得早于 observation_day；默认 `7` |
| `disagreement_minutes` | 两份已知标注相差超过多少分钟才记为分歧；等于容差不算超过；默认 `2.0` |

## 怎样读结果

`comparison.csv` 一行一种方案；`method` 是程序代号，`method_name` 是中文名称，`n` 是该行统计使用的样本数。`records.csv` 保留逐条输入与输出。同一编号出现多次，是不同方法对同一条样本计算，不是新增独立样本。

本课不是训练模型，`records.csv` 使用 `observed_minutes`、`proxy_minutes` 和 `review_minutes` 区分已观察标签、代理估计与另一份复核值。`visible` 表示当前是否收到真实标签。CSV 空白和 JSON `null` 表示没有值，不能自行改为零。

本课不预测新分钟数：逐条表使用 `visible`（截止日是否收到）、`observed_minutes`（已收到的真实标签）、`proxy_minutes`、`review_minutes` 和 `disagreement`。`n` 是该处理实际使用的标签数，不同处理的均值含义不同。`coverage` 分母是全部 8 条；`agreement` 分母只包括已知且有复核值的配对，不是所有记录。没有配对时保持为空。

`summary.json` 保存完整结果和输入、配置、源码哈希；`metrics` 只是一份指定主要方案的汇总，不是自动推荐。`comparison` 保存其余方案；`stress_test` 是改变一个条件的检查。哈希帮助核对文件变化，不能证明来源真实。兼容输出中出现但本课未使用的指标不要求背诵。

每次换配置或数据使用新的 `--output` 目录。错误退出后旧文件可能还在，不能把它们算作新运行结果。程序不自动把提交状态改为完成。数据可由 `mlcourse/foundations_data.py` 的 `example_data` 重建；完整批量脚本只能输出到新的空目录，不能覆盖自己的实验。

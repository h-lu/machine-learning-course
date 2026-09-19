# S04 数据、参数和结果说明

数据来源：人工教学数据，不代表真实人群、因果效果或 AI 能力。 S01/S03/S04 共用 24 条样本；S06 只隐藏其中部分人数，不改变标签。

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

人数必须是非负整数。标签是非负分钟数。

## 参数怎样影响实验

`config.json` 为默认配置，`config-trial.json` 是自己另存的副本。不要整份复制其他课的配置；未知字段会明确报错。

| 参数 | 含义 |
|---|---|
| `seed` | 固定随机划分或抽样；本课无随机步骤时不改变结果；默认 `7` |
| `evaluation_split` | 指定 validation 或 test；默认只评价验证集；默认 `validation` |
| `primary_model` | 主要汇总：baseline、linear 或 buffered；不是自动推荐；默认 `linear` |
| `buffer_minutes` | 在回归预测上增加的分钟数，不重新拟合模型；默认 `4.0` |
| `underestimate_weight` | 低估的权重，至少为 1；高估权重固定为 1；默认 `3.0` |
| `long_wait_minutes` | 实际等待达到此值为正类（需要提醒）；默认 `8.0` |
| `alert_threshold` | 预测达到此值才进入提醒候选，单位分钟；默认 `8.0` |
| `capacity` | 实际可提醒的名额，0 到评价样本数之间的整数；默认 `2` |
| `stress_capacity` | 保持预测不变，用来检查另一种容量；默认 `1` |

## 怎样读结果

`comparison.csv` 一行一种方案；`method` 是程序代号，`method_name` 是中文名称，`n` 是该行统计使用的样本数。`records.csv` 保留逐条输入与输出。同一编号出现多次，是不同方法对同一条样本计算，不是新增独立样本。

常用列：`actual` 为真实分钟数，`prediction` 为预测分钟数，`absolute_error` 为两者绝对差。`mae` 是这批绝对误差的平均。CSV 空白和 JSON `null` 表示没有值，不能自行改为零。

`asymmetric_loss` 是按当前低估权重算的加权误差，不能冒充实际损失分钟数；`weighted_error` 为逐条对应值。`alerts` 是实际提醒数，`eligible` 是达到阈值的候选数，`tp/fp/fn/tn` 为正确提醒、误报、漏报和正确不提醒。排序使用预测值，并列按编号，绝不使用真实标签选名额。`long_wait` 是真实类别，`alert` 是实际决定。

`summary.json` 保存完整结果和输入、配置、源码哈希；`metrics` 只是一份指定主要方案的汇总，不是自动推荐。`comparison` 保存其余方案；`stress_test` 是改变一个条件的检查。哈希帮助核对文件变化，不能证明来源真实。兼容输出中出现但本课未使用的指标不要求背诵。

每次换配置或数据使用新的 `--output` 目录。错误退出后旧文件可能还在，不能把它们算作新运行结果。程序不自动把提交状态改为完成。数据可由 `mlcourse/foundations_data.py` 的 `example_data` 重建；完整批量脚本只能输出到新的空目录，不能覆盖自己的实验。

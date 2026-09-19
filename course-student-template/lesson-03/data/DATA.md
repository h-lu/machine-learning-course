# S01 数据、参数和结果说明

数据由课程人工构造，用于练习本课方法。S01/S03/S04 共用 24 条样本；S06 只隐藏其中部分人数，不改变标签。

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

`config.json` 用于最终重跑；`config-start.json` 保留入门起点；`config-support.json` 是已经准备好的单项对照。入门步骤见 [SUPPORT.md](../SUPPORT.md)。`config-trial.json` 或 `config-mine.json` 是自己的配置副本。不要整份复制其他课的配置；未知字段会明确报错。

| 参数 | 含义 |
|---|---|
| `seed` | 固定随机划分或抽样；本课无随机步骤时不改变结果；默认 `7` |
| `evaluation_split` | 指定 validation 或 test；默认只评价验证集；默认 `validation` |
| `primary_model` | 主要汇总对象：baseline=均值基线，rule=人工规则，linear=线性回归；报告可得出不采用的结论；默认 `linear` |
| `rule_intercept` | 人工规则固定分钟数；默认 `1.0` |
| `rule_slope` | 规则中每多 1 人增加的分钟数；默认 `2.0` |
| `alert_minutes` | 预测达到多少分钟时提醒；包含恰好等于阈值；默认 `8.0` |
| `stress_queue` | 没有真实标签的新人数，只作输入检查；默认 `10` |

## 怎样读结果

`comparison.csv` 一行一种方案；`method` 是程序代号，`method_name` 是中文名称，`n` 是该行统计使用的样本数。`records.csv` 保留逐条输入与输出。同一编号出现多次，是不同方法对同一条样本计算，不是新增独立样本。

常用列：`actual` 为真实分钟数，`prediction` 为预测分钟数，`absolute_error` 为两者绝对差。`mae` 是这批绝对误差的平均。CSV 空白和 JSON `null` 表示没有值，不能自行改为零。

`summary.json` 保存完整结果和输入、配置、源码哈希；`metrics` 只是一份指定主要方案的汇总，不是自动推荐。`comparison` 保存其余方案；`stress_test` 是改变一个条件的检查。哈希帮助核对文件变化，不能证明来源真实。兼容输出中出现但本课未使用的指标不要求背诵。

每次换配置或数据使用新的 `--output` 目录。错误退出后旧文件可能还在，不能把它们算作新运行结果。程序不自动把提交状态改为完成。数据可由 `mlcourse/foundations_data.py` 的 `example_data` 重建；完整批量脚本只能输出到新的空目录，不能覆盖自己的实验。

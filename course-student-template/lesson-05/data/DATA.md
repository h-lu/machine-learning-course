# S03 数据、参数和结果说明

数据由课程人工构造，用于练习本课方法。receipt_minutes 是结束后小票才有的时间，仅供演示数据泄漏，不能作正常预测特征。

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
| `receipt_minutes` | 结束后小票上的时间，等于人工标签加 0.25；只能用于泄漏反例 |

人数必须是非负整数。标签是非负分钟数。三种划分仅重新安排非 test 行；后两天不会进入任何训练或验证。分组方案只用 A 训练、B 验证、C 后两天测试，其他未用编号在 `details.splits.group.unused_ids`。

## 参数怎样影响实验

`config.json` 用于最终重跑；`config-start.json` 保留入门起点；`config-support.json` 是已经准备好的单项对照。入门步骤见 [SUPPORT.md](../SUPPORT.md)。`config-trial.json` 或 `config-mine.json` 是自己的配置副本。不要整份复制其他课的配置；未知字段会明确报错。

| 参数 | 含义 |
|---|---|
| `seed` | 固定随机划分或抽样；本课无随机步骤时不改变结果；默认 `7` |
| `evaluation_split` | 指定 validation 或 test；默认只评价验证集；默认 `validation` |
| `split_strategy` | 主要划分：time=时间，group=按窗口，random=随机；默认 `time` |
| `train_through_day` | 时间方案训练到第几天；默认 4；默认 `4` |
| `validation_through_day` | 开发数据的最晚日期，默认 6；不能把保留测试日期纳入开发；默认 `6` |

## 怎样读结果

`comparison.csv` 一行一种方案；`method` 是程序代号，`method_name` 是中文名称，`n` 是该行统计使用的样本数。`records.csv` 保留逐条输入与输出。同一编号出现多次，是不同方法对同一条样本计算，不是新增独立样本。

常用列：`actual` 为真实分钟数，`prediction` 为预测分钟数，`absolute_error` 为两者绝对差。`mae` 是这批绝对误差的平均。CSV 空白和 JSON `null` 表示没有值，不能自行改为零。

`train_n` 是训练数量，`shared_sites` 是训练与评价共有窗口数；`leaked_mae_demo` 与 `leaked_prediction_demo` 是违规使用小票后的错误示范。不同划分中的 `n` 和具体编号可能不同，不能把它们当作同一测试上的模型竞赛。

`summary.json` 保存完整结果和输入、配置、源码哈希；`metrics` 只是一份指定主要方案的汇总，不是自动推荐。`comparison` 保存其余方案；`stress_test` 是改变一个条件的检查。哈希帮助核对文件变化，不能证明来源真实。兼容输出中出现但本课未使用的指标不要求背诵。

每次换配置或数据使用新的 `--output` 目录。错误退出后旧文件可能还在，不能把它们算作新运行结果。程序不自动把提交状态改为完成。数据可由 `mlcourse/foundations_data.py` 的 `example_data` 重建；完整批量脚本只能输出到新的空目录，不能覆盖自己的实验。

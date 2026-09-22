# 第 05 课数据、配置与结果说明

## 数据描述

本课使用 24 条人工构造的数据，只用于练习数据划分、MAE 和数据泄漏。一行数据代表“某个取餐窗口在某一天的一次排队记录”。A、B、C 是三个虚构的取餐窗口，每个窗口有 8 天记录。

`base.json` 是 JSON 文本文件，顶层 `rows` 是记录列表。第一次接触 JSON 时不需要记语法；先按 README 的命令运行，再从生成的 CSV 查看表格。

| 字段 | 含义 | 做预测时是否可用 |
|---|---|---|
| `id` | 记录编号，例如 A05 表示 A 窗口第 5 天 | 只用于查找，不作为模型特征 |
| `queue_length` | 加入队伍时前面的人数 | 可用，是默认预测特征 |
| `wait_minutes` | 实际等待时间，单位为分钟 | 标签／目标值，等待结束后用于评价 |
| `period` | 午间或晚间 | 本课只帮助辨认记录，不进入默认模型 |
| `site` | 取餐窗口 A、B 或 C | 用于分组划分，不进入默认模型 |
| `day` | 第几天 | 用于时间顺序划分 |
| `split` | 原始标记：训练、验证或保留测试 | 程序用它保护第 7–8 天测试记录 |
| `receipt_minutes` | 等待结束后小票上的时间 | 预测时不可用，只用于目标泄漏反例 |

`receipt_minutes` 被人工设定为 `wait_minutes + 0.25`。它几乎直接暴露标签，因此不能作为真实预测特征。数据来自课程程序 `mlcourse/foundations_data.py`，不能用来描述真实食堂或真实人群。

## 三种开发划分

三种方法只重新安排第 1–6 天的开发数据。第 7–8 天始终不进入训练集或验证集。

| 方法 | 训练集 | 验证集 | 主要回答的问题 |
|---|---|---|---|
| `time` 时间顺序划分 | A/B/C 第 1–4 天 | A/B/C 第 5–6 天 | 已有窗口的较晚日期 |
| `group` 分组划分 | 默认 A 第 1–6 天 | 默认 B 第 1–6 天 | 训练中没出现的新窗口 |
| `random` 随机划分 | 从第 1–6 天随机取 12 条 | 其余 6 条 | 近似独立样本的一次随机验证 |

分组划分中，C 的第 1–6 天列在 `unused_ids`，C07–C08 保留为测试记录。`config-group-check.json` 将 A、B 的训练／验证角色交换，但仍不使用 C 选择方案。

## 配置字段

`config.json` 用于最终主运行；`config-start.json` 是起点；`config-support.json` 是日期对照；`config-group-check.json` 是验证窗口对照；`config-mine.json` 由学生保存自己的检查。

| 字段 | 标准含义 | 本课设置 |
|---|---|---|
| `seed` | 随机种子，使 random 划分可以重现 | 默认 `7`；只影响 random |
| `evaluation_split` | 当前评价使用验证集还是测试集 | 本课保持 `validation` |
| `split_strategy` | `summary.json` 的 `metrics` 主要汇总哪种划分 | `time`、`group` 或 `random`；不自动推荐 |
| `train_through_day` | time 训练集包含到第几天 | 默认 `4` |
| `validation_through_day` | 开发数据最晚到第几天 | 固定 `6`，不能包含第 7–8 天测试记录 |
| `group_validation_site` | group 中哪一个开发窗口只进入验证集 | `B` 表示 A 训练、B 验证；`A` 表示 B 训练、A 验证 |

未知字段、错误类型或不允许的窗口会直接报错。换配置时使用新的 `--output` 目录；失败后旧目录可能仍存在，不能把旧结果当作新运行结果。

## 怎样读输出文件

### `comparison.csv`

一行是一种划分方法。先看下面几列：

- `method`：程序代号 `time`、`group` 或 `random`；
- `train_n`：训练记录数；
- `n`：验证记录数，也是 MAE 的分母；
- `shared_sites`：训练集与验证集同时出现的取餐窗口数；
- `mae`：验证集平均绝对误差，单位为分钟；
- `leaked_mae_demo`：目标泄漏反例，不是可选模型。

文件中还保留 `rmse` 和 `asymmetric_loss`，用于其他课兼容。本课不要求用它们作结论。

### `records.csv`

一行是某种方法对某条验证记录的计算。同一个 `id` 在不同 `method` 下出现，不代表新增了独立样本。

- `actual`：实际等待分钟数；
- `prediction`：正常预测值；
- `absolute_error`：`|actual - prediction|`；
- `leaked_prediction_demo`：错误使用小票时间得到的示范预测。

### `summary.json`

`details.splits` 保存每种划分的完整信息：

- `train_ids`、`evaluation_ids`、`test_ids` 和 `unused_ids`；
- `train_sites` 和 `evaluation_sites`；
- 由训练集拟合得到的模型参数。

`metrics` 只汇总 `split_strategy` 指定的方法，不表示程序替你选择了最佳方案。`provenance` 中的文件和源码摘要用于核对重跑时是否使用同一输入，不能证明人工数据来自真实环境。

# S02：先认列，再核对日期和分母

本课固定检查 A、B 两个虚构窗口第 1–4 天的八条排队记录，每个窗口四条。它与第三课同属排队情境，但不是同一份 24 条数据。所有数均人工构造，不是实际调查或 AI 输出。

## 一行数据有哪些字段

| 字段 | 本课含义与单位 |
|---|---|
| `id` | 样本编号，如 A03；一条排队经历对应一行 |
| `queue_length` | 排队开始时前面的人数，非负整数；本课不据此训练模型 |
| `site` | 窗口 A 或 B |
| `period` | 午间或晚间；本例 A 全是午间、B 全是晚间 |
| `day` | 排队发生在第几天，整数；不是等待了几天 |
| `available_day` | 直接观测标签上传的第几天；当日上传也计入；`null` 表示材料未提供 |
| `wait_minutes` | 直接观测到的目标值（等待时间），单位为分钟；本课暂作参照，不保证没有记录错误 |
| `proxy_minutes` | 根据其他信息推算的代理值；只有把它当作标签使用时才称为代理标签；默认八条都有 |
| `review_minutes` | 第二位记录者独立得到的复核值；不是自动裁定的标准答案；没有时为 `null` |

JSON 顶层 `rows` 是这些样本的列表。B04 的 `wait_minutes` 和 `available_day` 都是 `null`。其余记录可能已经发生，但截至某日还没有上传标签。

本离线文件预存后续上传值；这是教学模拟，不是当前时刻都可以使用的数据。程序只在 `available_day <= observation_day` 时输出直接观测标签，并只在此时比较独立复核值。**没有另设复核上传日**，所以本例不能模拟两位记录者各自的标签延迟；实际项目应分别记录每个标签的来源和到达时间。

## 配置：只改正在检查的一项

| 字段 | 含义及限制 |
|---|---|
| `observation_day` | 主统计截止日，按当天结束计算，默认 4；不得早于本批最晚发生日 |
| `later_day` | 额外演示的截止日，默认 7；可以等于主截止日，此时两次统计相同，但不能更早 |
| `disagreement_minutes` | 分歧容差，默认 2；非负数，差异**大于**它才计为分歧，等于不计 |
| `seed` | 为课程接口保留的非负整数，默认 7；本课没有随机步骤，修改它不改变结果 |

`config-start.json` 是固定起点；`config-support.json` 只改主截止日为 7；`config-mine.json` 是学生另存的个人检查；`config.json` 用于最终重跑。配置中的这些设置不是训练得到的模型参数。完整步骤见 [入门指南](../SUPPORT.md)。

从学生根目录运行 `analysis.py`，可用 `--config` 指定配置、`--data` 指定数据、`--output` 指定输出目录。本课不接受 `--split`。副本不可只留下改动的一个字段，其他字段也须保留。

## 运行后再读生成的 records.csv

`data/` 目录只保存原始教学数据 `base.json` 和这份字段说明；运行前这里没有 `records.csv` 或 `comparison.csv`。在仓库根目录运行 `analysis.py` 后，程序才会在你通过 `--output` 指定的结果目录中生成这两张表。例如使用 `--output lesson-04/artifacts/support-start` 后，应打开 `lesson-04/artifacts/support-start/records.csv` 和 `lesson-04/artifacts/support-start/comparison.csv`。不要在 `lesson-04/data/` 中寻找它们，也不要手工创建或修改结果表。

每行仍是一条样本，共八行。`day`、`site` 和 `available_day` 来自人工模拟记录，便于核对截止日；未来上传日也是模拟元数据，不是实际已知的未来事实。程序生成的 `records.csv` 会同时保留 `record_source`、`review_source` 和 `clock_quality`，让你能把统计数字与来源质量对应起来。

`visible=True` 表示截止日已收到直接观测标签，`False` 表示尚未收到。`observed_minutes` 只显示当前可用的目标值；`proxy_minutes` 显示代理值；`review_minutes` 在直接观测标签可见且独立复核值存在时显示。

`proxy_absolute_error` 是代理值与当前直接观测目标值的绝对差；`review_absolute_difference` 是直接观测值与独立复核值的绝对差。单位均为分钟，没有对应值就留空。`disagreement` 只对可比较的两份值显示 True 或 False；空白表示缺少比较所需的值，不是“没有分歧”。

## 再读 comparison.csv

| `method` | 数从哪里来 | `n` 与均值分母 |
|---|---|---|
| `available_only` | 仅已上传的直接观测目标值 | 第 4 天为 4；均值是 20/4，不是全体均值 |
| `zero_fill_demo` | 已上传记录，外加把未知当 0 的错误示范 | 分母 8；这个填零结果不能作为真实统计 |
| `proxy_all` | 全部代理值 | 分母 8；均值描述估计，不描述全体实际等待 |

`n` 是这一行求均值使用的数的个数，不等于原始记录总数，也不都代表直接观测标签数。本课比较的是处理方式，不是三个训练模型的性能。

主行 `available_only` 还报告：`coverage = n / total_rows`；`unknown_labels` 是未收到直接观测标签的数量；`proxy_mae_observed` 对当前可见记录求代理值与直接观测目标值的平均绝对误差；`review_pairs` 是同时有两种记录的记录数；`disagreements` 是其中超过容差的数量；`agreement = (review_pairs - disagreements) / review_pairs`。这里的一致比例是按分钟容差定义的标注者间一致性比例，不是模型准确率。

没有任何可见标签时，均值与代理 MAE 为 `null`；没有配对时，一致比例为 `null`。其他处理行的覆盖率等列留空，表示未在该行报告，不能读成零或 100%。真实标签为 0 时必须计入统计。

## summary.json 和失败处理

`metrics` 对应主截止日的 `available_only`，`comparison` 对应其余处理方式；`details.tables` 保存两张表；`stress_test.metrics` 保存 `later_day` 的统计。它不是训练或测试划分，也不是自动推荐。

`provenance` 保存数据、配置与源码哈希以便复核，不能证明数据真实。每次检查用新的输出目录；失败后旧文件可能仍在，不能作为本次结果。字段缺失、类型错误、标签与日期不成对、上传早于发生日或容差为负都会报错。修正后再运行，不手改结果表。

默认数据和计算公式未改。数据生成在 `mlcourse/foundations_data.py`；批量重建脚本只能输出到新的空目录，不覆盖个人实验。

## 记录来源和计时质量

为帮助安排复核，每条记录还保存：

| 字段 | 含义 |
|---|---|
| `record_source` | 第一份记录来自直接计时、日志重建或尚未提供 |
| `review_source` | 第二位记录者得到独立复核值的来源；B04 没有独立复核值 |
| `clock_quality` | 开始和结束时间是否完整，或缺少哪一部分 |

这些字段不能自动证明哪一个目标值正确。它们用于选择复核优先级；统计公式仍按 `wait_minutes`、`available_day` 和 `review_minutes` 计算。

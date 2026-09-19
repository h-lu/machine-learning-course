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
| `available_day` | 第一份实际等待标签上传的第几天；当日上传也计入；`null` 表示材料未提供 |
| `wait_minutes` | 第一份实际等待记录，非负分钟数；本课暂作核对参照，不保证无记录错误 |
| `proxy_minutes` | 事先准备的估计值，模拟代理标签；默认八条都有 |
| `review_minutes` | 第二份标注，不是自动裁定的标准答案；没有时为 `null` |

JSON 顶层 `rows` 是这些样本的列表。B04 的 `wait_minutes` 和 `available_day` 都是 `null`。其余记录可能已经发生，但截至某日还没有上传标签。

本离线文件预存后续上传值；这是教学模拟，不是当前时刻都可以使用的数据。程序只在 `available_day <= observation_day` 时输出第一份标签，并只在此时比较第二份标注。**没有另设复核上传日**，所以本例不能模拟两位标注者各自的延迟；实际项目应单独记录。

## 配置：只改正在检查的一项

| 字段 | 含义及限制 |
|---|---|
| `observation_day` | 主统计截止日，按当天结束计算，默认 4；不得早于本批最晚发生日 |
| `later_day` | 额外演示的截止日，默认 7；可以等于主截止日，此时两次统计相同，但不能更早 |
| `disagreement_minutes` | 分歧容差，默认 2；非负数，差异**大于**它才计为分歧，等于不计 |
| `seed` | 为课程接口保留的非负整数，默认 7；本课没有随机步骤，修改它不改变结果 |

`config-start.json` 是固定起点；`config-support.json` 只改主截止日为 7；`config-mine.json` 是学生另存的个人检查；`config.json` 用于最终重跑。配置中的这些设置不是训练得到的模型参数。完整步骤见 [入门指南](../SUPPORT.md)。

从学生根目录运行 `analysis.py`，可用 `--config` 指定配置、`--data` 指定数据、`--output` 指定输出目录。本课不接受 `--split`。副本不可只留下改动的一个字段，其他字段也须保留。

## 先读 records.csv

每行仍是一条样本，共八行。`day`、`site` 和 `available_day` 来自人工模拟记录，便于核对截止日；未来上传日也是模拟元数据，不是实际已知的未来事实。

`visible=True` 表示截止日已收到第一份标签，`False` 表示尚未收到。`observed_minutes` 只显示当前可用的值；`proxy_minutes` 显示估计值；`review_minutes` 在第一份标签可见且第二份存在时显示。

`proxy_absolute_error` 是代理值与当前参照值的绝对差；`review_absolute_difference` 是两份当前标注的绝对差。单位均为分钟，没有对应值就留空。`disagreement` 只对可比较的两份标注显示 True 或 False；空白不是“没有分歧”。

## 再读 comparison.csv

| `method` | 数从哪里来 | `n` 与均值分母 |
|---|---|---|
| `available_only` | 仅已上传的实际记录 | 第 4 天为 4；均值是 20/4，不是全体均值 |
| `zero_fill_demo` | 已上传记录，外加把未知当 0 的错误示范 | 分母 8；这个填零结果不能作为真实统计 |
| `proxy_all` | 全部代理估计 | 分母 8；均值描述估计，不描述全体实际等待 |

`n` 是这一行求均值使用的数的个数，不等于原始记录总数，也不都代表真实标签数。本课比较的是处理方式，不是三个训练模型的性能。

主行 `available_only` 还报告：`coverage = n / total_rows`；`unknown_labels` 是未收到数量；`proxy_mae_observed` 对当前可见记录求代理误差平均；`review_pairs` 是同时有两份标注的记录数；`disagreements` 是其中超过容差的数量；`agreement = (review_pairs - disagreements) / review_pairs`。一致比例是本课按分钟容差定义的比例，不是准确率。

没有任何可见标签时，均值与代理 MAE 为 `null`；没有配对时，一致比例为 `null`。其他处理行的覆盖率等列留空，表示未在该行报告，不能读成零或 100%。真实标签为 0 时必须计入统计。

## summary.json 和失败处理

`metrics` 对应主截止日的 `available_only`，`comparison` 对应其余处理方式；`details.tables` 保存两张表；`stress_test.metrics` 保存 `later_day` 的统计。它不是训练或测试划分，也不是自动推荐。

`provenance` 保存数据、配置与源码哈希以便复核，不能证明数据真实。每次检查用新的输出目录；失败后旧文件可能仍在，不能作为本次结果。字段缺失、类型错误、标签与日期不成对、上传早于发生日或容差为负都会报错。修正后再运行，不手改结果表。

默认数据和计算公式未改。数据生成在 `mlcourse/foundations_data.py`；批量重建脚本只能输出到新的空目录，不覆盖个人实验。

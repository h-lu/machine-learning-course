# S07 入门支持：先核对一条误差，再比较模型假设

这是本课必做任务的一条完整路径，不是额外作业。第一项小任务是在 `records.csv` 找到 R21，并重算它的绝对误差。

需要概念解释时打开 [LEARN.md](LEARN.md) 中本步骤点名的小例子，不要求开始前读完整份材料。

## 1. 运行现成配置

在学生仓库根目录运行：

```bash
python scripts/course.py start 09
python lesson-09/analysis.py --config lesson-09/config-start.json --output lesson-09/artifacts/start
```

看到“S07 完成”和“结果写入”表示运行成功。先打开 `lesson-09/artifacts/start/records.csv`，不要先翻所有 JSON。

## 2. 核对 R21

找到 `id=R21`、`method=simple_linear` 的一行。给定数据下，真实值是 4.0 分钟，预测约 1.199706 分钟，因此绝对误差为：

```text
|4.0 - 1.199706| = 2.800294 分钟
```

这是核对示例，不是评分要求。若不同，先检查方法名、输出目录和是否修改过数据。再任选另一行自己重算。

## 3. 比较同一验证集

打开 `comparison.csv`。起点中简单直线的训练/验证 MAE 约为 1.027/1.351 分钟，二次候选约为 0.290/0.307 分钟。两者都由相同训练集拟合，并在相同 8 条验证记录上评价，因此可以比较。不要只看训练误差，也不要把这些人工数据结果推广到真实业务。

## 4. 检查范围外输入

打开 `outside_check.csv`。训练输入范围是 0–10 个细节项，起点检查 12。该行 `observed_label` 为空，表示没有真实处理时间。先运行已准备的范围外输入 15，只改变这一项：

```bash
python lesson-09/analysis.py --config lesson-09/config-support.json --output lesson-09/artifacts/support
```

再把 `config-start.json` 另存为 `config-mine.json`，只将 `outside_detail_count` 改为你选择的大于 10 的整数：

```bash
python -m json.tool lesson-09/config-mine.json
python lesson-09/analysis.py --config lesson-09/config-mine.json --output lesson-09/artifacts/mine
```

写下两个模型的预测差距，以及需要补采哪类真实记录才能判断；这就是你自己的范围外检查。

## 5. 写报告并形成最终结果

先根据验证证据选择模型，记录理由后再查看测试列。把个人设置写回 `config.json`，并将 `evaluation_split` 改为 `test`，记录选择后运行：

```bash
python scripts/course.py run 09
```

报告至少写用途、R21 手算、同条件比较、范围外限制和测试前选择。填完任务说明，将状态改为 `complete` 后运行 `python scripts/course.py check 09`。若运行失败，保留报错；可以先完成上面的手算，但必须注明尚未运行并在修复后补跑。

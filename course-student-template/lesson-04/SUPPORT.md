# 第 04 课入门支持：先分清三个数，再计算覆盖率

这是第 04 课必做任务的一条完整路径。你会先读 B02 一行，再运行第 4 天起点，比较第 7 天，最后只改一个设置做自己的检查。

## 1. 第一项任务：B02 的三个数分别是什么

B02 是一次已经发生的排队经历：

| 字段 | 数值 | 来源与含义 |
|---|---:|---|
| `wait_minutes` | 9 分钟 | 第一份实际等待记录，本课暂作核对参照 |
| `proxy_minutes` | 5 分钟 | 按人数等信息得到的代理估计，不是实际计时 |
| `review_minutes` | 9 分钟 | 第二份标注，用来检查是否与第一份分歧 |

先回答：如果要统计已经收到的实际等待，应使用哪一列？代理估计 5 能不能直接说成实际等了 5 分钟？两份标注相同能否证明它们一定正确？

## 2. 运行第 4 天起点

在学生仓库根目录运行。电脑没有 `python` 命令时统一使用 `python3`。

```bash
python scripts/course.py start 04
python lesson-04/analysis.py --config lesson-04/config-start.json --output lesson-04/artifacts/support-start
```

看到“结果写入”后，先打开 `support-start/records.csv`。CSV 第一行是列名。先只看 `id`、`visible` 和 `observed_minutes`：`True` 表示截至第 4 天已经收到实际标签，空白表示未知，不是 0。

## 3. 手算均值和覆盖率

`visible=True` 的记录是 A01、A02、A04、B02，实际值为 1、3、7、9 分钟。

```text
均值 = (1 + 3 + 7 + 9) ÷ 4 = 5 分钟
覆盖率 = 4 ÷ 8 = 50%
```

均值分母为 4，覆盖率分母为 8。打开 `support-start/comparison.csv`，在 `method=available_only` 行核对 `n=4`、`mean_minutes=5`、`coverage=0.5`。

`zero_fill_demo` 是把未知错误填成 0 的示范；`proxy_all` 平均的是代理估计。它们都不是 8 条实际等待的真实平均值。

## 4. 核对一条标注分歧

找 A04：`observed_minutes=7`，`review_minutes=10`，绝对差为 3 分钟。默认容差是 2，规则写的是“差异超过 2 才算分歧”，所以 A04 标为 `True`。

一致比例的分母是同时有两份标注的记录数。没有第二份标注的记录不算一致，也不算分歧。

## 5. 检查来源质量

回到 `data/base.json` 看四条已知记录的 `record_source` 和 `clock_quality`。统计数字相同不代表来源质量相同；把一条需要复核的记录写入报告，并说明你要先查哪份原始记录。运行结果的 `records.csv` 也会保留这三列，方便把来源和统计数字对应起来。

## 6. 只把观察日改为第 7 天

先预计会新增哪些标签，再运行现成配置：

```bash
python lesson-04/analysis.py --config lesson-04/config-support.json --output lesson-04/artifacts/support-compare
```

比较 `support-start` 和 `support-compare`。第 7 天新增 A03、B01、B03，已知 7/8 条，覆盖率 87.5%；B04 仍未知。新均值约为 6.143 分钟。

这是同一批 8 条经历在较晚截止日收到更多标签，不是第 7 天重新发生了 8 次排队，也不能说服务因此变慢。

## 7. 做自己的单一检查

从 `config-start.json` 另存为 `config-mine.json`。只改 `disagreement_minutes` 或 `observation_day` 中的一项，先写预计，再运行：

```bash
python -m json.tool lesson-04/config-mine.json
python lesson-04/analysis.py --config lesson-04/config-mine.json --output lesson-04/artifacts/my-check
```

成功后记录一条原始数值和一个带分母的比例。若把容差改为 3，A04 的差异恰好为 3，不再满足“超过 3”，但原始的 7 和 10 没有改变。

写一条具体复核计划，例如检查 A04 的加入队伍和取餐时间。计划尚未执行时必须写成“准备复核”，不能写成已经证实。

## 8. 写报告并检查保存

报告至少包含：三个数的来源、均值与覆盖率手算、日期对照、自己的检查、复核计划和限制。填写 `contract.json`；其中 `split_plan` 写“第 4 天起点、第 7 天对照和最后保留的截止日”，不是机器学习中的训练/验证/测试划分。把最后保留的设置写回 `config.json`，实际完成后把 `submission.json` 状态改为 `complete`。

```bash
python scripts/course.py run 04
python scripts/course.py check 04
git add lesson-04
git add -f lesson-04/artifacts
git diff --cached --name-only
```

暂存清单应包含报告、任务说明、配置和报告引用的结果。以上命令只准备本地提交，不会自动上传。

## 9. 卡住时怎么办

- 不知道先看什么：先看 `records.csv` 中 B02，再找四行 `visible=True`。
- 均值或覆盖率不对：分别检查分母是 4 还是 8。
- 日期改变后结果没变：检查实际使用的配置和输出目录。
- JSON 报错：按行号、列号检查英文双引号、逗号和非负数值。
- 软件暂时不能运行：保留报错，先完成第 1、3、4 节手算，并在报告标明“尚未运行”，修复后补跑。

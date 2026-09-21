# S09 入门支持：跟踪同一条记录的近邻变化

这是必做任务的可执行路径。第一项小任务是找到 C28，并比较原始表示和缩放表示各自选出的 3 条近邻。

需要概念解释时打开 [LEARN.md](LEARN.md) 中本步骤点名的小例子，不要求开始前读完整份材料。

## 1. 运行起点

```bash
python scripts/course.py start 11
python lesson-11/analysis.py --config lesson-11/config-start.json --output lesson-11/artifacts/start
```

成功后先打开 `lesson-11/artifacts/start/records.csv`，搜索 C28。`nearest_ids` 用竖线分隔 3 条训练记录；`nearest_distances` 是对应距离。

## 2. 理解为什么尺度会改变距离

假设两条记录消息长度相差 20、历史次数相差 2。直接计算欧氏距离时，仅这两项就给出 `sqrt(20²+2²)≈20.10`，长度几乎决定结果。缩放后，每个连续字段先减训练均值，再除训练标准差，使不同量纲更可比。

打开 `summary.json`，任选一个字段和一条记录，按 `(值-训练均值)/训练标准差` 重算。均值与标准差只能来自 24 条训练记录。

## 3. 查看挑战记录

打开 `challenge.csv`。P01 长度缺失，程序用训练中位数填补；`prepared` 还会增加缺失指示。P02 渠道 `social` 未在训练出现，`prepared` 会使用“其他渠道”位置。P03 是少见但可能正常的记录。起点只比较 `raw` 和 `scaled`，所以渠道仍未进入候选表示；这正是下一步检查的理由。

## 4. 运行完整候选表示

`config-support.json` 已设置 `candidate_representation=prepared`。运行：

```bash
python lesson-11/analysis.py --config lesson-11/config-support.json --output lesson-11/artifacts/support
```

比较 `raw` 与 `prepared` 的验证准确率和三条挑战记录。结果相同也不表示表示方式相同；要看近邻和处理规则。

再另存 `config-mine.json`，只改表示或近邻数之一，写预计后运行。选择最终设置并在看测试前记录。

## 5. 完成最后评价和提交

将最终设置写回 `config.json`，把 `evaluation_split` 改为 `test`，运行 `python scripts/course.py run 11`。报告保留一个缩放手算、C28 近邻变化、至少两条挑战记录和结论边界。填写任务说明并标记完成后，运行 `python scripts/course.py check 11`。

# S11 入门支持：分清源数据、目标训练数据和评价数据

这是必做任务的一条路径。第一项小任务是确认三批数据各做什么：60 条无标签源记录学习表示，24 条目标训练记录学习输出层，12 条验证记录比较方案。

需要概念解释时打开 [LEARN.md](LEARN.md) 中本步骤点名的小例子，不要求开始前读完整份材料。

## 1. 运行起点

```bash
python scripts/course.py start 13
python lesson-13/analysis.py --config lesson-13/config-start.json --output lesson-13/artifacts/start
```

成功后先打开 `summary.json`，核对 `source_unlabeled_count` 和 `target_train_count`；再看 `comparison.csv`。不要把无标签源记录计入下游标签训练样本。

## 2. 读懂一维借来表示

打开 `source_components.csv`。起点只保留第 1 个分量。它由四个源字段的缩放值按权重相加得到。权重来自源数据的共同变化，并没有使用 `needs_review` 标签。

选择一个字段，写出“缩放值 × 权重”这一项；不用手算完整 PCA。源方差较大只说明源数据沿该方向变化多，不等于当前标签预测更好。

## 3. 公平比较并做场景检查

起点中原始缩放表示验证准确率约 0.917，一维借来表示约 0.750。这是本次小数据结果，不是借来表示永远更差。打开 `stress_check.csv`，查看消息长度信息不可用时两条路线怎样变化。该检查保持模型参数不变。

## 4. 增加一个表示维度

运行两维配置：

```bash
python lesson-13/analysis.py --config lesson-13/config-support.json --output lesson-13/artifacts/two-dim
```

两维借来表示在默认验证集约为 0.833，仍不必优于原始表示。另存 `config-mine.json`，只改维度或压力字段之一，先预计再运行。报告明确写“源数据 PCA 后冻结，只训练输出层”，不要写成大型模型微调。

## 5. 最后评价和提交

验证集上选定表示后写回 `config.json`，再改 `evaluation_split=test` 并运行 `python scripts/course.py run 13`。报告包含数据用途、一个分量贡献、同划分比较、信息缺失检查和选择。填完状态后运行 `python scripts/course.py check 13`。

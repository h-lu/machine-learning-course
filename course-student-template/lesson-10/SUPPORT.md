# S08 入门支持：先数概率分组，再选择提醒办法

这是完成必做任务的详细路径。第一项小任务是数 `[0.4, 0.7)` 概率组中有几条记录、几条真实需要复核。

需要概念解释时打开 [LEARN.md](LEARN.md) 中本步骤点名的小例子，不要求开始前读完整份材料。

## 1. 运行并打开第一张表

```bash
python scripts/course.py start 10
python lesson-10/analysis.py --config lesson-10/config-start.json --output lesson-10/artifacts/start
```

命令从仓库根目录运行。成功后先打开 `lesson-10/artifacts/start/calibration.csv`。

## 2. 手算一个概率分组

在 `records.csv` 中，验证集概率落在 `[0.4, 0.7)` 的记录有 C28、C29、C31，共 3 条；其中标签为 1 的有 1 条，所以实际发生比例是 `1/3≈0.333`。三条平均概率约 0.602。平均概率和实际比例并不相等，且只有 3 条，证据很不稳定。

这是给定起点的核对数字。若不一致，检查是否使用验证集和起点配置。

## 3. 看提醒办法改变了谁

打开 `comparison.csv`。阈值 0.5 选 5 条，阈值 0.4 选 6 条；在这批数据中召回率没有提高，精确率从 0.8 降到约 0.667。到 `records.csv` 找新增的 C28，核对概率和真实标签。由此说明降低阈值通常会增加提醒，但不保证在每批数据中找回更多正类。

## 4. 做个人单因素检查

先运行已经准备的较高阈值 0.6，其他条件保持不变：

```bash
python lesson-10/analysis.py --config lesson-10/config-support.json --output lesson-10/artifacts/support
```

再把 `config-start.json` 另存为 `config-mine.json`。只改 `candidate_threshold` 或只改 `review_capacity`，先写预计，再运行：

```bash
python -m json.tool lesson-10/config-mine.json
python lesson-10/analysis.py --config lesson-10/config-mine.json --output lesson-10/artifacts/mine
```

根据误报、漏报和人工容量选择规则。不要把概率 0.8 解释成这条记录“80% 确定”为正类；校准要在一组记录上核对。

## 5. 保存选择再看测试

把选定设置写回 `config.json`，先记录选择，再把 `evaluation_split` 改为 `test`：

```bash
python scripts/course.py run 10
```

完成报告、任务说明和状态后运行 `python scripts/course.py check 10`。报告引用概率分组的分母、改变行动的一条记录和容量理由。环境失败时先保留命令、报错和手算，修复后补跑。

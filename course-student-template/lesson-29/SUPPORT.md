# 第 29 课入门支持：先分清 6 条、4 条和 2 条

本课分析固定预测日志。第一项任务是找到标签状态，不需要训练模型。

### 五分钟内开始

```bash
python scripts/course.py start 29
python lesson-29/analysis.py --config lesson-29/config-start.json --output lesson-29/artifacts/start
```

成功后打开 `records.csv`，筛选 `batch=current`。共有 6 行；M09、M11 的 `label_available` 为 `False`，所以已有标签 4 条、暂无标签 2 条。

### 手算已有标签质量

运行候选版本：

```bash
python lesson-29/analysis.py --config lesson-29/config-support.json --output lesson-29/artifacts/support
```

在支持结果的 `records.csv` 中，只数 `label_available=True` 的 4 行。`v2` 其中 2 行正确，所以是 `2/4=0.50`。不要把暂无标签两行当错，也不要猜它们正确。

### 比较报警和恢复

打开 `summary.json`：

- `alarms.before_labels` 使用新条件、低置信和路线分布，可以先于标签；
- `alarms.after_available_labels` 使用当前已经到达的 4 个标签；
- `recovery_check` 只说明 `v1` 在已有标签记录上的结果。

### 只改一个报警阈值

```bash
cp lesson-29/config-support.json lesson-29/config.json
```

只改 `new_condition_rate_limit` 或 `known_accuracy_minimum`，先预计会增加误报还是漏报，再运行 `python scripts/course.py run 29`。报告恢复步骤和仍未知的两条请求。完成后更新提交状态并运行 `python scripts/course.py check 29`。

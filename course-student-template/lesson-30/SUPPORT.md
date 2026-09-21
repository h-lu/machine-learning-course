# 第 30 课入门支持：正确数、计时和估算成本分开看

本课第一次运行不需要改程序。计时会随机器负载波动，这是正常现象。

### 五分钟内开始

```bash
python scripts/course.py start 30
python lesson-30/analysis.py --config lesson-30/config-start.json --output lesson-30/artifacts/start
```

成功后出现 `summary.json`、`records.csv` 和 `timings.csv`。先打开 `summary.json`，找到无缓存的 `fast` 与 `thorough`：分别答对 8/10 和 10/10。

### 核对一条缓存

打开 `records.csv`，找到 P05。它的文字与 P01 完全相同，因此规范化后也相同；在 `cache_enabled=True` 的行中，P05 应为缓存命中。开启缓存没有改变预测路线，只减少新计算。

估算 `fast` 开缓存的成本：8 次新计算乘每次 1 个估算单位，得到 8。这个值不是实际账单。

### 增加重复计时

先预计哪些量会变化：每次毫秒值与观察到的波动会变，正确数/10 不应变。运行：

```bash
python lesson-30/analysis.py --config lesson-30/config-support.json --output lesson-30/artifacts/support
```

对同一方案读五个 `mean_request_latency_ms`，写最小值和最大值，单位是毫秒/条。`total_elapsed_ms` 是这批 10 条的总时间；不要把缓存查询时间叫做推理时间。

### 实际改一条重复输入，再按预算选择

复制现成检查配置到最终配置，再按 README 第 5 步编辑 `repeat_input_check`，只选 P05 或 P08，写一条不再与前面相同、但参考路线仍一致的新文字。先预计命中次数，运行后打开 `changed_records.csv` 核对。最后写一个明确预算或允许等待上限，在四种方案中作选择。

```bash
cp lesson-30/config-check.json lesson-30/config.json
# 编辑 config.json 中已有的 repeat_input_check，然后运行：
python scripts/course.py run 30
```

把本次 `timings.csv` 连同确定性结果提交。计时文件不会通过逐字节重跑核对，因为实际时间本来会波动；所以 `course.py check` 通过后，仍要单独确认这个文件已经提交。

`artifacts/` 默认被 Git 忽略；提交时另执行 `git add -f lesson-30/artifacts/timings.csv`，让教师能看到报告引用的这一次实测。

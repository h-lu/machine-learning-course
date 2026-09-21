# 第 32 课入门支持：先用开发证据固定方案，再进行最后评价

这是一条完成必做任务的完整路径。开始时不要打开 `data/final.json`；默认命令也不会读取它。

### 五分钟内开始开发评价

从仓库根目录运行：

```bash
cp lesson-32/config-start.json lesson-32/config.json
python scripts/course.py start 32
python scripts/course.py run 32
```

终端打印的命令不应出现 `--final-data`。成功标志是 `lesson-32/artifacts` 中出现 `summary.json`、`records.csv` 和 `manifest.json`。先打开 `summary.json`，看到 `"evaluation_stage": "development"`；再打开 `records.csv`，第一列应是以 `T` 开头的开发请求编号。

如果这一步因为 `data/final.json` 缺失或内容损坏而失败，说明运行路径有问题：保留报错并向教师报告。开发阶段只需要 `data/base.json`。

### 用开发证据固定计划

1. 在 `records.csv` 中分别统计 `original_correct` 和 `adapted_correct` 为真的行数，分母都是全部开发请求数。
2. 选择一条两个方案路线不同的请求，解释输入词语怎样改变路线。
3. 在 `config.json` 中把 `release_candidate` 设为 `campus_original` 或 `library_adapted`。两种选择都必须用开发证据说明。
4. 在 `report.md` 第一部分写候选、选择理由、最后指标、必须送人工的严重条件和停止自动使用的条件。
5. 填写 `contract.json`，尤其写清“候选固定后只使用最后评价一次”。

再运行 `python scripts/course.py run 32`，确认 `summary.json` 仍是 `development`，且 `selected_candidate_evaluation.scheme` 对应你的候选。

### 显式切换到最后评价

固定选择后运行：

```bash
cp lesson-32/config.json lesson-32/config-final.json
cp lesson-32/submission-final.json lesson-32/submission.json
python scripts/course.py run 32
```

终端打印的命令必须包含下面两组参数：

```text
--final-data lesson-32/data/final.json
--config lesson-32/config-final.json
```

现在才打开结果。`summary.json` 的 `evaluation_stage` 应是 `final_evaluation`；`records.csv` 的编号以 `D` 开头。对两个方案使用相同分母手算正确数，核对严重条件，并追踪一条路线发生变化的请求。

### 检查能否重跑

打开 `manifest.json`，按 `run_command` 的顺序复制所有参数，只把 `<OUTPUT_DIR>` 替换为新目录：

```bash
python lesson-32/analysis.py --data lesson-32/data/base.json --final-data lesson-32/data/final.json --config lesson-32/config-final.json --output lesson-32/artifacts/replay
```

比较两个目录的 `summary.json`、`records.csv` 和 `manifest.json`。三个文件都应逐字节一致。manifest 中必须有 `final_data_sha256`；如果没有，说明你保存的是开发运行，而不是最后评价。

### 完成交付

写完报告后，把 `submission.json` 的状态改为 `complete`，再运行：

```bash
python scripts/course.py check 32
python scripts/course.py ci
```

看过最后评价后，不要再针对这些请求修改关键词并称为新测试。需要修改时，把这批结果降为开发证据，并另备一批未见数据。

# 第 31 课入门支持：在同一批图书馆请求上重跑

本课先重新写任务，再运行。不要直接引用设备场景旧分数。

### 五分钟内开始

在 `report.md` 写四句话：谁使用；输入是什么；输出是什么；哪些请求必须转人工。再把同样信息分别写入 `contract.json` 的 `user`、`question`、`data_source`、`metric`、`split_plan` 和 `initial_expectation`；每个字段的对应内容见 README 第 1 步。然后运行：

```bash
python scripts/course.py start 31
python lesson-31/analysis.py --config lesson-31/config-start.json --output lesson-31/artifacts/start
```

成功后打开 `records.csv` 的 T01、T02。查看 `original_route`、`adapted_route` 和 `expected_route`，说明“读者证”“馆藏可借册数”为什么是新条件。

### 手算共同分母

两种方案都使用 8 条请求：原方案 `6/8=0.75`，适配方案 `8/8=1.00`。不能把设备场景旧数据放进这个分母。

### 新增一条可能推翻建议的请求

打开 `config.json` 中现成的 `added_request`，把示例的编号、条件、文字和参考路线改成你自己的请求。先写参考路线的用途理由和预计，再运行：

```bash
python scripts/course.py run 31
```

保留失败，不要事后修改参考路线迎合程序。

### 整理最终证据

打开最终 `summary.json`：`provided_comparison` 只用课程给出的 8 条，`comparison` 包含新增请求。报告新场景定义、共同分母、改变请求、自设计检查和未覆盖条件。完成后更新提交状态并运行 `python scripts/course.py check 31`。

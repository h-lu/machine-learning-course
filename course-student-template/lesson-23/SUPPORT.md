# 第 23 课入门支持：跟踪失败、重试和停止

1. 在学生仓库根目录运行：

   ```bash
   python scripts/course.py start 23
   python lesson-23/analysis.py --config lesson-23/config-start.json --output lesson-23/artifacts/stop-on-completion
   ```

2. 打开 `action_trace.csv`，先筛选 `id=W09`、`scheme=model`。依次找到 `model_route`、首次 `tool_call` 的 `tool_failure`、一次 `is_retry=True` 的工具调用。成功后没有第三次工具调用。
3. 再筛选 `scheme=fixed`。它先执行三次路线条件检查，再经历相同失败和重试。这里每个条件检查、模型决定、检索、工具调用或交人都按 1 个动作计数。
4. 打开 `summary.json`：起点固定流程 22 个动作，模型路线 13 个；各有 1 次失败和 1 次重试。自动请求与转人工请求分开计数。
5. 运行关闭完成停止的对照：

   ```bash
   python lesson-23/analysis.py --config lesson-23/config-support.json --output lesson-23/artifacts/repeat-after-completion
   ```

   找 `is_repeat_after_completion=True` 的 8 行：固定和模型流程各 4 行。它们是无意义重复，不是失败重试。
6. 复制起点配置，只把 `max_tool_retries` 改为 0。先预计 W09 的停止原因，再运行；工具首次失败后应转人工，而不是记作已经答错或答对。
7. 报告说明你采用的停止条件、动作上限、重试上限，以及人工容量不足时怎样调整。把最终单因素配置复制到 `config.json`；采用起点时执行 `cp lesson-23/config-start.json lesson-23/config.json`。然后生成根目录提交结果：

   ```bash
   python scripts/course.py run 23
   ```

   确认 `summary.json`、`route_decisions.csv` 和 `action_trace.csv` 都在 `lesson-23/artifacts/`。在 `submission.json` 把 `status` 从 `in_progress` 改成 `complete`，再运行：

   ```bash
   python scripts/course.py check 23
   ```

   检查只确认文件与路径，不替你判断停止规则是否合理。

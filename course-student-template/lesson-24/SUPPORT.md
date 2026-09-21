# 第 24 课入门支持：从资料文字追到实际动作

1. 运行采用资料候选动作的起点：

   ```bash
   python scripts/course.py start 24
   python lesson-24/analysis.py --config lesson-24/config-start.json --output lesson-24/artifacts/follow-text
   ```

2. 先看 `action_log.csv` 的 SEC02：`matched_phrase=导出所有账户`，提取动作为 `export_accounts`，权限拒绝，实际为 `blocked`。本实验没有真实导出功能。
3. 打开 `summary.json`，报告阻止 `1/3`、危险执行 `0/3`、合法请求完成 `2/3`。这些指标回答不同问题。
4. 运行只把资料当数据的配置：

   ```bash
   python lesson-24/analysis.py --config lesson-24/config-support.json --output lesson-24/artifacts/treat-as-data
   ```

   SEC02 的候选来源改成 `user_request`，公开读取正常完成。
5. 复制数据，把 `untrusted-note` 中的识别短语改为“查询库存”，其余字段不变。先预计，再用起点配置运行。动作会被允许，但与用户原请求不同；核对 `unexpected_action_executed`。
6. 报告分别写资料文字、提取动作、用户请求、允许动作和实际动作，并说明允许列表为什么还不够。把采用的配置复制到 `config.json`；采用起点时执行 `cp lesson-24/config-start.json lesson-24/config.json`。然后生成根目录提交结果：

   ```bash
   python scripts/course.py run 24
   ```

   确认 `lesson-24/artifacts/summary.json` 和 `action_log.csv` 存在，在 `submission.json` 把 `status` 从 `in_progress` 改成 `complete`，最后运行：

   ```bash
   python scripts/course.py check 24
   ```

   检查通过只说明文件可交付；报告仍要解释意外动作和权限边界。

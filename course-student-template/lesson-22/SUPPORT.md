# 第 22 课入门支持：核对一次真实工具返回

1. 在学生仓库根目录运行：

   ```bash
   python scripts/course.py start 22
   python lesson-22/analysis.py --config lesson-22/config-start.json --output lesson-22/artifacts/invalid-minus-2
   ```

2. 先看 `tool_calls.csv` 的 W03。写出 `overdue_fee(days=2)`，手算 `2 天×2 元/天=4 元`，再核对状态、值和单位。
3. 找 W02：一步基线固定答 1 件，库存工具实际返回 2 件。说明两个数各来自哪里。
4. 打开 `summary.json`，写一步基线 `1/5`、工具 `5/5`。这 5 条都是自动请求；本处没有把人工交接混入分母。
5. 查看 `invalid_call`：-2 天应失败且没有 `value`。再运行 31 天对照：

   ```bash
   python lesson-22/analysis.py --config lesson-22/config-support.json --output lesson-22/artifacts/invalid-31
   ```

6. 复制数据并增加一条有来源的工具请求。先预计它会让哪一方案的正确数改变，再运行到新目录。若新设备库存恰好为 1 件，一步基线也可能正确，但仍没有当前查询记录。
7. 报告写清何时调用、何时停止、何时转人工，以及分数相同是否表示证据同样充分。把采用的配置复制到 `config.json`；采用起点时执行 `cp lesson-22/config-start.json lesson-22/config.json`。然后运行并检查最终提交文件：

   ```bash
   python scripts/course.py run 22
   ```

   确认 `lesson-22/artifacts/summary.json` 和 `tool_calls.csv` 存在，在 `submission.json` 把 `status` 从 `in_progress` 改成 `complete`，再运行：

   ```bash
   python scripts/course.py check 22
   ```

   检查失败时保留报错，按提示补文件或修路径后重跑。

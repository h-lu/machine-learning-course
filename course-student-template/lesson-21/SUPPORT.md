# 第 21 课入门支持：从一条请求追踪完整流程

这是完成必做任务的一条路径。命令都在能看到 `scripts/` 和 `lesson-21/` 的学生仓库根目录运行。

1. 运行初始开发批次：

   ```bash
   python scripts/course.py start 21
   python lesson-21/analysis.py --config lesson-21/config-start.json --output lesson-21/artifacts/initial
   ```

2. 先看 `traces.csv` 的 W01。一步基线按固定规则回答 7；分步流程记录 `retrieve → loan-student-current → 7`。两者最终数字相同，证据来源却不同。
3. 再看 W02。一步基线固定回答 1 件，分步流程用 `inventory_lookup` 查询相机并返回 2 件。沿列说明哪一个值来自规则、哪一个来自当前库存。
4. 打开 `summary.json`。初始批次有 4 条自动请求和 2 条交人请求。分别写“自动正确数/4”和“转人工数/6”，不要把两个分母混在一起。
5. 运行 W07–W12 的后一批开发请求：

   ```bash
   python lesson-21/analysis.py --config lesson-21/config-support.json --output lesson-21/artifacts/later
   ```

   这批请求以后还会使用，因此只是换一批开发证据。
6. 复制数据为 `data/mine.json`，新增一条请求，按 `data/DATA.md` 填写必需字段。先预计一步规则和分步流程分别会怎样处理，再实际运行并保存变化。
7. 报告说明何时一步规则已经够用、何时中间产物值得额外步骤，以及哪些请求必须转给人。把最终采用的批次写入 `config.json`；若采用起点，可执行 `cp lesson-21/config-start.json lesson-21/config.json`。然后生成提交清单所列的根目录结果：

   ```bash
   python scripts/course.py run 21
   ```

   成功后应有 `lesson-21/artifacts/summary.json` 和 `traces.csv`。在 `submission.json` 把 `status` 从 `in_progress` 改成 `complete`，最后运行：

   ```bash
   python scripts/course.py check 21
   ```

   只有报告和两个结果文件都存在时检查才会通过；通过不等于结论自动正确。

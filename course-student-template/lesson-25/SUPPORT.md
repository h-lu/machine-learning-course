# 第 25 课入门支持：沿局部值定位一个故障

1. 运行检索故障：

   ```bash
   python scripts/course.py start 25
   python lesson-25/analysis.py --config lesson-25/config-start.json --output lesson-25/artifacts/retrieval-fault
   ```

2. 在 `fault_comparison.csv` 找 W01，按顺序读三组字段：
   - 原流程：`original_document=loan-student-current`、值 7、自动正确；
   - 故障流程：`fault_document=loan-old`、值 30、自动错误；
   - 替换流程：文档和值恢复，自动正确。
3. 打开 `summary.json`，自动正确分母是 4 个自动请求；另外 2 条是适当交人。
4. 运行工具故障：

   ```bash
   python lesson-25/analysis.py --config lesson-25/config-support.json --output lesson-25/artifacts/tool-fault
   ```

   筛选 W02、W03、W05，核对故障工具值 -1 与替换后的真实值。再找 W01，确认它没有经过工具。
5. 复制配置，选择 `route` 或 `handoff` 作为自己的故障和替换阶段。先预计受影响编号，再运行；用具体中间列解释预计是否正确。
6. 报告说明当前证据支持先修哪一步，以及仍可能同时存在的另一个故障。把采用的故障实验配置复制到 `config.json`；采用检索实验时执行 `cp lesson-25/config-start.json lesson-25/config.json`。然后生成根目录提交结果：

   ```bash
   python scripts/course.py run 25
   ```

   确认 `lesson-25/artifacts/summary.json` 和 `fault_comparison.csv` 存在，在 `submission.json` 把 `status` 从 `in_progress` 改成 `complete`，再运行：

   ```bash
   python scripts/course.py check 25
   ```

   如果检查失败，保留报错和三组局部结果，修复路径后再检查。

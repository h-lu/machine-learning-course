# 第 25 课（S23）：多步方案失败，应该先改哪一步

## 本课要解决什么问题

同一条请求可能经过路由、资料检索或工具调用，再把结果交给使用者。最终错误可能来自上游路线、资料、工具，也可能在最后交接时产生。一次同时重写所有步骤，即使结果恢复，也无法判断哪项修改有效。本课人为加入一个已知故障，再只用参考输出替换一个步骤，比较局部中间值和端到端结果。

你要提出至少两个故障解释，比较原流程、故障流程和单步替换流程，并运行一个自己选择的故障阶段。`fault_comparison.csv` 会保存三种流程的路线、资料、工具状态和值、交人状态、最终值和结果状态，不再只给正确/错误布尔值。第一次操作卡住时直接按 [入门支持](SUPPORT.md) 的完整路径执行。

## 本课要学会什么

| 标准术语 | 本课需要掌握的含义 |
|---|---|
| 端到端评价（end-to-end evaluation） | 从原始请求到最终处理是否完成用途。 |
| 局部评价（stage-level evaluation） | 单独检查路由、资料、工具或交接步骤的值。 |
| 误差传播（error propagation） | 上游错误成为下游输入，使后续按规则运行仍得到错误结果。 |
| 替换实验（component replacement test） | 固定其他步骤，用参考输出替换一个步骤，检查局部和整体是否恢复。 |
| 竞争解释（competing explanations） | 同一失败可能来自不同环节，需要实验区分。 |

## 90 分钟安排

| 时间 | 活动 |
|---|---|
| 0–15 分钟 | 画已有流程，提出两个故障解释 |
| 15–35 分钟 | 运行检索故障，逐列追踪 W01 |
| 35–50 分钟 | 比较局部值和自动结果分母 |
| 50–65 分钟 | 运行工具故障或自选阶段 |
| 65–75 分钟 | 决定先改哪一步并写未排除解释 |
| 75–90 分钟 | 概念检查与提交 |

## 完成步骤

1. 在学生仓库根目录运行：

   ```bash
   python scripts/course.py start 25
   python lesson-25/analysis.py --config lesson-25/config-start.json --output lesson-25/artifacts/retrieval-fault
   ```

2. 打开 `fault_comparison.csv` 的 W01。从 `original_document`、`fault_document` 到 `replacement_document` 依次读取 `loan-student-current → loan-old → loan-student-current`，再比较三个 `answer_value` 和 `status`。这样才能说明局部检索变化怎样传播到最终结果。
3. 打开 `summary.json`。初始 6 条中有 4 条自动请求、2 条适当交人；检索故障使自动正确从 4/4 变为 3/4，单步替换后恢复到 4/4。人工请求单独报告。
4. 运行工具故障：

   ```bash
   python lesson-25/analysis.py --config lesson-25/config-support.json --output lesson-25/artifacts/tool-fault
   ```

   找出 W02、W03、W05 的 `fault_tool_value=-1` 和错误单位。资料请求没有经过工具，局部值不应变化。
5. 从起点另存 `config-mine.json`，在 `route`、`retrieve`、`tool`、`handoff` 中选择一个故障阶段，并把替换阶段先设为同一步。运行前写预计受影响请求和哪一列会变化；运行后逐列核对。选择 `route` 或 `handoff` 会改变比默认更多请求，可能改变你下一步优先修复的建议。
6. 若替换后仍未恢复，不要立刻排除该步；检查是否选了不同替换阶段，或是否存在第二个故障解释。把采用配置写入 `config.json`，运行 `python scripts/course.py run 25`，更新提交清单并检查。

## 必须提交什么

- 原流程、故障流程和替换流程的实际配置与结果。
- `summary.json` 和含完整局部字段的 `fault_comparison.csv`。
- W01 或另一条受影响请求从局部值到最终状态的解释。
- 两个竞争解释、自选实验前的预计、受影响分母和下一步建议。

## 不同起点怎么做

### 入门支持（Support）：逐列比较检索和工具故障

按 [SUPPORT.md](SUPPORT.md) 先做 W01，再做工具案例，不需要修改程序。

### 必做任务（Core）：用单步替换定位原因

提出竞争解释，只改变一个步骤，同时检查局部值与端到端状态，再运行一个自选阶段。

### 提高任务（Upgrade）：组合两个故障

分别替换后再组合替换，说明一个步骤恢复失败为何不一定表示它无关。

### 换数据重测（Transfer）：换一个多步作品

在检索、分类或数据处理作品中保存真实中间产物并执行一次替换。

### 自选拓展（Open extension）：增加运行时监测

为最容易传播错误的中间值增加范围、单位或来源检查，实测能发现和会漏掉什么。

## 运行限制

故障只在离线教学流程中注入。普通 CPU 数秒内完成。参考替换帮助定位当前人工案例，不证明真实系统拥有随时可用的正确部件。

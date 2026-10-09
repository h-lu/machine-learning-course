# 第一次运行与目录

先按[离线环境](../ENVIRONMENT.md)核对完整学生目录、Python启动命令和NumPy。每课从README了解任务与证据标准，自主安排工作。遇阻时按卡点读SUPPORT，那里给读取支持与命令示例，不要求统一执行全部步骤。

`contract.json` 保存任务说明：`question` 写要估计或检查的问题，`user` 写使用者，`data_source` 写数据来源并区分真实数据与人工练习，`metric` 写指标、单位和分母，`split_plan` 写哪些数据用于训练、选择方案和最后评价，`initial_expectation` 写看结果前的预计。保留标明课次的 `lesson` 字段。各字段也可引用报告中的相关段落。

`submission.json` 中，`lesson` 是课次，`report` 是报告路径，`artifacts` 是主要结果文件路径的列表，`run` 是重新生成这些结果的命令参数列表。完成本课要求后才把 `status` 改为 `complete`；仅运行成功或复制例题不算完成。字段和命令例子见[提交说明](SUBMISSION.md)与[提交流程](WORKFLOW.md)。文件检查核对格式与路径，自动复现检查核对重跑结果，两者都不替你判断结论。

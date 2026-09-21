# 第 30 课数据说明：质量、重复输入和本机计时

`performance_requests` 一行代表一次待处理请求，共 10 行。P05 重复 P01，P08 重复 P06，用来检查完全相同输入的缓存。

- `text`：本地路由程序实际读取的文字。
- `expected_route`：课程人工参考路线，用于计算正确数/10。
- `fast` 与 `thorough` 不是数据字段，而是程序中的两套透明关键词方案。
- `work_iterations`：为了获得可测量的本地计算耗时而执行的哈希轮数；它不是神经网络计算量。
- `estimated_cost_per_fresh_call`：人为给定的估算单价，只用于课程内比较。

缓存键包含规范化文字和方案名。本课的“规范化”只把英文字母转成小写并去掉空白字符；没有判断两句话意思是否相同。相同文字换方案不会命中同一缓存。`timings.csv` 是当前机器实测，耗时单位为毫秒：`total_elapsed_ms` 是 10 条请求的总时间，`mean_request_latency_ms` 是其除以 10 的平均每条延迟，`fresh_compute_ms` 和 `cache_lookup_ms` 是其中两类环节的累计时间。这些值会随负载变化；`summary.json` 的正确数、新计算次数和估算成本是确定性结果。

`config.json` 的 `repeat_input_check` 用于完成单因素检查：只替换一条原本重复的文字，其余 9 条、参考路线和方案不变。`changed_records.csv` 保存改动后的确定性路由与缓存命中结果；实测耗时仍只放在 `timings.csv`，因此 `records.csv` 和 `changed_records.csv` 都可逐字节重跑核对。

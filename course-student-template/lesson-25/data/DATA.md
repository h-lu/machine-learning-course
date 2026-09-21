# 第 25 课数据说明：同一套设备请求流程

这六课使用同一套人工校园设备请求。所有规定、库存、费用、账户请求和失败都是课程编写者制作的离线样例，不代表真实学校或平台。`W01`–`W12` 都是可以反复查看的**开发请求**：`initial` 是前 6 条，`later` 是后 6 条。后 6 条在前几课已经使用，不能再叫最终测试。

## 一条请求有哪些字段

| 字段 | 含义、单位与是否必需 |
|---|---|
| `id` | 请求编号，必须唯一。开发请求沿用 W01–W12。 |
| `split` | `development` 表示可用于理解和修改。只有第 26 课单独文件中的 `holdout` 才用于最终评价。 |
| `batch` | `initial`、`later` 或 `final`，用于选择同一用途下的不同批次。 |
| `text` | 程序实际读取的请求文字，必填。 |
| `expected_route` | 课程参考路线：查资料 `retrieve`、查库存 `inventory`、计算费用 `calculator` 或转人工 `human`。它用于运行后核对，不保证覆盖真实世界所有合理路线。 |
| `expected_value` | 人工数据下的参考数值。借用期限单位是天，库存单位是件，费用单位是元；`null` 表示应转人工，不是数值 0。 |
| `expected_document` | 资料请求的参考文档编号，`retrieve` 请求必填。 |
| `item` | 库存请求中的设备名，`inventory` 请求必填。 |
| `days` | 逾期天数，`calculator` 请求必填，单位是天。 |

新增请求时，先写 `text`、参考路线和路线所需字段，再写预计；不能看完输出后改参考值迎合程序。缺少必填字段时程序会明确报错。未被一步基线覆盖的自拟输入应记作 `not_covered`，不自动算成错误。

## 一步基线、资料和工具

- `direct_baseline` 是透明的一步基线：借用请求统一回答 7 天、库存统一回答 1 件、费用按 1 元/天估计；它不查资料和工具。这个规则有意简单，但会对每条标准请求实际产生结果。
- `documents` 是可检索资料。`active` 表示是否为当前版本，`trusted` 表示本练习是否允许使用该来源，`keywords` 是字面检索词，`answer_value` 是可核对数值。
- `inventory` 的值以件为单位；`fee_per_day` 的单位是元/天。工具返回还会写 `ok`、`value`、`unit` 或 `error`。
- `route_training` 是训练小型路由分类器的人工例子，与 W01–W12 分开。

## 权限练习字段

- `security_cases` 每行需要唯一 `id`、存在的 `document_id` 和用户原本请求的 `requested_action`。文档编号不存在时程序会在运行前报错。
- `document_action_phrases` 是公开的字面短语表。例如文字含“导出所有账户”时，教学提取器记录候选动作 `export_accounts`。它只识别表中原样短语，不是语言理解。
- 允许动作只有读取公开资料 `read_public`、查询库存 `inventory_lookup` 和计算费用 `calculate_fee`。其他动作由权限层记为 `blocked`；程序没有真实副作用。

## 怎样读汇总指标

`automatic_count` 是实际自动执行的请求数；`automatic_correct` 和 `automatic_errors` 只在这些自动请求中计算。`sent_to_human` 单独记录交人数量，其中 `appropriate_handoffs` 是本来就需要人的请求，`deferred_automatable` 是本可自动处理但因阈值或失败而保守转人的请求。人工处理后的最终结果没有被观察，因此转人工不计作自动错误，也不能直接当作最终正确。

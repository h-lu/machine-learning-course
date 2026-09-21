# 第 32 课数据说明：开发数据与最后评价分开保存

`base.json` 保存同一 `equipment-helpdesk-v1` 项目的前课数据，其中 `transfer_requests` 是本课可反复查看的开发请求。默认运行只读取这个文件。开发请求中：

- 一行代表一条社区图书馆文字请求；
- `split` 为 `development`；
- `condition` 说明这条请求检查的输入条件；
- `expected_route` 是课程编写者给出的人工参考路线。

`final.json` 单独保存 8 条最后评价请求。先在开发数据上固定候选、指标和停止条件，再通过 `--final-data lesson-32/data/final.json` 显式读取它。不要通过文件预览、搜索或默认命令提前查看内容。

`final.json` 中：

- 一行代表一条社区图书馆文字请求；
- `split` 全部为 `final_evaluation`；
- `condition` 说明新名词、在架说法、个人信息等条件；
- `expected_route` 是课程人工参考路线。

开发运行的 manifest 只计算 `base.json` 与开发配置的 SHA-256 摘要。最后评价运行才会增加 `final_data_sha256`。摘要用于判断本次运行是否使用了相同字节，不能证明数据真实、参考路线正确或方案安全。看过这 8 条后再修改方案，同一文件只能作为开发证据；新判断需要另备数据。

`config.json` 的 `release_candidate` 只接受 `campus_original` 或 `library_adapted`。在开发证据上作出选择后，把它复制为 `config-final.json`；最后评价命令读取这份固定配置。程序会在 `selected_candidate_evaluation` 中单独报告所选候选，同时保留两个方案在相同请求上的比较供复核。

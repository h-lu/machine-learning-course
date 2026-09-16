# 第 26 课 示例数据

对显式请求动作比较关键词过滤和权限允许列表；这组样例不能证明系统安全。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`requests`。顶层字段及一行记录字段包括：`id, request, allowed, sensitive, requested_action`。

可调整参数（见 `../config.json`）：`seed`=7, `candidate`=allowlist, `max_request_chars`=100。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `candidate` | allowlist按申请动作检查权限；keyword检查危险关键词。它们都是教学演练。 |
| `max_request_chars` | 关键词过滤最多扫描请求的前多少个字符；权限允许列表直接检查申请的动作。 |

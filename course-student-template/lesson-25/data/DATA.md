# 第 25 课 示例数据

在本地材料中检索后直接引用原文回答，检查引用和拒答；不包含大模型生成。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`corpus`。顶层字段及一行记录字段包括：`kind, documents, queries, vector_source`。

`documents`含id、正文text、版本version、是否有效active和人工vector；`queries`含查询、同一向量空间中的vector、相关文档id及是否可回答。学生换查询必须同时提供或计算向量，不能把人工向量当作通用embedding。

可调整参数（见 `../config.json`）：`seed`=7, `top_k`=2, `minimum_similarity`=0.6, `active_only`=True。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `top_k` | 检索最多几篇候选，当前起步回答只引用其中第一篇；多篇证据融合需自行实现。 |
| `minimum_similarity` | 抽取式回答所要求的最低余弦相似度；未达标则拒答。 |
| `active_only` | 是否只检索数据中active=true的有效文档；有效标记需要由数据维护者核实。 |

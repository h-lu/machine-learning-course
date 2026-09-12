# S18 示例数据

计算一个微型Transformer块，训练输出头一步；不更新整个Transformer，不构成预训练实验。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`sequence`。顶层字段及一行记录字段包括：`kind, tokens, vectors, next_token_targets`。

`tokens` 为四个符号；`vectors` 为对应的人工4维向量；`next_token_targets` 为教学目标词编号，最后一个目标只是演示约定。

可调整参数（见 `../config.json`）：`seed`=7, `learning_rate`=0.05, `causal`=True。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `learning_rate` | 固定Transformer块后，输出头只更新一次时使用的步长。 |
| `causal` | 是否禁止当前位置读取后面的词元。false可用来检查未来信息进入的影响。 |

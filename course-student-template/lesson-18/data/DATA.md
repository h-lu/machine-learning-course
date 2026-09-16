# 第 18 课 示例数据

从人工构造的表示和原始特征分别拟合线性概率得分；不包含真实预训练或微调。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`representations`。顶层字段及一行记录字段包括：`id, raw, embedding, label, split`。

`raw` 为10维输入；`embedding` 为人工构造的2维表示；`label` 是潜在变量和的符号。matched使用此表示，mismatched保留一个与标签无关的方向，模拟任务不匹配。

可调整参数（见 `../config.json`）：`seed`=7, `training_examples`=24, `ridge`=0.2, `representation`=matched。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `training_examples` | 用于拟合分类得分的训练记录数量，从原训练部分抽取。 |
| `ridge` | 线性模型系数的平方惩罚强度；截距不受惩罚，0表示不加惩罚。 |
| `representation` | matched使用人工构造的匹配表示；mismatched只保留另一方向，模拟任务不匹配。 |

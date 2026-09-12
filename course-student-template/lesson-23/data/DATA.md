# S21 示例数据

评价人工编写的候选响应表；新增提示必须另行收集真实输出再评测。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`response_table`。顶层字段及一行记录字段包括：`id, query, expected, split, responses`。

`expected` 是本任务允许的类别；`responses` 是每个已列候选的人工输出；`split` 为 development/evaluation。修改candidate只能选择已有响应，修改提示文本并不会生成新输出。

可调整参数（见 `../config.json`）：`seed`=7, `candidate`=few_shot, `invalid_cost`=2.0。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `candidate` | 选择已在响应表中列出的keyword、few_shot或structured候选。新的提示必须先补对应输出。 |
| `invalid_cost` | 在一般答错损失之外，对不符合输出类别的结果再加多少惩罚。 |

# S30 示例数据

在已有线性/均值方案上比较新使用场景中的代价与重新拟合。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`table`。顶层字段及一行记录字段包括：`id, x1, x2, target, label, score, group, user, time, split`。

`id` 是记录编号；`x1/x2` 是无量纲合成特征；`target` 是连续结果；`label` 是0/1结果；`score` 是合成机制给出的概率，不是拟合模型的泛化成绩；`group` 是演示分组；`user` 是重复对象编号；`time` 是顺序；`split` 为 train 或 evaluation。每课用到的列由程序明确选择。示例评估可反复用来理解代码；自己的最终测试数据需另行保留。

可调整参数（见 `../config.json`）：`seed`=7, `training_fraction`=0.7, `ridge`=1.0, `underestimate_cost`=3.0。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `training_fraction` | 从原训练部分抽取多大比例来拟合现有方案；新批次的适配/评估另行一分为二。 |
| `ridge` | 线性模型系数的平方惩罚强度；截距不受惩罚，0表示不加惩罚。 |
| `underestimate_cost` | 低估一个单位的代价；高估一个单位的代价固定为1。 |

原模型和适配后的模型都在新批次的后半评估，参看old_on_adaptation_holdout与adapted_on_first_half_of_new_batch，避免比较不同分母。

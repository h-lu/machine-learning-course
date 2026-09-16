# 第 06 课 示例数据

比较均值与线性预测的绝对误差、平方误差和低估代价。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`table`。顶层字段及一行记录字段包括：`id, x1, x2, target, label, score, group, user, time, split`。

`id` 是记录编号；`x1/x2` 是无量纲合成特征；`target` 是连续结果；`label` 是0/1结果；`score` 是合成机制给出的概率，不是拟合模型的泛化成绩；`group` 是演示分组；`user` 是重复对象编号；`time` 是顺序；`split` 为 train 或 evaluation。每课用到的列由程序明确选择。示例评估可反复用来理解代码；自己的最终测试数据需另行保留。

可调整参数（见 `../config.json`）：`seed`=7, `underestimate_cost`=3.0, `prediction_shift`=0.0。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `underestimate_cost` | 低估一个单位的代价；高估一个单位的代价固定为1。 |
| `prediction_shift` | 统一给模型预测加上多少，用于比较保守或宽松的预测方案。 |

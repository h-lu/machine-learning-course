# S27 示例数据

已知转移的小网格价值迭代，计算Bellman残差和策略。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`grid`。顶层字段及一行记录字段包括：`kind, width, height, start, goal, hazards, bonus_state, step_reward, goal_reward, hazard_reward, actions`。

状态为row×width+column；动作0/1/2/3是上/右/下/左；撞墙停留；到goal或hazards后回合结束。step_reward用于普通移动，goal_reward和hazard_reward替代终止步奖励。bonus_state用于检查奖励诱导的循环。

可调整参数（见 `../config.json`）：`seed`=7, `gamma`=0.9, `tolerance`=1e-08。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 随机数种子。只影响使用随机数的步骤；在同一数据、参数和环境下可重现结果。 |
| `gamma` | 未来奖励每晚一步乘以多少。必须小于1；越接近1，越重视较远的结果。 |
| `tolerance` | 价值迭代停止的数值变化要求；仍需核对输出中的Bellman残差。 |

# 第 30 课 示例数据

Q-learning从交互学习；比较多个种子与额外奖励造成的行为变化。

数据由本仓库脚本生成，未收集真实个人信息。固定种子用于重现；它不是现实世界的代表性样本。

类型：`grid`。顶层字段及一行记录字段包括：`kind, width, height, start, goal, hazards, bonus_state, step_reward, goal_reward, hazard_reward, actions`。

状态为row×width+column；动作0/1/2/3是上/右/下/左；撞墙停留；到goal或hazards后回合结束。step_reward用于普通移动，goal_reward和hazard_reward替代终止步奖励。bonus_state用于检查奖励诱导的循环。

可调整参数（见 `../config.json`）：`seed`=7, `episodes`=220, `alpha`=0.2, `epsilon`=0.2, `gamma`=0.9, `bonus_reward`=0.2。

替换数据时保留相应字段和数值形状，或者一起修改 `analysis.py`。写下新数据如何得到、每条记录代表什么、哪些结果已知。程序输出在 summary.json 的 provenance 中记录实际输入哈希。

## 参数怎样改变实验

| 参数 | 含义 |
|---|---|
| `seed` | 五个训练种子从这个值开始；五个独立评估种子从它加1000开始，评估时只换起点，不更新策略。 |
| `episodes` | 每个训练种子与网格交互多少个回合；每回合最多60步。 |
| `alpha` | Q-learning每次用新目标修正旧估计的比例。 |
| `epsilon` | 以多大概率随机探索一个动作；其余时候使用当前估计最优动作。 |
| `gamma` | 未来奖励每晚一步乘以多少。必须小于1；越接近1，越重视较远的结果。 |
| `bonus_reward` | 到达奖励点额外加多少奖励；如果撞墙后仍留在该点，本例也会给奖励，可暴露奖励漏洞。 |

每个训练策略固定后，在五个独立评估种子选出的其他合法起点运行。五个训练种子共得到25条评估结果，比较使用同样的起点。该实验没有测试全新地图。

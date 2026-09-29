# 第 06 课二次模拟冷读与练习复核（2026-09-29）

本轮复核 `lesson-06`（课程编号 S04）。第 06 课此前已修订并发布；本次重点检查学生第一次读到的对象、术语和最后的提交步骤，并使用仅含学生材料的独立副本再次运行。复核者已接触过上一版课件与题库，因此这不是完全盲读；也不是学生真人试读或 90 分钟课堂计时。

## 学生路径与发现的停顿点

按 README 首屏 → SUPPORT 第一项任务 → LEARN 所需解释 → 起点结果 → 权重对照 → 个人容量检查 → 报告和提交检查走一遍。第一步是在仓库根目录运行 `start 06` 与 `analysis.py --config lesson-06/config-start.json --output lesson-06/artifacts/support-start`，然后先打开 `records.csv` 的 B05/linear 行；不需要教师提供额外路径。学生应先知道一行代表一位同学的一次排队观察、实际等待与预测值均以分钟计、模型只用加入队伍时前面的人数作为特征。程序读取 24 条人工数据和起点配置，写出逐条表、方法汇总表和摘要。

这次复核发现并修订：

| 冷读停顿点 | 处理 |
|---|---|
| “一行窗口记录”与“提醒哪位同学”没有连起来；不同日期的验证记录被假想成同一轮 | 明确每行是一位同学的一次观察，联系名额属于假想批次，不冒充真实同轮服务 |
| 线性回归、特征、模型参数首次出现时解释不足 | 就地说明特征是预测输入，给出截距＋斜率×排队人数的关系，并说明本课未读取学生上节模型 |
| 同样排 1 人却等候不同，容易误以为程序算错 | 用 A06 与 B05 的同预测、不同真实等待做一高估一低估的手算；指出模型没有使用窗口等信息 |
| `config.json` 容易被误认为能同时保存两个用途的结论 | 明确它只控制一次主结果重跑，两条建议写在报告中；给出只改容量的具体做法和 JSON 格式检查 |
| 并列预测按编号排序可能被误读成“编号靠前更需要提醒” | 说明编号只用于确定性地打破并列，不是风险证据；报告要求讨论这一限制 |
| S04-A-05 的“核对记录”与课程中的人工联系名额不一致 | 统一为“联系并提醒同学”，保留正类、候选、容量与事后评价的区别 |
| 原 S04-B-01 只检查大误差，不检查与 A-01 对应的误差方向 | 改为配送时间一高估一低估的 MAE 计算，B 版仍用新情境检查同一知识点 |
| 原 S04-B-05 称仅降低阈值后，较低分新候选可能改变前三名 | 按固定预测和降序排序重新推导：原候选已超过容量，新候选分数更低，前三名及同批误报漏报不变；题目、选项和解释均已修正 |

标准术语与概念界限对照了 [Google 机器学习术语表](https://developers.google.com/machine-learning/glossary)、[Google 的分类阈值与混淆矩阵说明](https://developers.google.com/machine-learning/crash-course/classification/thresholding)和 [scikit-learn 的决策阈值说明](https://scikit-learn.org/stable/modules/classification_threshold.html)。本课把回归模型预测的**分钟数**与 8 分钟提醒阈值比较，没有把 8 分钟写成分类概率。

## 实际运行与练习核对

最终学生材料复制到独立目录 `/tmp/lesson06-v17-finalstudent.iQRaJe`；仅修改该副本的配置、模拟报告和提交状态，没有把示例作业推送到真实学生仓库。依次执行：

```bash
python3 scripts/course.py start 06
python3 lesson-06/analysis.py --config lesson-06/config-start.json --output lesson-06/artifacts/support-start
python3 lesson-06/analysis.py --config lesson-06/config-support.json --output lesson-06/artifacts/support-compare
python3 -m json.tool lesson-06/config-mine.json
python3 lesson-06/analysis.py --config lesson-06/config-mine.json --output lesson-06/artifacts/my-check
python3 -m json.tool lesson-06/config.json
python3 scripts/course.py run 06
python3 scripts/course.py check 06
python3 scripts/course.py ci
```

`config-mine.json` 与主结果的 `config.json` 只把容量设为 1；权重对照只把低估权重从 3 改为 1，各次结果存入不同目录。B05 实际 8、预测约 6.333，低估约 1.667 分钟，权重 3 下逐条加权误差分数为 5；A06 实际 4、预测也约 6.333，高估约 2.333 分钟。两人的输入排队人数都为 1。起点 `linear` / `buffered` 的 MAE 分别约 2.556 / 3 分钟，平均加权误差分数约 6.111 / 3；权重改成 1 后平均加权分数分别约 2.556 / 3，预测及提醒未变。容量 1 时两种方法都只提醒 C06，各有 TP/FP/FN/TN = 1/0/3/2，四项之和为 6，`alerts=1`。主结果与个人容量结果一致。模拟报告、任务说明、配置及引用的被忽略输出均已加入本地 Git 提交 `be34131` 并打 `v2-l06-final` 标签；`check 06`、整仓 `ci` 均通过。

题库仍有 32 课、320 题。S04 五个知识点分别配 A/B 各一题，题号和正确选项位置沿用 v16；其他 31 课的题库对象逐项未变。A/B 十题按题面重新计算，选择顺序为 A：`0,3,1,0,2`，B：`2,1,3,2,0`，与教师源答案一致。B-05 的数学复核还用了预测分数 `90,80,70,60`、容量 3，以及降低阈值后新加入的 `50,40,30`：前三仍为 `90,80,70`，所以同一批记录的最终决定和误报漏报不变。由于复核者事先见过上一版答案，此处是逻辑与文字复核，不能称为新学生盲答。

完整仓库执行 `python3 tools/validate_course.py` 八组检查通过；独立 `PYTHONPATH=ml-check pytest -q ml-check/tests` 为 81 项通过。上述命令证明本环境中的材料、计算与提交路径可执行；真实初学者是否无需帮助以及能否在 90 分钟内完成，仍须真人试读或授课观察。

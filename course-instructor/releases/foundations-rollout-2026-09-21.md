# 第 05–08 课问题与评价模块发布记录：2026-09-21

## 范围与版本边界

本记录适用于学生 `lesson-05` 至 `lesson-08`，对应 S03–S06。第 01–04 课已经授课，学生材料、概念题和成绩依据冻结；本模块不追溯改变前四课，也不使用本模块的新题解释旧场次。

本轮保留已经成套完成的 S05–S06，并加深 S03–S04 的选择与证据要求。最终汇集题库的目标版本是 `ml-v13-course-map-2026-09-21`；题库文件摘要、仓库提交和生产部署信息在完成整仓验收后补记。

| 课次 | 标题 | 本课留下的主要证据 |
|---|---|---|
| S03／第 05 课 | 怎样比较才接近未来使用 | 时间、分组与随机划分的评价对象、编号、分母和 MAE；保留测试不参与开发选择 |
| S04／第 06 课 | 什么算做好了，失败会造成什么后果 | 同一批预测上的 MAE、非对称损失、误报漏报、容量和实际提醒编号 |
| S05／第 07 课 | 还缺哪些数据，哪些记录值得补 | 相同新增预算下的覆盖、标签来源和固定评价；合成标签不当作新增真实观察 |
| S06／第 08 课 | 一次小实验能否改变最初的问题 | 同一起点上的单因素候选、训练阶段学得的处理参数、验证选择和最后测试 |

## 学生路径与产物

四课都从学生仓库根目录使用 `scripts/course.py start/run/check`。起点、现成对照和个人配置分别写入不同输出目录；主要产物为 `summary.json`、`comparison.csv` 和 `records.csv`，S05 另有 `added_samples.csv`。README、SUPPORT、LEARN、数据说明和报告提示要求学生在看结果前写预计，核对一项带单位和分母的计算，只改变一个设置，并说明什么证据会使自己保留、限制或停止建议。

S03–S04 的本轮模拟在全新临时学生副本中实际执行了以下完整链路：

```text
python3 scripts/course.py start 05
python3 lesson-05/analysis.py --config lesson-05/config-start.json --output lesson-05/artifacts/support-start
python3 lesson-05/analysis.py --config lesson-05/config-support.json --output lesson-05/artifacts/support-compare
python3 lesson-05/analysis.py --config lesson-05/config-mine.json --output lesson-05/artifacts/my-check
python3 scripts/course.py run 05
python3 scripts/course.py check 05

python3 scripts/course.py start 06
python3 lesson-06/analysis.py --config lesson-06/config-start.json --output lesson-06/artifacts/support-start
python3 lesson-06/analysis.py --config lesson-06/config-support.json --output lesson-06/artifacts/support-compare
python3 lesson-06/analysis.py --config lesson-06/config-mine.json --output lesson-06/artifacts/my-check
python3 scripts/course.py run 06
python3 scripts/course.py check 06
```

两课的提交检查均通过。S05–S06 的起点、对照、个人检查和提交链路已记录在此前的模块复核与分层指导复核中；它们本轮没有被作为新课重写。

## 已有验收证据

- [S03–S04 深化与模拟冷读记录](../lessons/S03/REVIEW-2026-09-21.md)记录了阅读顺序、实际命令、手算、个人单因素检查、结果文件摘要和失败继续办法。
- [第 05 课冷读与难度复核](../reviews/lesson-05-cold-read-2026-09-21.md)记录了两种未来用途、划分对象和题目迁移检查。
- [S01–S06 复核记录](../reviews/s01-s06-2026-09-19.md)与[S01–S07 分层指导复核](../reviews/s01-s07-guided-review-2026-09-19.md)保存 S05–S06 的命令演练和证据边界。
- 本轮 S03–S04 记录中的专项结果为 `test_foundations.py` 22 项通过、两项定向支持路径测试通过、S03/S04 教师参考独立核算通过、学生严格材料检查为 32 课 0 项需处理。整仓最终结果仍以发布前重新执行的 `validation/latest.json` 为准。
- [前八课概念题冷读记录](../reviews/check-cold-read-c01-s06-2026-09-20.md)核对了 S03–S06 每课五个知识点和 A/B 对应；最终汇集到 v13 后仍须重新执行整库题目检查。

## 证据边界

上述冷读是模型按初学者顺序进行的模拟冷读；命令确实在临时副本运行，但没有真人学生参与，也没有测量 90 分钟课堂完成时间。程序通过证明路径、数据和确定性产物能接起来，不证明学生已经理解报告中的选择与结论。

## 发布后补记

正式同步和上线后补充以下可核实信息：

- GitHub 完整仓库提交：待补。
- Gitea 学生模板、教师仓库和 `ml-check` 提交：待补。
- 学生发布仓库 `course-student-release-2026` 提交：待补。
- v13 汇集题库 SHA-256、整仓验证命令、测试数量和 `validation/latest.json` 状态：待补。
- 生产镜像标识、部署时间、数据库与旧题库备份路径、健康检查结果和旧场次快照核对：待补。
- 真人试读或实际课堂观察：尚未进行；如后续发生，另记参与人数、设备、首次找到结果和完成各阶段的时间。

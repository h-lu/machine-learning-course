# 第 05–08 课问题与评价模块发布记录：2026-09-21

## 范围与版本边界

本记录适用于学生 `lesson-05` 至 `lesson-08`，对应 S03–S06。第 01–04 课已经授课，学生材料、概念题和成绩依据冻结；本模块不追溯改变前四课，也不使用本模块的新题解释旧场次。

本轮保留已经成套完成的 S05–S06，并加深 S03–S04 的选择与证据要求。汇集题库已经以 `ml-v13-course-map-2026-09-21` 发布；题库文件摘要、仓库提交和生产部署信息见文末正式发布记录。

| 课次 | 标题 | 本课留下的主要证据 |
|---|---|---|
| S03／第 05 课 | 怎样划分数据，才能让验证更接近实际使用 | 时间、分组与随机划分的评价对象、编号、分母和 MAE；保留测试不参与开发选择 |
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
- [第 05 课可读性与练习路径复核](../reviews/lesson-05-cold-read-2026-09-22.md)记录了本轮初学者顺序冷读、A/B 窗口互换检查、报告模拟作答和完整命令实跑。
- [S01–S06 复核记录](../reviews/s01-s06-2026-09-19.md)与[S01–S07 分层指导复核](../reviews/s01-s07-guided-review-2026-09-19.md)保存 S05–S06 的命令演练和证据边界。
- 本轮 S03–S04 记录中的专项结果为 `test_foundations.py` 22 项通过、两项定向支持路径测试通过、S03/S04 教师参考独立核算通过、学生严格材料检查为 32 课 0 项需处理。整仓最终结果见文末正式发布记录。
- [前八课概念题冷读记录](../reviews/check-cold-read-c01-s06-2026-09-20.md)核对了 S03–S06 每课五个知识点和 A/B 对应；汇集到 v13 后的整库检查已经通过，数量见文末正式发布记录。

## 证据边界

上述冷读是模型按初学者顺序进行的模拟冷读；命令确实在临时副本运行，但没有真人学生参与，也没有测量 90 分钟课堂完成时间。程序通过证明路径、数据和确定性产物能接起来，不证明学生已经理解报告中的选择与结论。

## 正式发布记录

- 内容提交：GitHub 完整仓库 `fea7ab2`；Gitea 学生模板 `f0807a4`；教师课包内容 `19a1d2a`；`ml-check` `e7bf5a0`；学生发布仓库 `4f7406f`。
- 题库：`ml-v13-course-map-2026-09-21`，SHA-256 为 `537bf31972b8cb3655f1cd1e9fcd245ea7bf6713ae3187d899e4c4e446c9720f`。
- 整仓验证：`python3 tools/validate_course.py` 的 8 组检查全部通过，其中学生实验 131 项、32 课教师参考 117 项独立核算、教师脚本 15 项、`ml-check` 单元测试 81 项通过，学生、教师和课程规划严格检查均通过；另行运行 `PYTHONPATH=ml-check pytest -q ml-check/tests`，81 项通过。
- 学生路径实跑：在全新学生仓库副本中完成第 05–32 课 151 条命令，全部退出码为 0；随后执行整仓 `python3 scripts/course.py ci` 通过。该结果证明命令和确定性产物可以衔接，不等于真人理解或课堂用时证据。
- 生产发布：镜像 `ml-check:2026-09-21-v13` 于 `2026-09-21T18:33:59Z` 至 `2026-09-21T18:34:03Z` 完成切换；内网和公网健康接口均返回正常。
- 回退材料：数据库备份为 `/home/ubuntu/ml-check/data/ml-check.before-v13-20260921T182552Z.sqlite3`，服务源码与部署文件备份为 `/home/ubuntu/ml-check/backups/source-before-v13-20260921T182552Z.tar.gz`；历史题库文件保存在 `/home/ubuntu/ml-check/data/session-banks/`。
- 历史数据核对：切换前后用户、场次、作答和学习完成记录分别为 64、4、1649、169，SQLite 完整性检查通过；场次 7、8、9、11 分别固定到 v4、v6、v11、v11 题目快照，不随 v13 改写。
- 真人试读边界：本次没有真人首次试读或 90 分钟课堂计时。后续课堂观察需单独记录学生停顿点、概念解释和各阶段实际用时，不能用上述模拟冷读与命令实跑替代。

## 2026-09-22 第 05 课补充发布

第 05 课按[新一轮冷读与实跑记录](../reviews/lesson-05-cold-read-2026-09-22.md)重写了 README、SUPPORT、LEARN、数据说明和报告提示，并新增 A/B 窗口互换检查。具体提交、`ml-v14-s03-readability-2026-09-22` 题库摘要、测试数量、生产切换时间和回退材料见[发布说明](../RELEASE.md)。第 01–04 课没有修改，历史场次继续读取创建时的题目快照。

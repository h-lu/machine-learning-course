# S03 运行单：怎样划分数据，才能让验证更接近实际使用

状态：第 05 课可读性与练习路径已以 `ml-v14-s03-readability-2026-09-22` 发布；学生目录为 `lesson-05`。第 01–04 课已授课并冻结，本次不修改。

## 本课关系与前置知识

学生已经见过输入、标签、训练集、验证集、测试集和 MAE。本课只推进一个主要关系：**数据划分必须接近模型将来的使用对象和时间**。

同一等待时间模型有两个用途：预测训练中已经出现的取餐窗口在较晚日期的等待时间，或预测训练中没有出现的新取餐窗口。前者用时间顺序划分检查，后者用分组划分检查。随机种子只能让一次随机划分可复现，不能替代用途判断。结束后小票时间构成目标泄漏，任何划分方法都不能修复它。

## 课前准备

从学生仓库根目录实际运行：

```bash
python3 scripts/course.py start 05
python3 lesson-05/analysis.py --config lesson-05/config-start.json --output lesson-05/artifacts/support-start
python3 lesson-05/analysis.py --config lesson-05/config-support.json --output lesson-05/artifacts/support-compare
python3 lesson-05/analysis.py --config lesson-05/config-group-check.json --output lesson-05/artifacts/group-check
```

确认起点 time 为 12 条训练、6 条验证、共有 3 个窗口；group 为 A 的 6 条训练、B 的 6 条验证、共有 0 个窗口。日期对照只改变 time；验证窗口对照将 group 改为 B 训练、A 验证，C 仍保留为测试。终端不再突出本课未使用的加权误差，先显示训练数、验证数、共有窗口数和验证集 MAE。

## 90 分钟组织

- 0–12 分钟：让学生用完整句子写两个用途，不先展示 MAE。
- 12–28 分钟：运行起点，打开 `comparison.csv` 和 `summary.json`，核对编号、分母和分组对象。
- 28–45 分钟：手算 time 的六条绝对误差平均值，追踪 B05 的正常预测与目标泄漏示范。
- 45–65 分钟：学生按主要用途选择日期边界检查或验证窗口检查，运行前先写改变条件。
- 65–75 分钟：整理支持证据、限制证据和两种用途的建议。
- 75–90 分钟：A 版 4 分钟、AI 学习 5 分钟、B 版 4 分钟、提交 2 分钟。

## 观察与提问

先问具体对象，不先问定义：

- 模型要预测已经见过的取餐窗口，还是训练中没出现的新窗口？
- 这行 MAE 用了哪些验证编号，分母是多少？
- `shared_sites=3` 或 `0` 分别表示什么？
- 小票时间在做预测时是否已经存在？
- 个人检查改变了日期范围还是验证窗口？这个结果怎样可能改变建议？

学生答不上来时退回一条记录、一组编号或一个分母，不增加新术语。代码可以由 AI 帮助完成，但学生必须能解释实际文件中的数字。

## 失败支持与验收

入门路径第一项任务能在五分钟内开始：写两个用途和预计。运行失败时，学生先用 SUPPORT 的小表核对数量和 MAE，明确标记“尚未运行”，保留完整命令和报错，修复后补跑。排错参考值不能当作学生实验结果。

必做证据包括：两个用途的 time/group 对应关系；训练与验证编号、窗口、分母和 MAE；一次 MAE 手算；目标泄漏解释；运行前的改变条件；日期边界或验证窗口检查；一条支持证据、一条限制证据和两句用途建议。使用 SUPPORT 不设置分数上限，也不需要再交一套 Core。

## 教师备课验证

在完整工作区运行：

```bash
python3 course-instructor/scripts/validate_reference_coverage.py --lesson S03
python3 -m unittest course-student-template.tests.test_foundations course-student-template.tests.test_guided_support
```

再按学生顺序从全新副本执行 README → SUPPORT → 所需 LEARN → 实际命令 → 报告 → `course.py check`。自动测试和模型模拟冷读不等于真人 90 分钟试读；真实学生的停顿点与完成时间另行记录。

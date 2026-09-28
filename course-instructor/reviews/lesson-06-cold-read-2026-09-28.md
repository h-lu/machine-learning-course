# 第 06 课模拟学生冷读与练习复核（2026-09-28）

本记录基于完整课程仓库 `67c18f4` 之后的第 06 课修订工作树。受检对象是 `course-student-template/lesson-06`、学生术语表和 S04 概念题；最终发布提交与服务题库版本见[发布说明](../RELEASE.md)。冷读由模型按初学者视角模拟，命令确实在独立学生副本中运行；没有真人首次试读，也没有 90 分钟课堂计时。

## 只按学生页面首次阅读

顺序为第 06 课 README 首屏 → SUPPORT 第一项任务 → LEARN 所需的误差与提醒说明 → SUPPORT 命令 → 实际结果 → 报告与提交检查。冷读阶段不看教师参考、题库答案或旧版学生报告。

第一项动作是从仓库根目录运行 `start 06` 和本课起点，打开 `lesson-06/artifacts/support-start/records.csv` 的 B05/linear 行。开始前需要知道“低估＝预测少于实际”“线性回归是本课给定模型”“一行记录的实际与预测值以分钟计”。运行读取 `data/base.json` 的 24 条人工记录和 `config-start.json`；生成 `records.csv`、`comparison.csv`、`summary.json`。成功后先看 B05 的 `actual=8`、`prediction≈6.333`，重算绝对误差约 1.667 分钟及权重 3 下的逐条加权误差分数 5。

第二步只把低估权重从 3 改成 1，使用准备好的 `config-support.json`，对照两份 `comparison.csv`。第三步只把 `capacity` 改为 4，保存为 `config-mine.json`；先写预计，再看实际提醒编号和四类计数。模拟报告记录两个用途、不同评价、个人容量检查、支持证据与代价。程序不能运行时，材料要求保留报错、注明“仅手算，尚未运行”，修好后补跑，不能把核对示例冒充实验。

## 冷读中发现并已修改的停顿点

| 停顿点 | 修订 |
|---|---|
| 首屏就出现“原回归”“缓冲方案”，没有说明模型是否来自上节课 | 明确 `linear` 是本课用 12 条训练记录拟合的给定线性回归，`buffered` 仅在其预测上加 4 分钟；不读取学生第 05 课模型 |
| “实际至少 8”“预测至少 8”“候选”“提醒”连在长句里，容易当作同一个阈值 | 用四行数值表分开事后真实类别、当时可用预测、候选、容量内的最终提醒及 TP/FP/FN/TN |
| 学生打开原始 JSON 会看到工作人员数、天气、活动标记，却不知道是否进入模型 | 数据说明逐列解释，并明确本课只把 `queue_length` 用作预测特征 |
| 加权误差容易被写成实际损失的分钟数，`eligible` 容易当成 `alerts` | 把它称为评价分数，写出逐条与平均的分母；分别解释候选数、实际提醒数和四类计数 |
| 报告提示抽象，容易照抄核对数字 | 改为运行前预计、B05 与高估记录手算、两份配置路径、提醒编号、两条有代价的建议 |
| A/B 中个别题未明确记录配对、阈值作用于预测，或把“可能变化”写成不精确结论；AI 学习说明过短 | 保留五个知识点和 10 个稳定题号，补清题干条件、算式与解释；五段学习说明先给术语定义，不复述题目 |

术语核对参考了 scikit-learn 的 [平均绝对误差说明](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_error.html)、[阈值与决定的区别](https://scikit-learn.org/stable/modules/classification_threshold.html)及[不同错误后果的例子](https://scikit-learn.org/stable/auto_examples/model_selection/plot_cost_sensitive_learning.html)。本课在回归预测的分钟数上自定提醒阈值，并未使用分类器的默认概率阈值；课堂权重也只是后果假设。

## 实际执行与结果

环境为本机 Python 3、NumPy 和普通 CPU；先把学生模板复制到全新临时 Git 仓库，不打开教师答案。按修订后的 SUPPORT 执行：

```bash
python3 scripts/course.py start 06
python3 lesson-06/analysis.py --config lesson-06/config-start.json --output lesson-06/artifacts/support-start
python3 lesson-06/analysis.py --config lesson-06/config-support.json --output lesson-06/artifacts/support-compare
python3 -m json.tool lesson-06/config-mine.json
python3 lesson-06/analysis.py --config lesson-06/config-mine.json --output lesson-06/artifacts/my-check
python3 scripts/course.py run 06
python3 scripts/course.py check 06
python3 scripts/course.py ci
git add lesson-06
git add -f lesson-06/artifacts
git diff --cached --name-only
```

`config-mine.json` 由起点另存，只将容量设为 4；模拟报告、任务说明和完成状态在检查前填写。实际生成的目录含 `summary.json`、`comparison.csv`、`records.csv`。起点的 linear/buffered MAE 分别为约 2.556/3 分钟，平均加权误差分数为约 6.111/3；权重改成 1 后，预测与提醒不变，两者的平均加权误差分数分别为约 2.556/3。容量改成 4 后，linear 的候选/提醒数为 3/3，TP/FP/FN/TN 为 3/0/1/2；buffered 为 6/4 和 3/1/1/1。逐条表确认 buffered 提醒 A06、B06、C05、C06，其中 A06 误报、B05 漏报。`check 06` 和整仓 `ci` 均通过，模拟 Git 提交和 `v2-l06-final` 标签已创建；没有向真实学生仓库推送模拟作业。

在只看学生可见题干和选项的条件下，S04 A 版五题选择 0、3、1、0、2，B 版五题选择 2、1、3、2、0；之后才与教师源答案比较，10 题均一致。题库的人工复核仍检查 A/B 同号概念对应、B 版情境变化和学习说明不泄露题目。题目正确不证明不同基础的真实学生都能独立完成。

## 验收界限

模型模拟冷读能发现文字和操作停顿，命令实跑能证明这一环境中的路径、计算与提交清单可用。尚未做真人首次试读、真实 90 分钟课堂计时、真实学生账号提交，也未从这些人工数据估计真实食堂中的等待或提醒效果。

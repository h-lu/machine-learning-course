# 第 07 课模拟学生冷读与练习复核（2026-09-30）

本记录对应第 07 课（S05）发布前审核。先只读学生仓库本课 README、SUPPORT、LEARN、数据说明、配置和程序，再看教师参考与题库。模型模拟冷读、命令实际运行、真人首次试读是不同证据；本轮没有真人试读或 90 分钟课堂计时。

## 第一项任务与停顿点

学生从 README 首屏进入 SUPPORT，先说明“顾客入队时根据前面人数预测等待分钟数”的用途与预计，再在学生仓库根目录执行 `start 07` 和起点命令。程序读取 28 条人工记录的 `data/base.json` 与 `config-start.json`，写出 `comparison.csv`、`records.csv`、`added_samples.csv` 和 `summary.json`。成功后先看比较表的新增条数、晚间训练条数和验证 MAE，再到新增样本表看 B01–B04 与标签来源。验证集 6 条是 MAE 的分母；午间 2 条、晚间 4 条。B05 原方案预测 3、实际 8，单条绝对误差为 5 分钟；优先补晚间后预测 5，误差为 3 分钟。失败时保留命令和报错，不将手算或旧输出当新运行。

冷读发现并修订：原首屏没有说清一行代表谁、预测时有哪些输入和标签何时取得；原命令使用本机不存在的 `python`；“补晚间”容易被误读为覆盖所有晚间窗口；输出表不单列窗口，学生需要知道如何按编号到原数据查 `site`；`source.type=synthetic` 容易与单个方案的模型生成标签混同。现在首屏、SUPPORT、LEARN、数据说明与报告提示分别说明这些对象和核对路径。人工数据中 A 仅午间、B/C 仅晚间，不能单独识别时段和窗口的作用；默认优先晚间按编号取 B01–B04，C 窗口仍无训练记录。教师运行单和参考也同步说明这个结论边界。

## 实际命令与结果

在独立学生副本 `/tmp/lesson07-finalstudent.H1kCNa`，用 Python 3.14、NumPy 和普通 CPU 执行：

```bash
python3 scripts/course.py start 07
python3 lesson-07/analysis.py --config lesson-07/config-start.json --output lesson-07/artifacts/support-start
python3 lesson-07/analysis.py --config lesson-07/config-support.json --output lesson-07/artifacts/support-compare
python3 -m json.tool lesson-07/config-mine.json
python3 lesson-07/analysis.py --config lesson-07/config-mine.json --output lesson-07/artifacts/my-check
python3 scripts/course.py run 07
python3 scripts/course.py check 07
python3 scripts/course.py ci
```

`config-support.json` 只把预算从 4 改成 2；`config-mine.json` 只把随机种子从 7 改成 11，均另存结果。起点四方案的验证 MAE 分别约为 4.333、3.836、3.000、4.333 分钟；预算 2 时优先晚间约为 3.222 分钟；种子 11 时随机抽样约为 3.083 分钟。模拟报告解释这些差异，不把较好的种子当稳定证据。填写任务说明与报告、标记完成、显式加入被 Git 忽略的输出后，`check 07` 和整仓 `ci` 均通过；本地模拟提交为 `fce3401`，打 `v2-l07-final` 标签，没有推送至真实学生仓库。

题库沿用 v17 的 S05 内容，五个知识点各有一对 A/B 题；按题面计算或判断，A 五题选项索引为 `1,0,1,3,2`，B 为 `3,2,2,0,1`，与教师源文件答案一致。B 版换用了语音、图像、配送和客服等情境，学习说明只讲知识点，不显示题干或答案。复核者已经见到教师答案，因此这是逻辑复核，不是新学生盲答。

整仓 `python3 tools/validate_course.py` 的八组检查通过，含 133 项学生实验、117 项教师参考独立核算、15 项教师脚本及 81 项服务测试；独立 `PYTHONPATH=ml-check pytest -q ml-check/tests` 为 81 项通过。`ml-check` 的 S05 题目已在 v17 生产题库中，`lessons.json` SHA-256 保持 `72b57de0a58a237b5f2513848dc366cc6b55e9039ff66794fbcc191deb050f82`，本次没有改题库或服务代码。发布后还需从学生发布仓库全新克隆，核对仅 01–07 课、题库接口与本课命令。

# 第 09–14 课学习、表示与泛化模块发布记录：2026-09-21

## 范围与版本边界

本记录适用于学生 `lesson-09` 至 `lesson-14`，对应 S07–S12。第 01–04 课已经授课并冻结，本模块不追溯修改其要求或成绩依据。

六课按“模型假设 → 概率行动 → 数据表示 → 参数更新 → 借用表示 → 泛化诊断”形成连续主线。最终汇集题库的目标版本为 `ml-v13-course-map-2026-09-21`；最终提交、题库摘要和部署信息在整仓验收后补记。

| 课次 | 标题 | 首项可核对证据 |
|---|---|---|
| S07／第 09 课 | 简单模型与复杂模型各自假设了什么 | 在 `records.csv` 重算 R21 的分钟误差，并检查区间外输入 |
| S08／第 10 课 | 预测概率怎样转成合适的行动 | 数 `[0.4,0.7)` 概率组的记录与正类，再区分概率质量和行动结果 |
| S09／第 11 课 | 数据怎样表示，模型才容易使用 | 比较 C28 在两种表示下的近邻并检查挑战输入 |
| S10／第 12 课 | 模型究竟从数据中学到了什么 | 核对 `message_length` 参数的第一次更新及学习曲线 |
| S11／第 13 课 | 借来的表示适合当前数据吗 | 区分无标签源数据、目标训练数据和验证数据，再检查不匹配 |
| S12／第 14 课 | 下一项实验应该改数据、表示还是训练方法 | 先写训练不足与过拟合的不同预计，再用曲线选择诊断实验 |

## 学生路径与产物

每课的模拟冷读都从学生 README 首屏进入 SUPPORT，只在当前动作需要时阅读 LEARN，并从仓库根目录执行：

```text
python3 scripts/course.py start NN
python3 lesson-NN/analysis.py --config lesson-NN/config-start.json --output lesson-NN/artifacts/start
python3 lesson-NN/analysis.py --config lesson-NN/config-support.json --output lesson-NN/artifacts/support
python3 -m json.tool lesson-NN/config-mine.json
python3 lesson-NN/analysis.py --config lesson-NN/config-mine.json --output lesson-NN/artifacts/mine
python3 scripts/course.py run NN
python3 scripts/course.py check NN
```

其中 `NN` 为 09–14。个人副本只修改 SUPPORT 指定的一项设置。六课分别输出 `summary.json` 以及用于假设、校准、表示、更新、迁移或曲线诊断的 CSV；每份 COLD_READ 记录都列明成功后先看的文件和行。

## 已有验收证据

- [S07](../lessons/S07/COLD_READ.md)、[S08](../lessons/S08/COLD_READ.md)、[S09](../lessons/S09/COLD_READ.md)、[S10](../lessons/S10/COLD_READ.md)、[S11](../lessons/S11/COLD_READ.md)和[S12](../lessons/S12/COLD_READ.md)分别保存模拟冷读、实际命令、首个手算和修订记录。
- 记录中的六课起点运行均不足 0.11 秒；这是程序耗时，不是学生完成时间。
- 起点、支持配置、个人副本、默认主运行和提交检查均已在临时完整学生仓库运行；六课状态完成后，`python3 scripts/course.py ci` 的逐文件哈希复现通过。
- 联调中修正了范围外单值数组读取、起点提前显示测试分数、题干与正确选项文字重合以及学生文案旧说法。修订后重新运行上述路径通过。
- 每课教师目录包含 RUNBOOK、REFERENCE 和五对 A/B 源题。最终 v13 汇集和整库服务测试仍以发布前统一运行结果为准。

## 证据边界

每份 COLD_READ 都是作者模拟第一次接触本课的学生，不是真人试读。实际命令和哈希复现能证明输入、输出及提交链路可运行，不能证明所有学生能在 90 分钟内理解模型假设、概率校准、表示或优化，也不能代替教师阅读学生对失败原因的解释。

## 发布后补记

- GitHub 完整仓库提交：待补。
- Gitea 学生模板、教师仓库、`ml-check` 和学生发布仓库提交：待补。
- v13 汇集题库 SHA-256、整仓验证命令、测试数量及验证报告状态：待补。
- 生产镜像、部署时间、数据库与题库备份、健康接口及旧场次快照核对：待补。
- 真人试读或课堂数据：尚未进行；后续应单独记录不同基础学生的停顿点和阶段用时。

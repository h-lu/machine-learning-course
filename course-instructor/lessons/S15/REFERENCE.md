# S15 参考分析 · 提示改进了，还是只适配了见过的例子

## 可复核入口

```bash
python3 course-student-template/lesson-17/analysis.py --config course-student-template/lesson-17/config-start.json --output /tmp/S15-original
python3 course-student-template/lesson-17/analysis.py --config course-student-template/lesson-17/config-support.json --output /tmp/S15-revised
```

原提示在 6 个开发问题上任务率 4/6、来源率 0、无资料说法率 2/6；三次重复的具体猜测可能不同。新提示任务率和来源率均 6/6，无资料说法率 0，格式率 4/6。拒答没有“结论”标题造成格式率非满分，不应误判为事实错误。

## 独立核算与反例

直接数 `responses.csv`：有资料四题的 expected answer 均出现，原提示两条无资料题没有“资料不足”，所以 4/6。新提示四条有资料题含 source，两条无资料题拒答，所以任务与来源均 6/6。

反例：学生删掉“资料不足”后仍引用旧 revised 输出，结果没有对应新提示，不能成为比较证据。程序会为实际新提示生成输出；教师应检查结果目录的配置摘要。

## 两条合理路线

- **采用详细提示**：用途重视来源和拒答，开发与 final 都保持收益，额外长度可接受。
- **保留简短提示或缩短新提示**：用途只需有资料问题的核心答案，格式成本较高；但必须另行处理无资料猜测风险。

学生可保留原提示，前提是风险取舍明确。不能强迫所有人把更多文字称为改进。

## 评价学生成果

最低合格有提示假设、两个开发目录、问题数与重复数、具体有/无资料案例、个人新输出、final 顺序和模板边界。若 final 已参与修改，如实报告并提出新数据即可。

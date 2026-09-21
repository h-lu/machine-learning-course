# S16 参考分析 · 怎样补充资料，而不是期待模型猜对

## 可复核入口

```bash
python3 course-student-template/lesson-18/analysis.py --config course-student-template/lesson-18/config-start.json --output /tmp/S16-threshold1
python3 course-student-template/lesson-18/analysis.py --config course-student-template/lesson-18/config-support.json --output /tmp/S16-threshold2
```

阈值 1：5 条 development 查询检索均按期望处理，任务完成 4/5；dev-03 是回答选择失败。阈值 2：dev-02 因只有一个重合词而检索失败，dev-03 仍是回答失败，任务完成 3/5。

## 独立核算与反例

D1 含“作业、提交”，dev-01 重合 2；dev-02 只有“补交”重合 1。无需调用程序即可核对阈值结果。dev-03 的 D2 两个单元分别命中“概念检查”和“阶段”，打平后程序取第一句，未包含期望的 A/学习/B，因此检索正确、任务失败。

反例：答案写 D2 但加入 D2 没有的扣分规则，来源编号正确仍不受支持。教师应让学生拆关键主张，而不只看 citation 字样。

## 两条合理路线

- **阈值 1 加强回答检查**：保留短查询召回，重点修复切分或句子选择。
- **阈值 2 并改进查询词**：降低弱匹配，要求用户或预处理提供更多有效词；接受短问题可能拒答。

路线取决于漏答与误答后果。资料不足时停止也可以是正确结果。

## 评价学生成果

最低合格有一次重合数核对、两个阈值、两类失败、资料不足、新查询和动态新输出。学生修改资料后继续提交旧 answers.csv 不合格；要求新目录重跑。

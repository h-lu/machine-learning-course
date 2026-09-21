# S18 参考分析 · 没有唯一答案时，怎样判断真的变好了

## 可复核入口

```bash
python3 course-student-template/lesson-20/analysis.py --config course-student-template/lesson-20/config-start.json --output /tmp/S18-ab
python3 course-student-template/lesson-20/analysis.py --config course-student-template/lesson-20/config-support.json --output /tmp/S18-ba
```

默认 development 四案例中，dev-01/A 总分为 1.1；dev-02/A 为 2，B 为 0.35；dev-03/A 为 1.7，B 为 1.95；dev-04/A 为 0.95，B 为 2。三项评分分歧见 disagreements.csv。交换 AB/BA 不改人工均值和加权总分，只改固定 proxy 分数。

## 独立核算与反例

`2×0.3+1×0.3+0×0.3+2×0.1=1.1`。dev-02/B 两位任务完成给 1 与 0，不能只写平均 0.5；应澄清“没有依据地猜地点是否算部分回应”。事实与支持均为 0，因此无论如何都不应将其当可靠回答。

反例：把格式权重提高到 1、其余设 0，可能让流畅错误回答获高分。这不是计算错误，而是用途不合理；权重理由应先于 final 排名。

## 两条合理路线

- **采用当前事实/支持优先量表**：课程规则问答重视可核对事实，格式只占 0.1。
- **为受控模板提高格式权重**：事实由另一流程已严格确认，当前任务只检查输出结构；必须保留事实检查而非假定永远正确。

两套量表服务的用途不同。学生可提出其他权重，只要总和为 1、有事前理由并在 final 前确定。

## 评价学生成果

最低合格有四维度、手算、分歧处理、顺序对照、个人权重、final 和 S13–S18 证据链。不能把 proxy 分数称为真实 AI 评价器测试，也不能用模拟冷读代替真人评分一致性研究。

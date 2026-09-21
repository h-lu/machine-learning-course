# S17 参考分析 · 该改提示、补上下文，还是改参数

## 可复核入口

```bash
python3 course-student-template/lesson-19/analysis.py --config course-student-template/lesson-19/config-start.json --output /tmp/S17-context
python3 course-student-template/lesson-19/analysis.py --config course-student-template/lesson-19/config-support.json --output /tmp/S17-parameter
```

同 6 案例：提示路线任务 4/6、支持 2/6、格式 4/6；上下文路线任务和支持 6/6、格式 4/6；参数候选任务 5/6、支持 1/6、格式 5/6。准备时间 10/25/60 分钟是课程情境的人工假设，不是实测开发工时；12 条参数适配样例也是固定材料元数据。

## 独立核算与反例

逐项搜索 expected answer 与 required source 可重算比例。case-01 只有上下文和参数候选给出精确时间，但参数候选写“训练样例”而非可核对资料；case-02 中参数候选猜三楼，说明固定参数候选也可能在无资料时失败。

反例：新增 case-07 却没有三路线输出时，脚本应拒绝或报告缺材料。旧案例平均不能填补新输出。

## 两条合理路线

- **上下文路线**：规则频繁更新、资料可维护且事实支持优先；接受检索与输入成本。
- **提示路线或暂缓参数路线**：只需格式改善、预算紧，或参数训练证据不足；保留低成本方案并限制事实用途。

也可选择参数适配，但需另行取得训练日志、标注来源与独立评价。不能将本课固定候选当作该证据。

## 评价学生成果

最低合格包括两组公平比较、两个具体案例、改变与不变部分、数据和维护成本、S15/S16 文件引用、固定材料限制。分数最高不自动成为标准答案。

# S12 入门支持：用增加训练轮数检验一种解释

这是必做任务的详细路径。第一项小任务是在运行前写两句话：如果只是训练轮数不够，增加轮数后训练和验证损失预计怎样；如果发生过拟合，又预计怎样。

需要概念解释时打开 [LEARN.md](LEARN.md) 中本步骤点名的小例子，不要求开始前读完整份材料。

## 1. 运行现成诊断实验

```bash
python scripts/course.py start 14
python lesson-14/analysis.py --config lesson-14/config-start.json --output lesson-14/artifacts/start
```

成功后先打开 `comparison.csv`。起点使用扩展表示训练 80 轮，候选只增加到 320 轮，其他条件不变。

## 2. 用实际数字判断

给定起点中，训练损失约从 0.301 降到 0.253，而验证损失约从 0.237 升到 0.249。更多训练继续改善已见记录，却没有改善验证记录，因此这批证据不支持“只需继续训练”。差异很小且验证集只有 12 条，结论应写成当前证据下的优先级，而不是证明唯一原因。

打开 `learning_curve.csv`，找出验证损失开始不再下降的阶段。再计算两种方法各自的“验证损失−训练损失”，写清这只是描述差距。

## 3. 做第二项单因素检查

`config-support.json` 已设置 `simpler_representation`：只去掉平方项和交互项。运行：

```bash
python lesson-14/analysis.py --config lesson-14/config-support.json --output lesson-14/artifacts/support
```

也可以另存 `config-mine.json`，只选择 `stronger_regularization`。先写预计，再比较训练与验证。某项候选没有改善也能成为有用证据。

## 4. 决定下一项工作

在报告中选择补数据、改表示或改训练方法，并引用 S09–S11 的一项实际证据。程序不会读取旧课个人结果，因此请核对路径，不要把给定起点称为自己的旧模型。

## 5. 最后评价和提交

验证集确定方案后写回 `config.json`，再改成 `evaluation_split=test`，运行 `python scripts/course.py run 14`。完成任务说明、报告和状态后运行 `python scripts/course.py check 14`。若测试后改变方案，明确把这次测试转为开发证据。

# S10 入门支持：核对一次参数更新

这是必做任务的详细路径。第一项小任务是打开 `first_update.csv`，用学习率核对 `message_length` 参数的更新方向。

需要概念解释时打开 [LEARN.md](LEARN.md) 中本步骤点名的小例子，不要求开始前读完整份材料。

## 1. 运行起点

```bash
python scripts/course.py start 12
python lesson-12/analysis.py --config lesson-12/config-start.json --output lesson-12/artifacts/start
```

成功后先看 `lesson-12/artifacts/start/first_update.csv`。起点学习率是 0.15。

## 2. 手算一个参数

`message_length` 的更新前值为 0，梯度约为 -0.330045。因此：

```text
更新后 = 0 - 0.15 × (-0.330045) ≈ 0.049507
```

正值表示在其他缩放特征固定时，这个模型的预测方向随该特征增加而上升。它不证明增加消息长度会造成需要复核，也不能直接解释为每个汉字的效果。

## 3. 读学习曲线

打开 `learning_curve.csv`，比较第 0、1、10、20 轮。再看 `comparison.csv`。起点中学习率 0.15 和 0.4 的评价准确率相同，但评价对数损失不同；这说明只看阈值后的对错会遗漏概率置信程度。

## 4. 改一个训练设置

运行已经准备的较大学习率：

```bash
python lesson-12/analysis.py --config lesson-12/config-support.json --output lesson-12/artifacts/support
```

然后把 `config-start.json` 另存为 `config-mine.json`，只改 `comparison_learning_rate` 或只改 `epochs`，先写预计再运行。不要从一次结果推出学习率越大越好。

## 5. 测试与提交

在验证集确定设置并写回 `config.json`，记录选择后把 `evaluation_split` 改为 `test`，运行 `python scripts/course.py run 12`。报告写一次更新计算、曲线比较、个人设置和“损失下降不能证明什么”。填完任务说明和状态后运行 `python scripts/course.py check 12`。

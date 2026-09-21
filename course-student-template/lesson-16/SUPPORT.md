# S14 入门支持：改变未来词元，观察较早位置


以下命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。
这条路径覆盖本课必做任务。第一项小任务：画四个格子 0、1、2、3，在因果遮罩条件下给位置 1 能看到的格子画圈。正确范围是 0 和 1；先自己画，再运行。

## 1. 运行起点

在学生仓库根目录执行：

```bash
python scripts/course.py start 16
python lesson-16/analysis.py --config lesson-16/config-start.json --output lesson-16/artifacts/support-start
```

终端提示成功后先打开 `visibility.csv`。`sequence-01` 中，位置 3 的值从 5 改为 8：因果遮罩行的输出仍约为 1.668，变化为 0；无遮罩行约从 3.419 变为 4.662，变化约 1.243。

## 2. 手算因果遮罩下的输出

到 `attention_weights.csv` 找 `sequence-01, causal_mask, before`。两个可见分数是 0 和 0.7。softmax 分母为：

```text
exp(0) + exp(0.7) ≈ 1 + 2.014 = 3.014
```

两个权重约为 0.332 和 0.668，总和为 1。值是 1 和 2，所以加权输出约为 `0.332×1 + 0.668×2 = 1.668`。写明这是人工标量，没有现实单位，也不是正确答案概率。

## 3. 比较另一个未来值

`config-support.json` 只把新的未来值从 8 改为 7：

```bash
python lesson-16/analysis.py --config lesson-16/config-support.json --output lesson-16/artifacts/support-compare
```

有遮罩的变化仍为 0；无遮罩输出变化较小。注意力权重没有变，因为这次只改 `value`，没有改用于计算权重的 `key`。

## 4. 做自己的检查

另存 `config-mine.json`，只改 `changed_future_value`。先用无遮罩条件下位置 3 的权重预计输出改变量：

```text
输出改变量 = 位置 3 的权重 ×（新值 − 原值）
```

然后运行到新目录并核对：

```bash
python -m json.tool lesson-16/config-mine.json
python lesson-16/analysis.py --config lesson-16/config-mine.json --output lesson-16/artifacts/my-check
```

若因果遮罩行发生变化，先检查你是否把 `changed_future_position` 改到了 0 或 1；程序会拒绝这种配置，因为它不再是未来位置实验。

## 5. 连到前课并提交

报告引用 `lesson-15/artifacts/evidence.json`，说明两课都没有更新基础模型。本课证据来自可查看的微型机制；仅比较两段黑箱回答不能证明内部使用了同样遮罩。

完成报告、`contract.json` 和提交状态后运行：

```bash
python scripts/course.py run 16
python scripts/course.py check 16
```

无法运行时先保留命令和报错，用上面的两个分数完成手算并标明“尚未运行”；修复后补跑，不能把核对值写成自己的运行结果。

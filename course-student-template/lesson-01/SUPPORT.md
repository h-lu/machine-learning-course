# 第 01 课入门支持：先手算一行，再让程序核对

这是第 01 课必做任务的一条完整路径，不是额外作业。你会先算 `train-03`，再运行起点，只改一个参数，最后检查一个没有标签的新输入。

## 1. 第一项任务：算出 train-03

这一行记录的是一次已经结束的排队经历：开始时前面有 2 人，最后实际等了 4 分钟。规则是：

```text
预测分钟数 = 1 + 2 × 前面人数
```

先写下：输入是 2 人；预测是 `1 + 2 × 2 = 5` 分钟；绝对误差是 `|5 − 4| = 1` 分钟。

这里的**特征**是预测时知道的前面人数，**标签**是事后记录的实际等待时间，**预测值**是规则算出的 5 分钟。实际值不能在排队开始时当作输入。

## 2. 从仓库根目录运行

根目录是能看到 `scripts` 和 `lesson-01` 的文件夹。不要把命令输入 Python 的 `>>>`。电脑没有 `python` 命令时统一使用 `python3`。

```bash
python scripts/course.py start 01
python scripts/course.py run 01
```

看到“结果写入”后，先打开 `lesson-01/artifacts/predictions.csv`。CSV 是用逗号分列的表格文本，第一行是列名。

## 3. 核对程序中的同一行

找到 `id=train-03`，只看这几列：

| 列名 | 含义 | 核对值 |
|---|---|---:|
| `queue_length` | 开始时前面人数 | 2 人 |
| `actual` | 事后实际等待 | 4 分钟 |
| `prediction_rule` | 人工规则预测 | 5 分钟 |
| `absolute_error_rule` | 预测与实际的绝对差 | 1 分钟 |

把你的手算和程序结果写进报告。如果不一致，先检查样本编号、配置和单位，不要手改 CSV。

再在 `data/base.json` 看 `train-03` 的三个背景字段。它们描述当时的工作人员、服务状态和天气，但这条规则没有把它们代入计算。记录一个你认为可能影响等待的条件，暂时不要把它写成已经验证的原因。

## 4. 只把斜率改为 1.5

把 `config.json` 另存为 `config-trial.json`，只将 `rule_slope` 改成 1.5。其余字段保持不变。先预计 `train-03` 的新预测，再运行：

```bash
python lesson-01/analysis.py --config lesson-01/config-trial.json --output lesson-01/artifacts/trial
```

打开 `trial/predictions.csv`。新预测应为 4 分钟，这一行误差为 0。不要写成“新规则已经更好”；你只核对了一行，还需要更多记录和清楚的评价方法。

## 5. 做自己的新输入检查

在 `config-trial.json` 中只改 `stress_queue`，例如设为 6。先写预计，再用上一步命令重跑。终端会显示新人数的预测。

新输入没有实际等待标签，所以不能计算绝对误差。报告应写出预测、单位、已知数据只覆盖 0–3 人，以及为什么这不能证明 6 人时可靠。

## 6. 写报告并检查文件

报告至少写：任务、`train-03` 手算、参数对照、新输入检查和限制。填写 `contract.json` 六个空字段，把最后保留的合法配置写回 `config.json`，实际完成后把 `submission.json` 状态改为 `complete`。

```bash
python scripts/course.py run 01
python scripts/course.py check 01
```

检查通过后，按 [第一次运行指南](../docs/FIRST_RUN.md) 保存结果和提交。

## 7. 卡住时怎么办

- 找不到文件：确认当前目录能看到 `scripts` 和 `lesson-01`。
- 找不到 Python：把所有 `python` 改成 `python3`。
- JSON 报错：按报错中的行号、列号检查英文双引号、逗号和数字。
- 输出没有变化：检查实际使用的 `--config` 和 `--output`，再看文件修改时间。
- 暂时不能运行：保留完整报错，先做第 1 节手算，在报告标明“尚未运行”，修复后补跑。

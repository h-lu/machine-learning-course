# 第 02 课入门支持：先算基线，再比较三个办法

这是第 02 课必做任务的一条完整路径。你会先用训练集算出一个简单基线，再在四条验证记录上比较，最后固定方案后查看测试集。

## 1. 第一项任务：算出均值基线

8 条训练标签是 `2、2、4、8、0、4、6、6` 分钟，总和为 32。**均值基线**不看人数，对每条新记录都预测：

```text
32 ÷ 8 = 4 分钟
```

验证集四条实际值为 1、3、5、4 分钟，所以基线绝对误差为 3、1、1、0 分钟，MAE 为：

```text
(3 + 1 + 1 + 0) ÷ 4 = 1.25 分钟
```

分母是参加评价的 4 条验证记录，单位是分钟。

## 2. 运行验证集起点

在学生仓库根目录运行。电脑没有 `python` 命令时统一使用 `python3`。

```bash
python scripts/course.py start 02
python lesson-02/analysis.py --split validation --output lesson-02/artifacts/validation-original
```

成功后先打开 `validation-original/predictions.csv`，找四行 `method=baseline`，核对预测、实际值和绝对误差。然后看 `summary.json` 中三种方法的 MAE。

## 3. 分清三个办法

- `baseline`：训练标签的平均值，每条都预测 4 分钟；
- `rule`：人写定的“1 + 2 × 人数”；
- `linear`：程序只用训练集拟合出的直线。

本例人工规则和回归碰巧得到相同预测，但参数来源不同。不能因为输出相同，就说人工规则也经过训练。

## 4. 做一次自己的规则检查

把 `config.json` 另存为 `config-trial.json`，只改 `rule_slope` 或 `stress_queue`，先在报告写预计，再运行：

```bash
python lesson-02/analysis.py --config lesson-02/config-trial.json --split validation --output lesson-02/artifacts/validation-trial
```

打开新旧两个 `predictions.csv`，找同一编号和同一方法比较。只改规则参数时，基线和回归不应改变。没有标签的新人数只能看预测，不能算误差。

## 5. 先看分组样本数，再解释误差

起点验证集中午间有 3 条，晚间只有 1 条。回归总体 MAE 为 0.75 分钟，但晚间唯一一条误差为 3 分钟。这两个结果可以同时成立。

报告应写：“在这 4 条验证样本上总体误差较小，但晚间只有 1 条，证据不足，需要补充晚间数据。”不要写成“回归在所有晚间都不可靠”。

## 6. 固定方案后再看测试集

在报告先写选择与理由，把选择时的配置保存为 `config-validation.json`，并生成 `artifacts/validation/`。之后只在 `config.json` 中把 `evaluation_split` 改为 `test`，其余参数保持不变。

```bash
python lesson-02/analysis.py --config lesson-02/config-validation.json --split validation --output lesson-02/artifacts/validation
python scripts/course.py run 02
```

测试结果不好时可以建议暂停或补数据。若根据测试结果修改方案，需要另找未参与修改的新数据，不能反复使用这 6 条测试记录证明新方案。

## 7. 写报告并检查文件

报告至少写：基线手算、同一样本上的三种方法、一个分组结果、自己的配置检查、查看测试前的选择和测试后的建议。填写 `contract.json`，实际完成后把 `submission.json` 状态改为 `complete`。

```bash
python scripts/course.py check 02
```

按 [第一次运行指南](../docs/FIRST_RUN.md) 保存验证和测试结果。

## 8. 卡住时怎么办

- 不知道先看什么：先看 `validation-original/predictions.csv` 的四行 `baseline`。
- MAE 算不对：核对是否使用同一批 4 条验证记录，单位是否为分钟。
- 配置改了但其他方法没变：这是正常的；规则参数只影响 `rule`。
- 测试集已经看过：如实记录，不再把它称为未见测试数据。
- 程序暂时不能运行：保留报错，先完成第 1 节手算并标明“尚未运行”，修复后补跑。

### 3.1 看一条背景条件

在 `data/base.json` 看一条验证记录的 `staff_count`、`service_mode` 和 `rain`。这些条件没有进入默认模型；先记录它们可能造成的差异，再决定是否把它作为提高任务，不要把背景字段误报成模型输入。

# 第 02 课（C02）：怎样公平比较三个预测办法

## 本课要解决什么问题

第 01 课让规则产生了预测，但“能算出来”不等于“值得使用”。本课仍用前面人数预测等待分钟数，比较三个办法：训练标签均值、人工规则和一元线性回归。

你要先在训练集上确定参数，再在验证集上比较并选定方案，最后只查看一次测试集结果。顺序很重要：如果先看测试集再修改参数，这份测试数据已经参与选择，不能继续叫独立的最后评价。

第一次学习基线、验证集或 MAE 时，按 [入门支持](SUPPORT.md) 逐步完成。它会从四条验证记录开始手算。

## 本课要学会什么

| 概念 | 学完后你能做什么 |
|---|---|
| 基线模型（baseline model） | 用简单办法作为参照，不因模型复杂就预先判定更好 |
| 训练集、验证集、测试集 | 说明哪份数据学参数、哪份选方案、哪份做最后评价 |
| 一元线性回归 | 看懂“截距 + 斜率 × 人数”，知道参数来自训练集 |
| 平均绝对误差（MAE） | 用同一批样本逐条算误差并求平均，正确写出单位和分母 |
| 分组评估 | 同时检查总体和午间／晚间结果，并先看每组样本数 |

详细数字例子见 [LEARN.md](LEARN.md)。本课不要求推导最小二乘公式。

## 90 分钟安排

- 0–15 分钟：区分三份数据，手算均值基线。
- 15–35 分钟：运行验证集，核对四条样本和三种方法。
- 35–55 分钟：带入自己的规则，检查总体与分组结果。
- 55–68 分钟：在看测试集前写下选择和理由。
- 68–78 分钟：固定方案后运行测试集，写有限结论。
- 78–90 分钟：完成概念检查和提交清单。

## 完成步骤

命令都在学生仓库根目录运行。电脑找不到 `python` 时，整套命令统一改用 `python3`。

### 1. 先写用途，只运行验证集

在 `report.md` 写清结果给谁看、预测单位是分钟，以及你认为多大的误差需要继续检查。先不要查看测试集。

```bash
python scripts/course.py start 02
python lesson-02/analysis.py --split validation --output lesson-02/artifacts/validation-original
```

程序用 8 条训练样本计算参数，再在 4 条验证样本上评价。成功后先打开 `validation-original/predictions.csv`，再打开同目录的 `summary.json`。

### 2. 用同一批四条记录重算 MAE

在 CSV 中找 `method=baseline` 的四行。训练标签平均值是 4 分钟，所以基线对四条验证记录都预测 4。实际值是 1、3、5、4，绝对误差是 3、1、1、0：

```text
基线 MAE = (3 + 1 + 1 + 0) ÷ 4 = 1.25 分钟
```

同一批验证记录上，人工规则和线性回归的 MAE 都是 0.75 分钟。该结果只描述这 4 条样本，不是 75% 准确率，也不是自动推荐。

### 3. 带入自己的规则

把本课 `config.json` 另存为 `lesson-02/config-trial.json`。可以将 `rule_slope` 改为 1.5，并把 `stress_queue` 改为 6；保持 `evaluation_split` 为 `validation`。本课不会自动读取第 01 课的配置。

```bash
python lesson-02/analysis.py --config lesson-02/config-trial.json --split validation --output lesson-02/artifacts/validation-trial
```

这个配置只改变人工规则，不改变基线和线性回归。即使人工规则的 MAE 恰好仍为 0.75，各条预测也可能已经不同，因此要核对逐条 CSV。

再看分组结果：午间有 3 条，晚间只有 1 条。晚间的一条样本中，基线误差为 0，回归误差为 3 分钟。不能用 1 条样本证明所有晚间都会如此。

### 4. 先选方案，再保存验证结果

在报告写明准备保留基线、人工规则、线性回归，还是暂不用于实际场景，并写出参数、用途、评价指标和理由。选择完成后，把同一配置另存为 `config-validation.json`：

```bash
python lesson-02/analysis.py --config lesson-02/config-validation.json --split validation --output lesson-02/artifacts/validation
```

保存这份配置和结果。它记录了你在查看测试集以前的选择依据。

### 5. 固定参数后，只查看一次测试集

只在 `config.json` 中把 `evaluation_split` 改为 `test`，其他已选参数不变，然后运行：

```bash
python scripts/course.py run 02
```

最终结果写入 `lesson-02/artifacts/summary.json` 和 `predictions.csv`。测试集有 6 条样本。重点报告事先选定方案的结果；不要看到测试分数后改选另一个办法并仍称这是最后测试。

要证明验证结果可以从保存的配置重新得到，可运行：

```bash
python lesson-02/analysis.py --config lesson-02/config-validation.json --split validation --output lesson-02/artifacts/recheck-validation
```

`recheck-validation` 应与先前保存的 `validation` 一致。

### 6. 完成报告和文件检查

填写 `contract.json` 六个字段。报告要保留运行前预计、验证阶段选择和测试后建议，不能把事后看到的结果改写成事前选择。完成实际工作后再把 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py check 02
```

检查通过不表示已经上传，也不评价结论。按 [第一次运行指南](../docs/FIRST_RUN.md) 保存验证配置、验证结果、最终测试结果和报告。

## 必须提交什么

- 程序、最终 `config.json` 和查看测试集前保存的 `config-validation.json`；
- `artifacts/validation/` 中的验证结果；
- `artifacts/summary.json` 与 `artifacts/predictions.csv` 中的最终测试结果；
- 已填写的 `contract.json`、`report.md` 和 `submission.json`；
- 报告引用的其他配置、结果和完整命令。

报告必须包含同一样本上的基线比较、至少一次 MAE 手算、分组结果及样本数、自设计检查、事先选定方案和测试后的有限建议。C02 不计平时分，但要完成入门练习。

## 不同起点怎么做

### 必做任务（Core）：按正确顺序完成比较

用验证集比较三种方法，解释一项分组结果，在看测试集前保存选择，然后固定方案完成最终评价。

### 入门支持（Support）：按 SUPPORT.md 完成

[SUPPORT.md](SUPPORT.md) 从基线的四条误差开始，提供完整命令、输出位置和卡住时的处理。它已经覆盖必做任务，不需要另交一份 Core。

### 提高任务（Upgrade）：增加一个合理基线

例如比较中位数基线。新方法仍只用训练集确定参数，在验证集上选择，不为增加模型数量而增加模型。

### 换数据重测（Transfer）：换一个时间预测任务

例如配送时间。重新说明划分依据、标签单位和使用条件，不能把本课分数直接搬过去。

### 自选拓展（Open extension）：研究误差代价

说明高估和低估分别会造成什么后果，再设计匹配的评价方式。新增指标不能在看过测试集后用来重新挑方案。

## 运行限制

需要 Python 3.10 以上、NumPy 和仓库内的 18 条人工数据。普通 CPU 即可，实验离线运行，不需要显卡或付费服务。单次运行目标不超过 3 分钟。人工样本只能帮助理解比较流程，不能证明真实食堂中的效果。

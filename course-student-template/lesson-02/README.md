# 第 02 课：一个结果能说明方案有用吗

## 本课要解决什么问题

沿用上节课的问题：用前面的排队人数预测等待分钟数。一个预测能算出来，并不说明它有用。这次为它找一个简单参照，再看总体误差和不同时段的误差。

**本课主线：训练集学参数，验证集选方案，方案确定后再用测试集做最后评价。**基线模型是用于比较的简单参照，具体例子和术语先看下面的学习材料。

你将提交程序、比较结果和报告。可以请 AI 编程和解释，但要说明怎样比较、证据支持什么。找不到文件或不会改配置时，查 [第一次运行指南](../docs/FIRST_RUN.md)；实验没有支持某种方法，也可以成为有依据的结论。

## 本课要学会什么

| 知识点 | 学完后能做什么 |
|---|---|
| 基线模型 | 为待比较的方法找一个简单参照 |
| 训练集、验证集与测试集 | 说清哪些数据学参数、哪些选方案、哪些做最后评价 |
| 一元线性回归 | 看懂“截距 + 斜率 × 特征”，知道参数来自训练集 |
| 平均绝对误差（MAE） | 逐条算绝对误差再求平均，报告分钟而不是准确率 |
| 分组评估与使用条件 | 同时看总体和不同时段的误差，并考虑每组样本数 |

先读 [LEARN.md](LEARN.md)，按“数据用途—简单基线—拟合直线—误差比较”学习。不要求推导最小二乘公式。

## 90 分钟安排

前 20 分钟理解三份数据、基线和 MAE；接着 35 分钟运行验证集并比较；用 20 分钟解释分组误差、确定方案后做测试集评价；最后 15 分钟完成概念检查与提交。

## 完成步骤

### 1. 写下用途，先运行验证集

在 `lesson-02/report.md` 说明结果给谁用、能接受怎样的误差。这是学习用途的选择，不代表这些教学数据已经能支持真实使用。先保留本课原始配置，不复制上节课整个配置文件。

在学生仓库根目录运行；电脑只认 `python3` 时仍将 `python` 换为 `python3`：

```bash
python scripts/course.py start 02
python lesson-02/analysis.py --split validation --output lesson-02/artifacts/validation-original
```

`--split validation` 表示评价验证集。数据共有 8 条训练样本、4 条验证样本和 6 条测试样本。这次只输出验证集结果，请先不要运行或查看测试集答案。

### 2. 看懂三种方法，不把默认输出当推荐

终端会按方法名称显示 MAE、单位和样本数。打开 `lesson-02/artifacts/validation-original/predictions.csv` 逐条核对；同目录 `summary.json` 保存汇总。

| 方法 | 怎样预测 | 原始配置下验证集 MAE |
|---|---|---:|
| 均值基线 `baseline` | 对每条样本都预测训练标签的平均值 4 分钟 | 1.25 分钟 |
| 人工规则 `rule` | 用人事先设定的 `1 + 2 × 人数` | 0.75 分钟 |
| 一元线性回归 `linear` | 只用训练集拟合截距和斜率 | 0.75 分钟 |

MAE 是平均绝对误差，越小表示在这批样本上平均相差越少。请用 CSV 核对至少一种方法的 MAE；示例数值不是作业必须达到的分数。各列中文解释见 [数据说明](data/DATA.md)。

本例拟合结果恰好也是截距 1、斜率 2，但参数来源不同。规则不是因为预测相同就变成了训练模型。汇总中的 `metrics` 固定保存线性回归指标，并不表示程序替你选中了它；其他方法在 `comparison`，分组结果在 `details.by_period`。

### 3. 带入自己的规则，做一次检查

把本课 `config.json` 另存为 `lesson-02/config-trial.json`。将你在 C01 最终保留的 `rule_intercept`、`rule_slope` 两个数值填进去，不要复制 C01 的 `evaluation_split: "train"`；本课保持 `"evaluation_split": "validation"`。程序不会自动读取 C01 的配置。

```bash
python lesson-02/analysis.py --config lesson-02/config-trial.json --split validation --output lesson-02/artifacts/validation-trial
```

比较自己的规则与基线、线性回归。这两个参数只改变人工规则，不改变另外两种模型。比如只把规则斜率改为 1.5，验证集 MAE 仍是 0.75，但各条预测和误差已经不同；请核对 CSV，不能只凭平均值相同判断程序没有读取新参数。进一步改参数时，另存配置和输出目录，保留每次比较依据。

看终端中的分组评估，再选一条预测偏差较大的样本，用 CSV 核对。默认晚间只有一条验证样本：基线误差为 0，规则和回归都为 3 分钟。因此，不能靠保留默认规则来修复回归的这个错误，也不能凭一条样本断言晚间总是如此。

再自己选择一个新人数，修改配置副本中的 `stress_queue` 并重跑，解释这项检查能说明什么。无标签的新输入只能检查预测和输入条件，不能证明误差更小。

### 4. 保留验证材料，确定方案后才用测试集

在报告中先写明选基线、规则还是回归，以及参数、用途、评价方法和理由；也可以得出暂不用于实际场景的结论。**选择写在报告中，程序仍输出三种方法供核对，不会自动替你挑最好的一种。**

把要保留的参数填入本课 `config.json`，保持 `evaluation_split` 为 `validation`，另存一份同样内容为 `lesson-02/config-validation.json`，然后保存这组参数的验证结果：

```bash
python lesson-02/analysis.py --config lesson-02/config-validation.json --split validation --output lesson-02/artifacts/validation
```

接着只在 `config.json` 中把 `"evaluation_split": "validation"` 改为 `"evaluation_split": "test"`，保留其他参数不变，运行：

```bash
python scripts/course.py run 02
```

最终输出在 `lesson-02/artifacts/summary.json` 和 `lesson-02/artifacts/predictions.csv`，不会覆盖子目录中的验证材料。程序沿用同一训练集拟合，在 6 条测试样本上评价。重点报告你事先选定方法的结果，不根据这次分数重新挑选。

测试结果不理想时，可以建议暂停使用或补数据；若据此改了模型或参数，要另找未参与修改的新数据再评价。公开教学数据只能练习这套方法，不能包装成真实业务中的独立测试。

### 5. 核对文件并提交

填写 `contract.json`，把 `report.md` 的提示替换成自己的说明。保存原先的选择，再补充测试结果和建议，不能把事后选择写成事前选择。报告至少给出下面两条完整的重算命令：

```bash
python lesson-02/analysis.py --config lesson-02/config-validation.json --split validation --output lesson-02/artifacts/recheck-validation
python scripts/course.py run 02
```

实际完成后，将 `submission.json` 的 `status` 改为 `complete`，保留默认运行命令和两份主要结果路径，运行：

```bash
python scripts/course.py check 02
```

按 [第一次运行指南](../docs/FIRST_RUN.md) 的第 02 课命令提交，包括验证阶段的配置和结果。`artifacts/` 被 Git 忽略，需要 `git add -f` 显式加入；文件检查通过不等于已经上传。

## 必须提交什么

程序和最终配置、最终两份结果、验证配置 `config-validation.json` 及其结果、任务说明、自己的报告和提交清单。报告应有同一批样本上的基线比较、分组或失败分析、自设计检查、事先选定的方案，以及测试后的建议。

可以保留基线、保留规则、继续研究回归或暂时不使用，理由要与实际比较相符。报告引用其他试验时也需提供相应配置、结果和命令。C02 不计平时分，但要完成入门练习。

## 不同起点怎么做

入门支持：先用给定数据核对两条误差，再求平均，请 AI 解释不懂的量；仍需自己选择用途和方案。提高任务：增加有意义的特征，或比较将数值排序后取中间位置的中位数基线。新方案仍在验证集上选择，不为了堆模型增加模型。

## 运行限制

需 Python 3.10 以上及已安装的 NumPy。数据只有 18 条，普通 CPU 即可；实验不联网、不调用付费服务。AI 辅助与在线概念检查另按教师安排。这些人工样本仅用于理解比较方法，不能证明真实食堂里的效果。

# 第11课操作参考

本页提供配置、运行和结果核对方法。概念见 [LEARN](LEARN.md)，任务要求见 [README](README.md)。

## 先读已有输出

在学生仓库根目录运行`python3 lesson-11/analysis.py`，生成一份人工特征基线。输出目录已有文件时程序停止；重跑使用新的`--output`路径。

|文件|用途|
|---|---|
|config.json|这次实际使用的表示、训练和复核设置|
|representation.json|训练文本拟合出的表示参数；人工特征的均值/标准差，或词表、DF与IDF|
|prediction_trace.json|一条真实开发短信的分词、未知词、非零值及预测贡献|
|records.csv|按ID保存开发记录的概率、行动和真实标签，供同记录比较|
|summary.json|开发集指标、划分与代码哈希、矩阵存储及维数|
|model.npz|这份表示上重新训练的系数和截距|
|curve.csv|固定步数内的训练目标与开发损失；不是自动选择停止点|
|first_update.json|首轮完整批量更新，供需要时查训练实现；本课不用把训练步骤作为主研究|

先看表示类型，再找相应字段。默认`manual`不建立词表，追踪中的每项特征使用`raw_value`（原始值）、`training_mean`（训练均值）、`training_scale`（训练标准差）和标准化后的`value`；按“原始值减训练均值，再除以训练标准差”核对。这里没有词次数`count`、DF或IDF；`unknown_tokens` 对人工特征不适用。

`bow`和`tfidf`才使用固定词表、count、DF、IDF及未知词记录。BoW记录IDF便于查训练统计，但不把它乘入词次数；TF–IDF才乘IDF。两类表示最后都核对`value × weight`的贡献和、截距、得分与概率。

## 运行第二套配置

复制`lesson-11/config.json`到你自己命名的配置文件，只改计划研究的表示设置。例如选择`bow`或`tfidf`，以及自己有理由的`min_df`。使用新目录：

```bash
python3 lesson-11/analysis.py --config lesson-11/my-config.json --output lesson-11/artifacts/my-run
```

先保存 `my-config.json`，再执行命令。

|配置|含义与限制|
|---|---|
|representation|`manual`为第10课六个人工特征；`bow`为原始词频；`tfidf`为词频乘平滑IDF|
|min_df|词至少出现在多少条训练短信中；只对bow/tfidf使用，默认2|
|max_features|最多保留多少词，默认1200，上限10000；先按训练DF降序取词，同DF按字母排序，最终坐标按字母排序|
|token_pattern|`words_numbers`保留英文词和数字串；`words`只保留英文词；都会转小写，词内英文撇号保留|
|normalization|bow/tfidf默认`l2`，每条非零行除以自己的长度；`none`保留未归一化的值。人工特征始终使用训练均值和标准差|
|trace_id|留空为第一条dev记录；可填某个真实dev ID，重新核对你选的记录|

人工特征沿用第10课，不受词表设置影响。空词表会报错，先检查拆词和min_df，而不是把开发文本加进去补词。未知词被忽略；全部未知或空输入得到零词向量，预测仍可由截距产生。

<a id="复核learn中的真实tfidf记录"></a>
## 复核LEARN中的真实TFIDF记录

LEARN中的真实短信数字来自单独提供的参考配置；默认起点仍是人工特征。在学生仓库根目录执行：

```sh
python3 lesson-11/analysis.py --config lesson-11/tfidf-reference.json --output lesson-11/artifacts/tfidf-reference
```

使用新输出目录。下面从JSON读取完整精度复算；若改了目录，请同步修改路径：

```python
import json, math
from pathlib import Path

t = json.loads(Path("lesson-11/artifacts/tfidf-reference/prediction_trace.json").read_text())
z = math.fsum(item["value"] * item["weight"] for item in t["features"]) + t["intercept"]
p = 1 / (1 + math.exp(-z))
assert math.isclose(z, t["logit"], abs_tol=1e-12)
assert math.isclose(p, t["probability"], abs_tol=1e-12)
print(t["id"], z, p, t["action"])
```

表格使用约数，复算使用JSON中的完整精度，并允许浮点舍入误差。

## 直接调用小工具

从学生仓库根目录启动Python，可以导入：

```python
from mlcourse.text_representations import fit_representation, transform, explain_text

# 用三段人工文本练习转换。
training = ["green tea", "green tea tea", "red coffee"]
rep = fit_representation(training, kind="tfidf", min_df=1, max_features=10)
matrix = transform(["green coffee", "gold"], rep)
detail = explain_text("green coffee", rep)
```

`rep['names']`给坐标顺序，`detail['features']`给已出现词的count、df、idf、weighted_value和归一化后的value；`unknown_tokens`记录没进词表的词。`row_norm`是除法之前的加权行长度。真实短信在同样规则下处理，IDF不会因这次新输入而重新拟合。

词表示使用稀疏存储，`matrix.row(i)`返回非零坐标与值；`matvec(w)`计算所有行与系数的内积。无需把数千维向量全抄到报告里。`to_dense()`只供小例检查，有单元格预算，不应对整个训练矩阵调用。

## 怎样核对词表示的真实追踪

本节用于BoW或TF–IDF。在`prediction_trace.json`中按原文找到tokens；对一个词核对出现次数。DF是含这个词的训练短信条数，本身是计数；同一条短信中的重复出现不会让DF增加多次。N是训练短信总条数，两者按给出的公式计算IDF。TF–IDF将count乘IDF，BoW保留count；若配置为L2归一化，再除以row_norm。`value × weight`是该坐标对logit的贡献；所有贡献加intercept后，再经sigmoid得到概率。

此处weight是分类器学到的系数，idf是表示阶段学到的统计量，两者不是同一个权重。相同分类器协议会在两份表示上分别训练。

## 比较时先列相同条件

保持train/dev ID及数据哈希、标签、逻辑模型目标、L2与截距约定、lr、steps、spam_weight、seed、initial_scale、threshold和capacity_fraction相同。表示的坐标、尺度和维数可以不同；同样400步比较的是共同固定预算，不是双方各自最优的上限。

用`records.csv`的ID对齐两份预测，不要按概率排序后把不同行相减。平均指标之外，挑你关心的失败类型检查记录证据。根据比较结果给出建议。

## 提交自己的比较程序

起点 `submission.json` 登记的是一次基线运行。若你的程序连续运行两份设置，将它登记为实际run，并把它每次生成的必要结果都列入artifacts；artifacts 只列程序生成的文件。原始运行目录要保留，自动复现另在临时副本进行。标签、评分和提交流程见[原流程](../docs/WORKFLOW.md)。


## 参考短信的完整坐标

对应 LEARN 中的 `sms-00004`。本次配置使用 train 3877条、dev 807条，`min_df=2`、`max_features=1200`、`words_numbers` 和L2归一化；逻辑回归运行400步、学习率1、L2系数0.001，阈值0.5，`capacity_fraction=1.0`。实际列序以 `representation.json` 的 `names` 为准。

|词|index|次数|训练DF|IDF|次数×IDF|归一化value|分类系数|贡献|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|already|90|1|62|5.11994011|5.11994011|0.29852608|-0.15021451|-0.04484295|
|c|189|1|64|5.08868757|5.08868757|0.29670386|0.20474299|0.06074803|
|dun|336|1|38|5.59951319|5.59951319|0.32648834|-0.11832412|-0.03863145|
|early|342|1|21|6.17203238|6.17203238|0.35986996|-0.07477203|-0.02690821|
|say|891|2|56|5.22002357|10.44004714|0.60872321|-0.13080820|-0.07962599|
|so|946|1|303|3.54604713|3.54604713|0.20675780|-0.40148660|-0.08301049|
|then|1011|1|156|4.20682903|4.20682903|0.24528572|-0.32210089|-0.07900675|
|u|1068|2|587|2.88634789|5.77269578|0.33658602|-0.33725664|-0.11351587|

IDF、value及贡献在表中四舍五入。完整输出的贡献和为 −0.40479366225056856，截距为 −2.0534728606082324，得分为 −2.4582665228588008，概率为 0.07883613213614646。本次 `action=0` 由概率低于阈值决定。

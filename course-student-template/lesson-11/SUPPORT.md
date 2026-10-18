# 按需要使用的计算支持

本页帮助读取一份结果、改一项表示设置和核对数字；自己的比较问题、第二套方案、诊断与结论由你完成。基本关系和完整小例见[LEARN](LEARN.md)。

## 先读已有输出

在学生仓库根目录运行`python3 lesson-11/analysis.py`，只产生一份人工特征起点，不自动比较或选赢家。输出目录已有文件时程序停止；重跑使用新的`--output`路径。

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

先看表示类型，再找相应字段。默认`manual`不建立词表，追踪中的每项特征使用`raw_value`（原始值）、`training_mean`（训练均值）、`training_scale`（训练标准差）和标准化后的`value`；按“原始值减训练均值，再除以训练标准差”核对。这里没有词次数`count`、DF或IDF，`unknown_tokens=[]`也不表示完整覆盖了所有词，只是该字段对人工特征不适用。

`bow`和`tfidf`才使用固定词表、count、DF、IDF及未知词记录。BoW记录IDF便于查训练统计，但不把它乘入词次数；TF–IDF才乘IDF。正式作品的词表示追踪从你选择的BoW或TF–IDF一方完成，不在默认人工特征输出里寻找这些字段。两类表示最后都核对`value × weight`的贡献和、截距、得分与概率。

## 用自己的配置运行一方

复制`lesson-11/config.json`到你自己命名的配置文件，只改计划研究的表示设置。例如选择`bow`或`tfidf`，以及自己有理由的`min_df`。使用新目录：

```bash
python3 lesson-11/analysis.py --config lesson-11/my-config.json --output lesson-11/artifacts/my-run
```

这个示例命令不会替你创建`my-config.json`。可以用编辑器复制和修改，也可以用自己的程序；提交时记录真正执行的命令。

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

这是核对一条输出的单方案示范，不替你选第二方案或完成正式研究。已有输出目录时改用新路径，保留旧证据。可从生成的JSON读取保存精度独立复算；若改了输出目录，下面路径也应相应修改：

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

打印的四舍五入值可能与完整精度最后一位不同。核对字段来源、公式和合理容差，不要求浮点末位相等。完整两方案比较和建议仍由你选择、构建。

## 直接调用小工具

从学生仓库根目录启动Python，可以导入：

```python
from mlcourse.text_representations import fit_representation, transform, explain_text

# 这里只是三条人工文本，用于验证计算，不是真实研究结果。
training = ["green tea", "green tea tea", "red coffee"]
rep = fit_representation(training, kind="tfidf", min_df=1, max_features=10)
matrix = transform(["green coffee", "gold"], rep)
detail = explain_text("green coffee", rep)
```

`rep['names']`给坐标顺序，`detail['features']`给已出现词的count、df、idf、weighted_value和归一化后的value；`unknown_tokens`记录没进词表的词。`row_norm`是除法之前的加权行长度。真实短信在同样规则下处理，IDF不会因这次新输入而重新拟合。

词表示使用稀疏存储，`matrix.row(i)`返回非零坐标与值；`matvec(w)`计算所有行与系数的内积。无需把数千维向量全抄到报告里。`to_dense()`只供小例检查，有单元格预算，不应对整个训练矩阵调用。

## 怎样核对词表示的真实追踪

本节用于BoW或TF–IDF。在`prediction_trace.json`中按原文找到tokens；对一个词核对出现次数。DF是含这个词的训练短信条数，本身是计数；同一条短信中的重复出现不会让DF增加多次。N是训练短信总条数，两者按给出的公式计算IDF。TF–IDF将count乘IDF，BoW保留count；若配置为L2归一化，再除以row_norm。`value × weight`是该坐标对logit的贡献；所有贡献加intercept后，再经sigmoid得到概率。

此处weight是分类器学到的系数，idf是表示阶段学到的统计量，两者不是同一个权重。相同分类器协议会在两份表示上分别训练，不能把六维人工特征的系数直接拿去乘词向量。

## 比较时先列相同条件

保持train/dev ID及数据哈希、标签、逻辑模型目标、L2与截距约定、lr、steps、spam_weight、seed、initial_scale、threshold和capacity_fraction相同。表示的坐标、尺度和维数可以不同；同样400步比较的是共同固定预算，不是双方各自最优的上限。

用`records.csv`的ID对齐两份预测，不要按概率排序后把不同行相减。平均指标之外，挑你关心的失败类型检查记录证据。只保留原方案也可以，但要说明这次比较支持什么、还缺什么。

## 提交自己的比较程序

起点`submission.json`只登记一次基线，不能代表标准比较已经完成。若你的程序连续运行两份设置，将它登记为实际run，并把它每次生成的必要结果都列入artifacts；不要把手写输入列成需要程序重建的产物。原始运行目录要保留，自动复现另在临时副本进行。标签、评分和提交流程见[原流程](../docs/WORKFLOW.md)。

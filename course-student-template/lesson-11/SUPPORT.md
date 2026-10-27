# 第11课操作：从短信数据到两方案比较

所有命令在学生仓库根目录运行。沿用已有Python环境，需要NumPy；环境准备见[ENVIRONMENT](../ENVIRONMENT.md)。

## 1. 先读一条数据

打开 `data/sms/dev.csv`，找到 `sms-00004`：

- `text`：U dun say so early hor... U c already then say...
- `label`：ham，即正常短信。
- `id`：sms-00004，用来在不同结果文件中定位同一条短信。

其余列用于核对文本与划分，不是模型输入。完整字段见[数据说明](../data/sms/DATA.md)。train用于学习，dev用于比较；不要将两者合并后拟合词表。

## 2. 一次运行，完成两套方案

```sh
python3 scripts/course.py start 11
python3 lesson-11/compare.py
```

默认读取 `lesson-11/config.json`（人工特征）和 `lesson-11/tfidf-reference.json`（TF–IDF），各自训练一份逻辑回归。结果在 `lesson-11/artifacts/comparison/`：

|文件或目录|先看什么|
|---|---|
|`comparison.csv`|两个方案各一行，比较整体结果|
|`paired_predictions.csv`|同一条短信的两套概率与复核决定|
|`first/`|人工特征的模型、转换和逐条结果|
|`second/`|TF–IDF的模型、转换和逐条结果|

`comparison.csv` 中，`reviewed` 是进入复核人数；`tp` 是找对的垃圾短信，`fp` 是误选的正常短信，`fn` 是漏掉的垃圾短信，`tn` 是正确放过的正常短信。`precision`、`recall` 用0至1保存，展示为百分数时乘100。

固定示范应得到：

|方案|TP|FP|FN|TN|查准率|召回率|
|---|---:|---:|---:|---:|---:|---:|
|manual|105|8|18|676|92.92%|85.37%|
|tfidf|12|0|111|684|100%|9.76%|

四类人数之和都是807。人工特征的查准率为105/(105+8)，召回率为105/(105+18)。TF–IDF虽然没有误选，却漏了111条垃圾短信，因此不能仅凭100%的查准率选择它。

## 3. 找到同一条短信发生了什么变化

打开 `paired_predictions.csv`：

|列|含义|
|---|---|
|`id`、`label`|短信编号、已有真实标签|
|`first_probability`、`second_probability`|两个方案预测为垃圾短信的概率|
|`first_action`、`second_action`|是否进入复核：1进入，0不进入|
|`changed`|两套复核决定不同为1，相同为0|

默认示范有101条记录的决定不同。找到 `sms-00020`，它的真实标签是spam，两套概率约为0.999599和0.304169，复核决定分别是1和0。再按id到 `data/sms/dev.csv` 查原文。

不要把两份文件分别按概率排序后逐行相减，那会把不同短信放在一起。比较程序已经按id配好记录。

## 4. 追踪一个词怎样影响预测

打开 `second/prediction_trace.json`。参考配置指定的是 `sms-00004`，这条正常短信中say出现两次。查看：

- `tokens`：分词结果；`unknown_tokens`：没有进入训练词表的词，本例为hor。
- `features`：非零坐标。每项含name、count、df、idf、value、weight和contribution。
- `intercept`：截距；`logit`：得分；`probability`：概率。

本例中，训练3877条短信有56条包含say，所以 $IDF=\ln(3878/57)+1\approx 5.220024$ 。词次数2乘IDF约10.440047，再除以整条短信的L2长度17.150729，得到 $value\approx 0.608723$ 。乘上分类系数 $weight\approx -0.130808$ ，贡献约−0.079626。

IDF来自词在训练文本中的出现情况；weight是分类器利用训练标签学到的系数。两者不是同一种权重。

下面的命令直接复算所有贡献，使用JSON的完整精度：

```sh
python3 - <<'PY'
import json, math
from pathlib import Path
p = Path('lesson-11/artifacts/comparison/second/prediction_trace.json')
t = json.loads(p.read_text(encoding='utf-8'))
z = math.fsum(x['value'] * x['weight'] for x in t['features']) + t['intercept']
prob = 1 / (1 + math.exp(-z))
assert math.isclose(z, t['logit'], abs_tol=1e-12)
assert math.isclose(prob, t['probability'], abs_tol=1e-12)
print(t['id'], z, prob, t['action'])
PY
```

应看到得分约−2.458267、概率约0.078836、action为0。表中的约数不能替代JSON完整精度。

人工特征的追踪在 `first/prediction_trace.json`。它显示原始值raw_value、训练均值training_mean、训练标准差training_scale和标准化值value，没有词表或IDF。正式任务的词坐标手算请选BoW或TF–IDF输出。

## 5. 换成自己的比较

可以沿用人工特征与TF–IDF，也可比较BoW与TF–IDF。先复制配置文件并修改 `representation`，取值为 `manual`、`bow` 或 `tfidf`。例如把一份配置保存为 `lesson-11/my-bow.json`，只把representation改为bow，其他设置保留，然后运行：

```sh
python3 lesson-11/compare.py --first-config lesson-11/my-bow.json --second-config lesson-11/tfidf-reference.json --output lesson-11/artifacts/my-comparison
```

先创建并检查配置，再执行命令。程序会核对训练和复核设置一致，并拒绝覆盖已存在的输出目录。

词表示常用设置如下：

|配置|含义|
|---|---|
|`min_df`|一个词至少出现在多少篇训练短信中，默认2|
|`max_features`|最多保留多少词，默认1200；先按DF降序选取，同DF按字母排序，最终坐标按字母排序|
|`token_pattern`|words_numbers保留英文词和数字串；words只保留英文词；都转小写|
|`normalization`|l2把每条非零文档向量除以自身长度；none不做这一步|
|`trace_id`|要追踪的真实dev编号；空值为第一条dev短信|

保持lr、steps、l2、spam_weight、seed、initial_scale、threshold和capacity_fraction相同。相同步数比较的是固定预算下的表现，不代表两种表示都达到各自最优；这里不要求把结果调整到“新方法更好”。

只想单独运行一个方案时，仍可使用原工具：

```sh
python3 lesson-11/analysis.py --config lesson-11/my-bow.json --output lesson-11/artifacts/bow-only
```

## 6. 手算题怎样用程序核对

下面只用三条人工文本，不读取真实短信或训练分类器：

```sh
python3 - <<'PY'
from mlcourse.text_representations import fit_representation, transform
training = ['small box', 'big box', 'small bag']
new_texts = ['big bag bag unknown', 'big box', 'box big', '', 'unknown']
for kind in ['bow', 'tfidf']:
    rep = fit_representation(training, kind=kind, min_df=1, max_features=4)
    print(kind, '词表=', rep['names'], 'DF=', rep['df'])
    for text, row in zip(new_texts, transform(new_texts, rep).to_dense()):
        print(repr(text), row)
PY
```

词表应是bag、big、box、small，DF依次为1、1、2、2。第一条新文本只留下bag两次和big一次，二者IDF相同，所以两种表示归一化后恰好都是[0.894427, 0.447214, 0, 0]。big box包含不同DF的两个词，会展示不同的相对权重。空文本与只有unknown的文本都得到零向量。

这里只对小例调用to_dense；真实词矩阵采用稀疏存储，不需要展开成数千列手抄。

## 7. 填写报告并提交

用 `report.md` 填结果、手算和建议。默认 `submission.json` 已登记两方案比较的18个输出文件，不包含报告本身。默认复现命令是 `python3 lesson-11/compare.py`。

如果用了自己的配置和输出目录，把 `run` 改为实际命令的参数列表；`artifacts` 中的目录也要对应修改。可用下面的命令列出自己的输出文件，把my-comparison改成实际目录：

```sh
python3 - <<'PY'
from pathlib import Path
import json
p = Path('lesson-11/artifacts/my-comparison')
print(json.dumps(sorted(str(x) for x in p.rglob('*') if x.is_file()), ensure_ascii=False, indent=2))
PY
```

配置是你保存的输入，不列入生成产物清单；first、second目录中的config.json是程序保存的实际配置，属于输出。完成分析后才把status改成complete，运行：

```sh
python3 scripts/course.py check 11
```

标签检查会在临时副本删去登记的输出并按run重建，比较文件内容，不删除原作业。最终标签及提交步骤见[WORKFLOW](../docs/WORKFLOW.md)。

## 其他输出按需查阅

每个方案目录中还有representation.json（表示参数）、records.csv（逐条预测）、summary.json（指标）、model.npz（系数）、curve.csv（训练过程）和first_update.json（首次更新）。先完成比较与解释，再按需要查看；不必把每个文件都抄进报告。

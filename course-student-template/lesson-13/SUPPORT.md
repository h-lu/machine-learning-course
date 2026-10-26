# 第13课｜运行帮助

以下命令均在学生仓库根目录执行。

## 运行前准备

先使用前几课已配置的Python环境。默认实验读取 `data/sms/cache/` 中的短信向量，只训练分类头；运行新英文或句子相似度示例时，才调用 `data/sms/encoder/` 中的本地编码器。

首次编码新文本前安装额外依赖：

```sh
python3 -m pip install -r data/sms/requirements-encoder.txt
```

模型权重、分词器与配置已随学生仓库提供。安装好Python依赖后，以下实验无需访问模型网站。旧仓库先按[更新说明](../docs/LESSONS13_14_UPDATE.md)补齐课程文件。

## 训练一个方案

```sh
python3 lesson-13/analysis.py
```

默认结果保存在 `lesson-13/artifacts/baseline/`。复制 `config.json` 为 `my-config.json`，修改后运行：

```sh
python3 lesson-13/analysis.py --config lesson-13/my-config.json --output lesson-13/artifacts/my-run
```

每次新实验使用新的输出目录。`representation` 可选manual、bow、tfidf或pretrained；pretrained使用固定表示，配置中只调整分类器训练和复核规则。

### 保存两个比较条件

先将 `lesson-13/config.json` 复制为 `lesson-13/pretrained-config.json`，保留其表示为pretrained。另建 `lesson-13/self-config.json`；下面以TF–IDF为例，也可以根据自己的第11课方案选择manual或bow：

```json
{
  "representation": "tfidf",
  "lr": 1.0,
  "steps": 400,
  "l2": 0.001,
  "spam_weight": 1.0,
  "seed": 0,
  "initial_scale": 0.0,
  "threshold": 0.5,
  "capacity_fraction": 1.0,
  "trace_id": null,
  "min_df": 2,
  "max_features": 1200,
  "token_pattern": "words_numbers",
  "normalization": "l2"
}
```

`lr`和`steps`控制分类头训练，`l2`控制正则，`threshold`与`capacity_fraction`控制复核。两份配置中这些共同设置保持一致，除非实验明确研究它们。`trace_id=null`追踪默认dev记录；也可填写同一个真实dev编号。

词袋和TF–IDF有自己的词表配置。不要将 `min_df`、`max_features` 等字段复制进pretrained配置，后者不重新建立词表，会报告未知设置。


## 输出文件

|文件|内容|
|---|---|
|config.json|本次实验设置|
|representation.json|表示方法与处理信息|
|model.npz|分类器系数|
|summary.json|dev评价指标|
|records.csv|逐条预测与行动|
|prediction_trace.json|一条记录的完整计算|
|first_update.json|第一次参数更新|
|curve.csv|训练过程|

先按以下顺序看文件：

1. `config.json` 与 `representation.json`：确认比较条件，而不是只看输出目录名字。
2. `summary.json`：找到 `metrics` 内的评价人数、TP/FP/FN/TN和指标；确认 `partition=dev`、`final_test_opened=false`。
3. `records.csv`：一行一条dev短信。按相同ID对齐两个方案，再比较概率与action，不凭行号猜同一条记录。
4. `prediction_trace.json`：先核对一个坐标的贡献，再合计全部贡献加截距，最后用逻辑函数重算概率。
5. `curve.csv`：一行是训练状态，不是一条短信；查看相同步数下两种表示是否仍明显变化。

TP为选对，FP为误选，FN为漏选，TN为正确放过：

$$
\mathrm{precision}=\frac{\mathrm{TP}}{\mathrm{TP}+\mathrm{FP}},
$$

$$
\mathrm{recall}=\frac{\mathrm{TP}}{\mathrm{TP}+\mathrm{FN}}.
$$

分母为零时指标未定义。action表示是否送去复核，不等于模型已证明短信是垃圾。向量的某个坐标也不直接对应一个可命名的词义。


## 处理新英文

```sh
python3 lesson-13/probe.py --system lesson-13/artifacts/baseline --text "Meeting moved to noon" --text "Meeting moved, please reply" --output lesson-13/artifacts/new-texts.json
```

输出包括原文、384维向量和分类概率。请根据自己的问题更换输入句子。该命令要求 `--system` 指向pretrained方案，不能把TF–IDF模型文件与384维向量混用。

输出中的 `ground_truth_labels` 为空：两条新英文没有经独立标注，不能据此计算准确率。探针也不输出容量限制后的action，因为容量依赖完整候选批次。分析时先报告改了什么、概率怎样变化，再说明这支持或不能支持哪种解释。

## 句子相似度小例

```sh
python3 lesson-13/meaning_example.py --output lesson-13/artifacts/meaning-example.json
```

此脚本编码讲义中的三个句子并计算相似度。预期第1、2句约为0.3480，第1、3句约为0.0827。

## 依赖与模型

编码依赖固定为 `onnxruntime==1.22.1` 和 `tokenizers==0.21.4`，见上述安装清单。

模型文件已随课程仓库提供，运行程序直接读取本地文件，不访问模型网站。模型介绍及需要补齐的文件统一从 **HF Mirror** 获取：

- [模型主页](https://hf-mirror.com/sentence-transformers/paraphrase-MiniLM-L3-v2)
- [本课固定版本文件目录](https://hf-mirror.com/sentence-transformers/paraphrase-MiniLM-L3-v2/tree/4ca70771034acceecb2e72475f72050fcdde4ddc)
- [量化ONNX文件](https://hf-mirror.com/sentence-transformers/paraphrase-MiniLM-L3-v2/resolve/4ca70771034acceecb2e72475f72050fcdde4ddc/onnx/model_quint8_avx2.onnx)
- [分词器文件](https://hf-mirror.com/sentence-transformers/paraphrase-MiniLM-L3-v2/resolve/4ca70771034acceecb2e72475f72050fcdde4ddc/tokenizer.json)

补齐文件时，在 `data/sms/encoder/` 下保持原目录结构。文件清单、SHA256及Apache-2.0许可见[模型清单](../data/sms/encoder/manifest.json)。程序启动编码器时会校验这些文件。

## 实现说明

本课使用量化ONNX模型在CPU上推理：分词并补齐长度，计算各词元向量，用位置标记（attention mask）排除补齐位置后求平均，再将句向量归一化为长度1。最大输入长度为128词元，输出为384维。

缓存同时记录文本ID、内容指纹、模型版本和向量文件校验值，用于检查数据对应关系。改变文本或模型后应重新生成相应向量。

## 可重复运行的比较脚本

前面的独立命令用于第一次观察结果，并保护已有目录。正式提交时，使用临时新目录计算，再把确定的产物复制到专用重建目录，可以连续运行而不删除历史实验。

先保存两份配置，并把自己的两条英文放在 `lesson-13/probe-texts.json`。文件结构示例：

```json
["Meeting moved to noon", "Meeting moved, please reply"]
```

以下保存为 `lesson-13/my-analysis.py`。示例仅提供重建骨架；英文、配置和实验解释仍由自己决定。

```python
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "lesson-13"
DEST = LESSON / "artifacts" / "rebuild"
CASES = {
    "self": "self-config.json",
    "pretrained": "pretrained-config.json",
}
FILES = (
    "config.json", "representation.json", "summary.json", "model.npz",
    "records.csv", "prediction_trace.json", "first_update.json", "curve.csv",
)
texts = json.loads((LESSON / "probe-texts.json").read_text(encoding="utf-8"))
if not isinstance(texts, list) or len(texts) != 2:
    raise ValueError("Provide exactly two probe texts")
if not all(isinstance(text, str) and text.strip() for text in texts):
    raise ValueError("Each probe must be a nonempty string")

with tempfile.TemporaryDirectory(prefix="lesson13-") as temporary:
    temp = Path(temporary)
    for name, config_name in CASES.items():
        fresh = temp / name
        subprocess.run(
            [sys.executable, str(LESSON / "analysis.py"),
             "--config", str(LESSON / config_name), "--output", str(fresh)],
            cwd=ROOT, check=True,
        )
        destination = DEST / name
        destination.mkdir(parents=True, exist_ok=True)
        for filename in FILES:
            shutil.copyfile(fresh / filename, destination / filename)

    probe = temp / "probes.json"
    command = [sys.executable, str(LESSON / "probe.py"),
               "--system", str(DEST / "pretrained")]
    for text in texts:
        command.extend(["--text", text])
    command.extend(["--output", str(probe)])
    subprocess.run(command, cwd=ROOT, check=True)
    shutil.copyfile(probe, DEST / "probes.json")
```

该脚本更新 `artifacts/rebuild/` 内两个方案和探针结果，不修改原始短信、缓存或模型权重。历史实验放在其他目录。新文本编码需要前述依赖；默认缓存实验成功，不代表新文本依赖已经安装。

连续运行两次：

```sh
python3 lesson-13/my-analysis.py
python3 lesson-13/my-analysis.py
```

两次应都成功；固定数据、配置、模型和环境时，提交检查会进一步核对产物内容。

## 提交检查

在 `submission.json` 中保留本课lesson与report字段，将run设置为：

```json
{"run": ["python3", "lesson-13/my-analysis.py"]}
```

这只是字段示例，不要用它覆盖整个提交文件。`artifacts`登记两个方案各8个文件，加上 `lesson-13/artifacts/rebuild/probes.json`，共17个产物。输入配置、报告、原始数据和预训练模型不是生成产物，不加入该清单。

可用以下代码列出示例脚本的17个路径，检查后填入artifacts：

```python
import json
names = [
    "config.json", "representation.json", "summary.json", "model.npz",
    "records.csv", "prediction_trace.json", "first_update.json", "curve.csv",
]
paths = [f"lesson-13/artifacts/rebuild/{case}/{name}"
         for case in ("self", "pretrained") for name in names]
paths.append("lesson-13/artifacts/rebuild/probes.json")
print(json.dumps(paths, ensure_ascii=False, indent=2))
```

报告与材料齐全后设置 `status=complete`，运行：

```sh
python3 scripts/course_l1314.py check 13
python3 scripts/course_l1314.py ci 13
```

`ci`在临时副本中重建登记产物，不读取最终留出作为开发评价。若自己的实验还生成了其他必要输出，也要登记并保证可重建。

## 常见问题

|现象|先检查什么|
|---|---|
|输出目录或probe文件已存在|新实验另取路径；重复重建使用临时目录脚本|
|Unknown pretrained setting|pretrained配置里是否误带词表参数|
|No module named onnxruntime/tokenizers|在运行脚本的同一Python环境安装编码依赖|
|Encoder changed或校验失败|核对模型清单与固定文件版本，不关闭校验或手改指纹|
|向量维数与系数不符|是否混用了词袋模型和预训练向量|
|缓存对应不上文本|核对ID、内容与模型身份，不手改缓存冒充新编码|
|探针没有准确率或action|它只有无标签概率；准确率需真值，容量行动需明确批次|
|CI输出不一致|检查配置、种子、模型和环境；不要手改概率或加入时间戳|

保留原始报错和命令，先解决具体依赖或路径问题，再补跑实验，不用伪造结果完成报告。

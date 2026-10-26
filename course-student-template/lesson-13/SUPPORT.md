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

每次实验使用新的输出目录。`representation` 可选manual、bow、tfidf或pretrained；pretrained使用固定表示，配置中只调整分类器训练和复核规则。

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

TP为选对，FP为误选，FN为漏选，TN为正确放过。precision=TP/(TP+FP)，recall=TP/(TP+FN)；分母为零时指标记为未定义。

## 处理新英文

```sh
python3 lesson-13/probe.py --system lesson-13/artifacts/baseline --text "Meeting moved to noon" --text "Meeting moved, please reply" --output lesson-13/artifacts/new-texts.json
```

输出包括原文、384维向量和分类概率。请根据自己的问题更换输入句子。

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

## 提交检查

将自己的实验命令写入脚本，在 `submission.json` 中用参数列表登记 `run`，并在 `artifacts` 中列出确定性输出文件。例如 `run` 为 `["python3", "lesson-13/my-analysis.py"]`。报告路径填入 `report`，完成后设置 `status=complete`。

```sh
python3 scripts/course_l1314.py check 13
python3 scripts/course_l1314.py ci 13
```

`ci` 会在临时副本中重建提交，检查所登记的产物。

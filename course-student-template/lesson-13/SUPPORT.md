# 第13课｜按需运行帮助

## 一个条件的起点
沿用原学生仓库、Python和NumPy环境，不新建第二个课程仓库：

```sh
python3 lesson-13/analysis.py
```

默认只有一个条件。复制config.json为my-config.json，按自己的问题改设置后：

```sh
python3 lesson-13/analysis.py --config lesson-13/my-config.json --output lesson-13/artifacts/my-run
```

不要用非空旧目录，防止覆盖证据。manual/bow/tfidf沿用第11、12课字段；pretrained只接受分类器训练与行动字段，不接受min_df/token_pattern等词表设置。

## 八个输出怎么看
config.json是实际设置；representation.json是输入转换；model.npz存系数；summary.json给dev指标；records.csv一行一条dev短信；prediction_trace.json追踪一条记录；first_update.json给第一次更新；curve.csv一行一步训练状态。

TP选对、FP误选、FN漏选、TN正确放过；precision=TP/(TP+FP)，recall=TP/(TP+FN)。分母为零时为未知，不伪装为完美。action是复核选择，不等于真实标签。

## 换成自建表示比较
复制本课配置，将representation改manual即可运行人工特征；若选bow/tfidf，可复用自己的第11课配置并按第12课训练约定核对。给两方相同数据和可解释的开发预算，记录曲线，不能只要求相同步数就声称完全公平。

## 真实处理新英文

```sh
python3 lesson-13/probe.py --system lesson-13/artifacts/baseline --text "Meeting moved to noon" --text "Meeting moved, please reply" --output lesson-13/artifacts/new-texts.json
```

文件含原文、384维向量和同一分类器的概率；两句示范概率约.091753/.067552，只用于核对流程。正式探针请按自己的研究问题设计。新文本没有真标签，不计算准确率。模型文件变动会报错，不能绕过哈希核对或使用随机数。

需要onnxruntime1.22.1与tokenizers0.21.4；教师按`data/sms/requirements-encoder.txt`课前准备。运行缓存分类本身不需要重新下载模型；新文本编码若依赖缺失，请先报告环境，不把查缓存说成编码成功。

## 提交前
把自己的全部开发比较命令写入一个脚本，run以命令参数列表指向它，artifacts列它生成的确定性文件；不要列运行耗时。设置status=complete，运行check/ci。ci在临时副本重建，不替你核对研究解释，也不应重复读取最终留出。

`submission.json`沿用原格式：lesson为`lesson-13`或`lesson-14`，report为报告相对路径，run为参数列表，例如 `["python3", "lesson-13/my-analysis.py"]`，不是一个shell字符串。

## 预训练背景小例：不用先训练分类器

```sh
python3 lesson-13/meaning_example.py --output lesson-13/artifacts/meaning-example.json
```

脚本只编码学习页的三句另设英文，输出384维向量与余弦相似度，不训练分类头、不接触train/dev标签，也不做垃圾短信准确率评价。预期第1与第2句约0.3480，第1与第3句约0.0827；细小浮点差异不等于含义发生改变。若未安装模型依赖，可先阅读已保存的小例数据理解，再请教师排查环境，不使用随机向量替代。

## 可选：模型文件到底怎样计算

ONNX是一种模型计算文件格式，本课使用已固定的量化CPU文件；量化是用较低精度存储/计算的工程选择，不是本课的学习目标。实际步骤为分词与补齐→模型计算各词元向量→排除补齐位置后求平均→向量除以自身长度，得到长度1的表示。attention mask就是标记哪些位置是真实输入、哪些是补齐的数组。归一化不是把每个坐标都改成0或1。

模型最多128词元、均值聚合和本课的长度归一化共同决定表示。量化实现可能与全精度结果略有差别，故比较时固定实现和版本。理解学习页之后，需要复核程序时再看这些细节。

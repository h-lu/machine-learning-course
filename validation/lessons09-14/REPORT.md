# 第09–14课本地交付与作者验收

本轮仅新增09–14与所需共享导航/检查资源；基线9fc28f58112e18ef3b62c0dab803a320382b0bdb。没有推送、合并、部署或GitHub Actions。1–8内容和15–32规划逐项字节/段落核验见protection.json；评分及历史题库也受保护。

## 课包入口

- [第09课学生任务](../../course-student-template/lesson-09/README.md) · [S07教师指导](../../course-instructor/lessons/S07/RUNBOOK.md)
- [第10课学生任务](../../course-student-template/lesson-10/README.md) · [S08教师指导](../../course-instructor/lessons/S08/RUNBOOK.md)
- [第11课学生任务](../../course-student-template/lesson-11/README.md) · [S09教师指导](../../course-instructor/lessons/S09/RUNBOOK.md)
- [第12课学生任务](../../course-student-template/lesson-12/README.md) · [S10教师指导](../../course-instructor/lessons/S10/RUNBOOK.md)
- [第13课学生任务](../../course-student-template/lesson-13/README.md) · [S11教师指导](../../course-instructor/lessons/S11/RUNBOOK.md)
- [第14课学生任务](../../course-student-template/lesson-14/README.md) · [S12教师指导](../../course-instructor/lessons/S12/RUNBOOK.md)

每课包括任务/LEARN完整例题/EXERCISES/HINTS/SUPPORT/最小入口/提交模板；教师有RUNBOOK、REFERENCE、作者走读边界与五对A/B题。新增60题与旧80题汇入新版本，旧八课条目逐对象一致。题目参与计分、六课最好五次、25/25/50不变。

## 真实数据与模型

UCI官方SMS ZIP 5,574条；归一化相同与字符三元组Jaccard≥0.85近重复连通分组后共4,985组，固定train/dev/finalholdout为3,877/807/890。实际规则是启发式，不能保证识别所有语义重复。不是时间划分，未按标签挑种子。来源、许可、ZIP与原文哈希见[数据说明](../../course-student-template/data/sms/DATA.md)。最终原文/标签/向量只在教师资源路径，公开数据封存是研究协议。

真实冻结编码器sentence-transformers/paraphrase-MiniLM-L3-v2，revision 4ca70771034acceecb2e72475f72050fcdde4ddc，Apache-2.0，384维，上游量化ONNX约17.5MB。保留模型卡、完整许可、分词器、模型字节与各文件SHA。缓存逐ID/原文SHA/编码器身份/生成参数验证，三分区分别保存。没有随机向量代替预训练。

## CPU实测（作者机器，非学生试教）

Python3.12、Linux x86_64，NumPy与ONNX均单线程。完整编码train/dev/final分别约6.8/1.7/1.4秒（encoding.json）；新4条含空文本和长文本实际编码结果见runtime.json。此运行既包含读取缓存的下游训练，也包含真实新输入编码，二者不混淆。

|实际入口/对照|秒|开发结果或Bike验证MAE|
|---|---:|---|
|lesson-9-default|0.228|{'training_mean': 197.82937894348797}|
|lesson-10-default|0.210|TP=105, FP=8, FN=18, TN=676|
|lesson-11-default|2.613|TP=12, FP=0, FN=111, TN=684|
|lesson-12-default|2.646|TP=12, FP=0, FN=111, TN=684|
|lesson-13-default|1.684|TP=83, FP=0, FN=40, TN=684|
|lesson-14-default|2.623|TP=12, FP=0, FN=111, TN=684|
|lesson-09-linear-vs-tree|0.245|{'linear': 146.48353463806205, 'shallow_tree': 128.11579744069076}|
|manual|0.156|TP=105, FP=8, FN=18, TN=676|
|manual-threshold|0.151|TP=107, FP=12, FN=16, TN=672|
|bow|2.616|TP=30, FP=0, FN=93, TN=684|
|tfidf|2.618|TP=12, FP=0, FN=111, TN=684|
|lr-small|0.154|TP=104, FP=8, FN=19, TN=676|
|lr200-reference|0.163|TP=96, FP=7, FN=27, TN=677|
|pretrained|1.565|TP=83, FP=0, FN=40, TN=684|
|tfidf-more-steps|5.142|TP=46, FP=0, FN=77, TN=684|
|tfidf-short-reference|0.706|TP=0, FP=0, FN=123, TN=684|

本次验证进程最高RSS约170.5MiB；新编码器加载0.048秒，新4条编码0.015秒。这是作者机器的命令时间，不等于90分钟课堂已通过真人试教，也不保证所有CPU速度相同。Python3.10+核心接口兼容设计；实际新环境验证为Python3.12，其他系统尤其非AVX2需教师课前实跑。

## 结果怎样解释

固定400步/学习率1.0/相同L2与阈值的比较检查固定计算预算下可用性，不代表各表示分别调优后的上限。人工特征在本任务中很强；预训练不要求胜出。早先100步小步长参考在阈值0.5下没有复核样本，是训练不足与阈值共同作用的诊断起点，不能据此宣布词袋无用。第12课只选学习率或停止时机一种比较；大步长200的参考有真实目标上升/震荡，但学生不必复制该现象。

[真实训练曲线](../../course-instructor/resources/sms/figures/training-curves.png)分别画含正则训练目标、未加权训练BCE和开发BCE；数值CSV与一次更新/预测追踪在教师resources/sms/reference。所有这些分数来自开发集，最终留出成绩不写入学习材料。

## 检查证据与边界

运行脚本tools/validate_lessons09_14.py核验六课入口、两模型Bike记录级MAE、短信混淆计数、系数贡献、一次更新与独立有限差分；核查空输入、OOV、Unicode、NaN/非法设置、零容量、并列排序、极端logit、随机种子重复性、缓存ID与文本身份、训练/开发处理分离、重复分组跨集合。

最终评价入口用事先指定的manual系统做教师协议冒烟测试，不用最终分数调整任何设置，未将最终分数公开到报告；验证改动定案配置与重复覆盖会被拒绝。此说明不能表述为“作者从未运行最终集”。学生自己的首次最终评价仍须在第14课开发定案后进行，已见最终数据者另寻独立评价。

数值核验使用独立标量公式与有限差分；没有额外独立评审者或真人学生试教。正式课堂可用性尚需教师试教确认。发布与服务部署由后续父任务处理，本地交付不修改线上场次/账号/成绩。

## 最终检查汇总

- 学生、教师、32课规划的严格结构检查均无问题。
- 旧学生实验38项单元测试通过；旧01–08整套作者入口/过程参考回归通过（historical-regression.json）。
- 386个原跟踪文件逐字节保持不变；地图中01–08与15–32共26个课次段落保持字节一致。共享文件只有必要导航、活跃范围、题库版本与验证路由变化。
- 旧题库8课80题对象完整保留；新增6课60题使用新content_version。评分文件、GitHub工作流保持原哈希。
- 7种缓存身份变造被拒绝，原缓存仍可读取；见cache-mutations.json。
- 原公开工作树与旧redesign脏工作树未写入；复制进来的两份原验证文件未修改、未纳入本次提交。
- 第14课真实开发诊断见教师S12/REFERENCE：短spam组仅2条，延长训练未改善固定阈值召回；报告保留失败与小分母限制，不强行制造成功。

尚未完成：真人90分钟试教、其他平台CPU兼容实测、父任务负责的推送/发布/部署。没有为此扩大第15–32课或改变已授课要求。

六课默认submission/run完整输出在一次性副本中通过逐字节重现，见submission-reproduction.json；耗时留在控制台和作者计时报告，不混入要求字节一致的科学结果。

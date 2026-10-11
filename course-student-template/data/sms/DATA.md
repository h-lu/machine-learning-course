# 短信资源与固定划分（第10课前准备）

默认研究路线使用真实 UCI SMS Spam Collection，Almeida、Hidalgo，2011，DOI [10.24432/C5CC84](https://doi.org/10.24432/C5CC84)。[官方页面](https://archive.ics.uci.edu/dataset/228/sms+spam+collection)于2026-10-11核对，标注CC BY 4.0；[许可](https://creativecommons.org/licenses/by/4.0/)。修改包括新增ID、分组、划分与计算表示，原文与标签不改写。原ZIP与readme保存在教师资源目录，旧readme的研究用途/免责声明也保留，不将原作者背书或部署保证附加于此。

实际逐行解析5,574条，ham 4,827、spam 747；不是常见清理版的5,572条。原始文件SHA256：`7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d`。ZIP SHA256：`1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3`。每行是一条历史英语短信，不是一个独立发送者或一个时间段。公开文本含联系方式；不要拨打、点击或作为操作对象，不导入私人短信。

## 分组在划分之前

按NFKC、英文小写、URL与数字归一化，先合并完全相同的归一化文本，再对长度≥12字符的文本以字符三元组Jaccard≥0.85连接近重复；取传递闭包。一组即使连接链较长也整体分配。方法不读标签。短文本采用归一化相同规则，防止大量无关短句误连。完整程序是仓库根tools/prepare_sms.py，教师保存全部连接边，实际4,985组、624条合并边。

用固定种子20261011与组内容哈希进行70/15/15分配，不按行号切分，不宣称时间外推，不根据结果挑种子。实际train=3,877、dev=807、finalholdout=890。train.csv/dev.csv只包含对应原文、标签、ID、组ID与原文哈希；split_manifest.csv列出全体ID/组/分区而不含文本标签。最终原文/标签与对应缓存在教师目录单独保存。

近重复是可审计的启发式规则，不等于识别所有语义近重复或发送者身份。它也可能把数字不同但意义重要的文本合在同组，这减少跨组泄漏而不把它们从数据删除。该限制必须保留。公开原始文件可另行下载，封存是研究协议，不能夸称技术上不可绕过。

## 各课可用信息

10–13只读train/dev。词表、IDF（逆文档频率）、均值/标准差、逻辑模型参数从train拟合；dev选择表示、阈值、容量、停止点和错误子集。不能让dev参与拟合IDF，也不能让finalholdout决定任何这些选择。14在开发结果上定案后才第一次最终评价；后续修改需要新的独立数据。

[英文阅读支架](READING.md)提供缩写释义，**不改变模型原文**。如比较译文，另存输入与翻译来源，作为明确的表示实验，不能混入原文缓存。

## 冻结编码器

[官方模型卡](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2)标注Apache-2.0与384维；本包保留原README和标准许可全文。revision为`4ca70771034acceecb2e72475f72050fcdde4ddc`，实际文件`onnx/model_quint8_avx2.onnx`约17.5 MB，量化权重、分词器、最大长度128、mask均值池化后L2归一化全部纳入manifest。模型每个文件都有SHA256。

train/dev缓存分别有ID顺序、原文哈希、模型manifest哈希、生成参数与向量哈希；不拟合短信标签。缓存加下游训练仅需NumPy；实际编码新英文文本需要课前安装[CPU依赖](requirements-encoder.txt)，本次验收为Python3.12、Linux x86_64/AVX2、单CPU线程，其他系统开课前另验。常规训练代码要求Python3.10+。离线入口不访问网络或付费API。没有编码器时应补齐教师资源，不能用随机向量或虚构结果补位。

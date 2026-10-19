# 本课短信数据：先读这三列

每行是一条历史英语短信，课程将它用于垃圾短信识别。第11课沿用第10课的数据，不需要另找数据或导入个人短信。

|列|含义|例子|
|---|---|---|
|id|短信编号，用来连接原文与两套预测|sms-00004|
|text|英文原文，模型从这列提取特征|U dun say so early hor... U c already then say...|
|label|已有分类标签；ham为正常短信，spam为垃圾短信|这条记录是ham|

- `train.csv`：3877条（3365条ham、512条spam）。词表、IDF、人工特征的均值与标准差，以及分类器，都只用这份数据学习。
- `dev.csv`：807条（684条ham、123条spam）。用来比较方案；模型预测只读取原文，标签用于核对预测。
- `split_manifest.csv`：划分记录，不是另一份训练数据；不含原文和标签。最终留出文本和标签不在学生包中。

`text_sha256` 用来核对原文是否变化，`group_id` 记录相同或近重复文本的分组，`split` 标明train或dev。这些是核对用字段，不加入特征。数据按分组划分，以免相同或近重复文本跨训练与开发集。

输出 `records.csv` 只有编号、标签与预测等字段；要阅读短信原文，用id回到dev.csv。原文始终用英文，中文解释只帮助阅读，不替代模型输入。

下面保留数据来源、许可及文件校验资料，分析时按需查阅。

## 来源与校验记录

Source: UCI SMS Spam Collection, Almeida and Hidalgo (2011), DOI 10.24432/C5CC84.
Upstream catalog URL: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
License record: CC BY 4.0 (UCI catalog), checked in the historical source record dated 2026-10-11.

## Files present in this student package

`train.csv`, `dev.csv`, `split_manifest.csv`, `provenance.json`, `DATA.md`.

|File|Rows|Groups|Columns|
|---|---:|---:|---|
|train.csv|3877|3501|id, label, text, text_sha256, group_id, split|
|dev.csv|807|711|id, label, text, text_sha256, group_id, split|
|split_manifest.csv|5574|4985|id, text_sha256, group_id, split|

Train label counts: ham 3365, spam 512. Dev label counts: ham 684, spam 123.
The split manifest contains ID, original text hash, group ID, and split metadata only; it contains neither text nor labels. It includes 890 historical finalholdout IDs.
Train and dev share no group IDs, record IDs, or original-text hashes.

## Current data SHA-256

- `train.csv`: `3d4c268e8bba99a5dd4bcd806b084d322ad0fb3f404db041109cc1f7d18b26fb`
- `dev.csv`: `21602715697e834fc1e69ea9eeb7ae2c280fb2a06833848f48940626e02ac5c6`
- `split_manifest.csv`: `686ee5e28cc33d749f25ca1d170e550b700f80629b2c262986751a0a11b9cd0d`

## Historical source records

Historical source commit: `912ade66c5449bfd740277bc761de7b9b54154fd`.
The nested `historical_source` object in `provenance.json` records original source totals, grouping, and hashes. Those records do not imply that referenced files are included here.
No upstream full corpus, source ZIP, finalholdout text or labels, encoder, or embedding cache is included in this student package.

The original English readme is retained byte-for-byte in the course repository teacher resource path `course-instructor/lessons/S08/resources/original-sms-readme.txt`, outside this student package. It contains labelled examples that match historical finalholdout texts. Its SHA-256 is `8753cd2d3cab68f80c8257851b8c2037778c267f55accb6fd1b5a2e32d36a84e`.

## Runtime metadata

The local lesson-10 baseline uses the fixed manual representation and NumPy. Its loader checks the current `file_sha256` keys for train/dev. It accepts only train and dev partitions.
Grouping recorded by the historical source: normalization and exact/near-duplicate grouping before group-level splitting, seed 20261011. No chronological order or sender identity is supplied.

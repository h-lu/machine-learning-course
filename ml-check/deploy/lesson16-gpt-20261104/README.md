# 第16课：GPT表示与生成

对应[新版第16课教材](https://hblu.top/ml/lessons/16/index.html)，内部课次为S14。五对A/B题覆盖查表与位置、初始向量与上下文、因果预测、参数学习、温度与采样；计算只用小向量逐项相加。完整题目、答案与干扰项解释见[教师审阅稿](REVIEW.md)。

`source/s14.json`为本课源题，`lessons.json`为从已发布32课题库生成的新快照。版本为`ml-lesson16-gpt-20261104-v1`，其余31课沿用已发布内容。A/B题号与阶段时长保持稳定，新建场次使用新版，已有场次继续读取各自快照。

依据教材已经核对的[GPT原论文§3.1](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)和[3Blue1Brown的Embedding、Beyond words与Softmax温度说明](https://www.3blue1brown.com/lessons/gpt/)。本轮为作者自查：两组向量加法对应同一机制；B版换词元或情境；因果题分别给出可见范围与预测目标；学习提示另举例子，答案解释逐项覆盖干扰项。

生成、测试和镜像制作在hblu-5090执行，发布记录见`deployment-receipt.json`。

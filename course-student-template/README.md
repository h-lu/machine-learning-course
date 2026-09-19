# 机器学习项目课：从问题到可检查的作品

**本分支材料状态：C01–C02 与 S01–S06 已成套改写为候选课包；S07 保留原线性回归实验，增加分层阅读支持并修订概念题，S08–S30 仍为原已发布内容。**候选课包是否用于课堂，由教师按班级指定版本；本次不自动切换在线题库。第一次学习时直接进入下面的第 01 课；文件操作查 [第一次运行指南](docs/FIRST_RUN.md)，新词按需查 [术语表](docs/TERMINOLOGY.md)，不必先背词表。

本学期你将完成 32 次课堂项目：把一个实际问题写成任务说明，准备数据，比较模型或规则，检查失败案例，并根据结果决定继续试用、修改还是停止使用。你可以全程使用 AI 编程、计算、分析和写作；提交时要说明选择、证据和适用场景与限制。

每节课先阅读对应目录的 `README.md`，了解使用者、数据、行动和限制，再阅读 `LEARN.md` 中的通俗解释和最小例子。概念检查按教师指定课包和场次进行：C01–C02、S01–S06 当前候选包留出约 15 分钟；现行 S07 的 A、学习、B 三阶段共 35 分钟，其他未改写课次以教师说明为准。使用 [ml-check](https://hblu.top/ml-check/) 时不要混用新旧题库。项目允许有依据的不同方法和结论，不按代码量、模型数量或网页外观评分。

## 第一次使用

按[操作与提交步骤](docs/WORKFLOW.md)使用此模板创建个人私有仓库，检查 Python 与 Git；依赖安装和目录核对见 [第一次运行指南](docs/FIRST_RUN.md)。课程已经提供小型离线数据和可以运行的示例代码；请在此基础上修改程序，完成当课的机器学习任务。

```bash
python scripts/course.py start 01
python scripts/course.py run 01
```

若你的电脑使用 `python3`，把命令中的 `python` 换成 `python3`。必做实验只需要普通 CPU、Python 3.10 或以上和仓库内的数据；运行限制见[实验接口](docs/RUNTIME.md)。

S01–S06 的先后关系、数据版本和提交方法见 [问题与评价模块](docs/FOUNDATIONS.md)。S01–S07 每课首屏都提供入门支持入口，直接跟着操作即可，不必先完成提高和拓展。

## 本学期项目

| 周 | 课次与机器学习任务 |
|---|---|
| 1 | [01 怎样把一个想法变成可运行的作品](lesson-01/README.md) · [02 一个结果能说明方案有用吗](lesson-02/README.md) |
| 2 | [03 怎样把模糊需求变成可研究的问题](lesson-03/README.md) · [04 这份数据和标签代表谁、代表什么](lesson-04/README.md) |
| 3 | [05 怎样比较才接近未来使用](lesson-05/README.md) · [06 什么算做好了，失败会造成什么后果](lesson-06/README.md) |
| 4 | [07 还缺哪些数据，哪些记录值得补](lesson-07/README.md) · [08 一次小实验能否改变最初的问题](lesson-08/README.md) |
| 5 | [09 直线能支持哪一种预测](lesson-09/README.md) · [10 风险概率应该怎样使用](lesson-10/README.md) |
| 6 | [11 一棵树能否成为可执行的规则](lesson-11/README.md) · [12 多一点性能值得多大成本](lesson-12/README.md) |
| 7 | [13 分成几组之后，准备怎样做](lesson-13/README.md) · [14 没有故障标签，先检查哪些记录](lesson-14/README.md) |
| 8 | [15 这次任务需要神经网络吗](lesson-15/README.md) · [16 训练没有变好，应该先改什么](lesson-16/README.md) |
| 9 | [17 图像换个样子，还能认出来吗](lesson-17/README.md) · [18 借来的表示，适合我的数据吗](lesson-18/README.md) |
| 10 | [19 一段话中，该看哪些信息](lesson-19/README.md) · [20 微型 Transformer 怎样猜下一个词元](lesson-20/README.md) |
| 11 | [21 一句话怎样变成词元和概率](lesson-21/README.md) · [22 同一个模型，怎样选择输出](lesson-22/README.md) |
| 12 | [23 提示改好了，还是只记住了例子](lesson-23/README.md) · [24 数据很多，怎样找到有用的一段](lesson-24/README.md) |
| 13 | [25 有了引用，回答就可信吗](lesson-25/README.md) · [26 哪些请求可以交给语言模型](lesson-26/README.md) |
| 14 | [27 先试一试，还是继续选最好的一项](lesson-27/README.md) · [28 怎样把连续决策写成一个环境](lesson-28/README.md) |
| 15 | [29 知道规则后，怎样规划下一步](lesson-29/README.md) · [30 不知道转移规律，怎样从尝试中学习](lesson-30/README.md) |
| 16 | [31 模型运行后，什么时候需要处理](lesson-31/README.md) · [32 换一个场景，原来的方案还能用吗](lesson-32/README.md) |

## 每课需要提交什么

每课提交一份能重新生成主要结果的程序、程序产生的结果，以及说明选择和结论的报告。默认在 `report.md` 写报告，在 `artifacts/` 保存 CSV、JSON 或图表；在 `submission.json` 填写报告路径、结果文件和运行命令，并将 `status` 设为 `complete`。

必做任务（Core）至少要完成四件事：明确任务和评价指标；运行可复现的基线或最小模型；设计一条容易出错的输入或条件变化；根据检查结果修改原来的决定，并说明理由。只运行示例程序、列出文件或复制 AI 生成的结论，都不算完成项目。

请阅读[成果与评分](docs/ASSESSMENT.md)、[AI 使用建议](docs/AI_USAGE.md)、[知识检查说明](docs/KNOWLEDGE_CHECK.md)和[操作与提交步骤](docs/WORKFLOW.md)。遇到安装或运行问题，先看[故障处理](docs/TROUBLESHOOTING.md)。仓库内数据是合成或微型样例，不能直接当作真实机构或用户的事实。

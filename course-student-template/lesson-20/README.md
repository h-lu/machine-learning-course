# 第 20 课（S18）：没有唯一答案时，怎样判断真的变好了

## 本课要解决什么问题

课程问答可以有不同措辞，不能只和一个标准句子做完全匹配。本课为离线问答助手建立分维度评价：任务是否完成、事实是否正确、是否有资料支持、格式是否符合要求。你还要处理两位评分者的分歧，并检查一个固定模拟评价器是否受 A/B 呈现顺序影响。

**先按 [入门支持](SUPPORT.md) 评价 development 案例**。数据中的两份人工评分和模拟评价器分数都是课程构造；它们用于练习评价流程，不测试真实 AI 评价能力。提交评分规则、一次手算、分歧处理、顺序比较、final 结果和六课连续作品的最终建议。若命令失败，保留报错、配置和已有开发结果，按 SUPPORT 先完成指定手算并标明“尚未运行”，修复后补跑；修复前不要打开 `data/final.json`。

## 本课要学会什么

- **评价维度（evaluation dimension）**：把任务完成、事实、资料支持和格式分开，避免一个总分掩盖失败原因。
- **评分量表（rubric）**：说明每个分数代表什么；本课 0、1、2 分分别是不满足、部分满足、满足。
- **评分者一致性（inter-rater agreement）**：两位评分者是否按相近标准判断；分歧需要回看资料与说明。
- **评价器偏差（evaluator bias）**：自动或人工评价可能受措辞、长度、顺序等无关因素影响。
- **开发评价与最终评价**：规则和权重在开发案例上调整，确定后再用于未参与修改的 final 案例。

## 90 分钟安排

0–15 分钟给四个维度写清 0/1/2；15–30 分钟运行 development 并手算一例；30–43 分钟检查三处分歧；43–55 分钟改变呈现顺序；55–67 分钟确定规则并运行 final；67–75 分钟形成六课建议；75–90 分钟概念检查和提交。

## 完成步骤

下面的命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。

1. 先读数据说明，在报告写每个维度为何需要单列，以及哪种错误不能被格式高分抵消。`weights` 总和必须为 1。
2. 运行开发评价：

```bash
python scripts/course.py start 20
python lesson-20/analysis.py --config lesson-20/config-start.json --output lesson-20/artifacts/order-ab
```

3. 在 `dimension_scores.csv` 找 `dev-01` 候选 A，手算 `2×0.3 + 1×0.3 + 0×0.3 + 2×0.1 = 1.1`。再打开 `disagreements.csv`，选择一项分歧回到 `data/base.json` 的资料和量表，写出需要澄清的问题；不能只说取平均即可。
4. `config-support.json` 只把固定模拟评价器的呈现顺序从 AB 改为 BA：

```bash
python lesson-20/analysis.py --config lesson-20/config-support.json --output lesson-20/artifacts/order-ba
```

人工分维度总分应不变，`fixed_proxy_score` 可能改变。这个差异是课程预设的模拟偏差，不是对真实 AI 能力的测试。
5. 从起点另存 `config-mine.json`，只调整四项权重并保持总和为 1。先说明用途为何需要这个取舍，再运行到 `artifacts/my-rubric`。比较至少一个候选胜负或差距是否改变。
6. 规则确定后把它复制到 `config-final.json`，将 `evaluation_split` 改为 `final`。不要提前打开 `data/final.json`；复制 final 提交清单，再由 `course.py run` 生成根目录最终结果：

```bash
cp lesson-20/submission-final.json lesson-20/submission.json
python scripts/course.py run 20
```

确认 `artifacts/summary.json` 使用 `final`，`dimension_scores.csv` 只有 4 个 `final-` 案例。若看过 final 后又改权重，必须改称开发证据或另找新案例。
7. 最终建议依次引用 S13–S18 的 `evidence.json`：能力来源、信息路径、提示、检索、适配路线和开放评价各支持什么。不要用本课总分代替前五课的机制与来源说明。

## 必须提交什么

提交采用的量表配置、程序、development 两种顺序和 final 的 `dimension_scores.csv`、`disagreements.csv`、`pairwise.csv`、`summary.json` 与 `evidence.json`。报告包括：四维度定义；一项加权手算；一项评分分歧及处理；顺序变化；个人权重理由；final 结论；六课作品建议及仍缺少的真实证据。

完成任务说明和报告后，确认 `submission.json` 已是 final 清单，把其中 `status` 从 `in_progress` 改为 `complete`，再运行：

```bash
python scripts/course.py check 20
```

## 不同起点怎么做

### 入门支持（Support）：使用现成评分表完成同一评价

[SUPPORT.md](SUPPORT.md) 点名一个计算和一个分歧，帮助开始；最终仍需写自己的权重理由。

### 必做任务（Core）：分维度评价并处理分歧

核对四个维度、两位评分者、顺序差异和 final，形成有资料依据的建议。

### 提高任务（Upgrade）：比较两套合理权重

设计“事实风险高”和“格式要求高”两种用途，分别给权重；说明哪些案例建议改变以及为什么。

### 换数据重测（Transfer）：评价新的开放回答

新增一题、资料和两个候选，请两位同学独立评分后再讨论；真人评分应另行记录，不能与课程模拟标注混写。

### 自选拓展（Open extension）：测量更多评价器偏差

在不改变事实内容时交换长度或措辞，先确定比较规则再观察；不把单次差异推广到所有评价器。

## 运行限制

标准库、8 个案例、16 个候选回答，普通 CPU 数秒内完成。所有评分与代理分数均为人工构造，不需要网络或大模型。模拟结果不能代替真人评分可靠性研究，也不能证明真实 AI 评价器能力。

# 第 17 课（S15）：提示改进了，还是只适配了见过的例子

## 本课要解决什么问题

上一课检查了输入信息路径。本课改变给离线课程问答助手的任务说明，也就是**提示（prompt）**。开发问题上的结果变好，可能只是提示碰巧适合这些已看问题。你要先写可检验的预计，在同样问题上重复比较两份提示，再把选好的提示用于没有参与修改的 final 问题。

**直接按 [入门支持](SUPPORT.md) 做第一轮**。程序是会读取新提示并重新产生输出的本地规则模板生成器，不是固定回答缓存，也不是真实大语言模型。它只识别“引用来源”“先写依据”“资料不足”和“结论”四个明确短语；真实语言模型能解释更多表达，本程序不能。提交原提示与新提示、程序实际识别的规则、重复结果、最终评价和限制；不能把模板表现写成真实模型能力。若开发命令失败，保留报错、配置和已有开发结果，按 SUPPORT 核对后补跑；修复前不要打开 `data/final.json`。

## 本课要学会什么

- **任务说明、示例与输出格式**：提示可以说明要做什么、给例子、规定回答结构；三者改变的作用不相同。
- **开发集（development set）**：允许反复查看并用于修改方案的问题。
- **最终评价集（final evaluation set）**：在提示和评分规则确定后才使用，避免根据答案倒改提示。
- **提示过拟合（prompt overfitting）**：提示只在参与修改的例子上变好，换问题后收益消失。
- **生成随机性**：同一输入可能产生不同措辞；重复运行估计波动，但不增加独立问题数量。

完成后应能说明每个比例的分母、开发与最终评价的用途，以及为何新提示必须产生匹配的新输出。详见 [LEARN.md](LEARN.md)。

## 90 分钟安排

0–15 分钟读问题和评价规则；15–27 分钟运行原提示；27–42 分钟比较新提示的三次输出；42–55 分钟查看失败问题并选定提示；55–67 分钟运行 final；67–75 分钟写连续证据；75–90 分钟概念检查和提交。

## 完成步骤

下面的命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。

1. 不打开 `data/final.json`，先在报告写：原提示可能在哪两类问题失败，新提示改变了哪条要求，什么结果会让你保留原提示。
2. 运行开发比较：

```bash
python scripts/course.py start 17
python lesson-17/analysis.py --config lesson-17/config-start.json --output lesson-17/artifacts/prompt-original
python lesson-17/analysis.py --config lesson-17/config-support.json --output lesson-17/artifacts/prompt-revised
```

3. 两个目录都先看 `prompt_features.json`，核对程序实际识别的规则；再看 `responses.csv` 和 `metrics.csv`。分母始终是 6 个开发问题；三次重复仍是同样 6 个问题。核对 `dev-04` 为什么原提示产生没有资料支持的说法，而新提示停止回答。
4. 从 `config-support.json` 另存 `config-mine.json`，只删除或加入“引用来源”“先写依据”“资料不足”或“结论”中的一个短语。程序会读取这段新文字并生成对应输出。运行到 `artifacts/my-check`，不能拿旧输出说明新提示有效。想尝试同义改写时，若 `prompt_features.json` 没有变化，只能说明这个模板未实现该表达，不能宣称提示本身无效。
5. 根据开发结果选定提示后，将同样的 `prompt_text` 写入 `config-final.json`，并保持 `evaluation_split` 为 `final`。此时才把最终提交清单复制为正式清单，由 `course.py run` 显式读取独立的 final 数据：

```bash
cp lesson-17/submission-final.json lesson-17/submission.json
python scripts/course.py run 17
```

6. 确认根目录 `artifacts/summary.json` 中的配置是 `final`，`responses.csv` 只有 4 个 `final-` 问题。报告引用 S13、S14 的 `evidence.json`：本课改变任务说明，没有更新参数，也没有检查真实内部注意力。说明 final 是否真的未参与修改；如果提前看过，就如实称为再次开发检查。

## 必须提交什么

提交三份提示配置、程序、原提示和新提示的 `prompt_features.json`、`responses.csv`、`metrics.csv`，最终评价结果及 `evidence.json`。报告至少写：提示假设；程序识别了哪条规则；每项比例的分子和分母；一条有资料问题和一条无资料问题；三次重复差异；个人提示改动；最终评价；模板实验不能支持的真实模型结论。

填写 `contract.json` 和报告后，确认 `submission.json` 是上一步复制的 final 清单，再把其中的 `status` 从 `in_progress` 改为 `complete` 并检查：

```bash
python scripts/course.py check 17
```

## 不同起点怎么做

### 入门支持（Support）：使用两份现成提示完成比较

[SUPPORT.md](SUPPORT.md) 给出完整命令、点名问题和比例核对。使用现成提示不降低完成标准。

### 必做任务（Core）：开发、重复与最终评价分开

比较两份提示，做一次个人单因素改写，并在方案确定后运行 final；不能只展示一条好回答。

### 提高任务（Upgrade）：检查评价规则依赖

在不改输出的前提下，分别比较“只看任务完成”和“同时要求来源”时的结论，说明规则为何应在 final 前确定。

### 换数据重测（Transfer）：加入新的课程问题

另存数据文件，添加一条有资料和一条无资料问题；程序必须对新输入重新生成，报告新资料来源。

### 自选拓展（Open extension）：连接离线小模型

可换成课前准备且能在 CPU 运行的小模型，但要记录模型、随机设置、实际生成时间和全部新输出，不以网络服务作为必做依赖。

## 运行限制

标准库、10 条人工问题，单次运行数秒。模板生成器只模拟提示条件和有限随机措辞，不代表大语言模型。final 在公开仓库可见，流程只能练习隔离方法；已经查看时必须说明限制。

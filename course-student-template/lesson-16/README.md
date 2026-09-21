# 第 16 课（S14）：输入怎样影响模型能够利用的信息

## 本课要解决什么问题

离线课程问答助手处理一句话时，某个位置能看到哪些词元，会影响它能计算出的表示。本课用四个词元和人工数值检查**因果遮罩（causal mask）**：改变较晚位置后，较早位置在有遮罩和无遮罩时分别会怎样变化。

**基础还不稳时，先打开 [入门支持](SUPPORT.md)**。你会运行一个能看到每个分数、权重和值的微型注意力实验，手算一个 softmax 权重，再只改未来位置的值。提交信息可见性比较、手算、个人对照和结论限度。若命令失败，先保留完整报错和配置，按 SUPPORT 手算指定的一行并标明“尚未运行”，修复后补跑；核对示例不能当作个人结果。这里没有真实词向量、没有训练参数，也没有真实大模型回答。

## 本课要学会什么

- **词元（token）**：模型处理文字时使用的片段；本例直接把中文词当作词元。
- **查询、键和值（query, key, value）**：查询和键产生匹配分数，注意力权重再对值作加权平均。
- **softmax**：把一组分数变成非负且总和为 1 的权重。
- **因果遮罩**：在预测当前位置时隐藏未来位置，防止未来内容提前进入计算。
- **预测概率与事实正确**：数值输出或较高概率只描述模型计算，不保证回答符合资料。

完成后应能从 `attention_weights.csv` 重算一个权重，并说明黑箱回答变化为什么不能单独证明内部遮罩。详细计算见 [LEARN.md](LEARN.md)。

## 90 分钟安排

0–18 分钟画出四个位置和可见范围；18–30 分钟运行起点；30–48 分钟重算一个权重与加权平均；48–60 分钟改变未来值；60–72 分钟联系 S13 的输入变化证据并写限制；72–90 分钟概念检查和提交。

## 完成步骤

下面的命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。

1. 先在报告写预计：位置 1 在因果遮罩下能看哪些位置；把位置 3 的值从 5 改为 8 后，两种条件的输出是否变化。
2. 从仓库根目录运行：

```bash
python scripts/course.py start 16
python lesson-16/analysis.py --config lesson-16/config-start.json --output lesson-16/artifacts/support-start
```

3. 在 `visibility.csv` 找 `sequence-01` 的两行。再到 `attention_weights.csv` 核对因果遮罩只保留位置 0、1；按 [LEARN.md](LEARN.md) 手算这两个位置的权重和输出。
4. `config-support.json` 只把位置 3 的新值改为 7，运行到另一个目录：

```bash
python lesson-16/analysis.py --config lesson-16/config-support.json --output lesson-16/artifacts/support-compare
```

5. 从起点另存 `config-mine.json`，只选择一个新的 `changed_future_value`。先预计变化方向，再运行到 `artifacts/my-check`。比较因果遮罩的变化是否仍为 0，以及无遮罩变化是否随新值改变。
6. 报告引用上一课的 `lesson-15/artifacts/evidence.json`：上一课中输入规则能改变分数但不更新参数；本课进一步说明输入能否到达某个位置取决于信息路径。两份证据都不能推出真实大模型在同一句话上的内部权重。

## 必须提交什么

提交配置、程序、`summary.json`、`visibility.csv`、`attention_weights.csv` 和 `evidence.json`。报告写出：目标位置与未来位置；一个分数、softmax 分母、权重和加权平均；有无遮罩的变化；个人对照；机制实验支持和不支持的结论。

完成 `contract.json` 和报告后，把 `submission.json` 标为 `complete`，运行：

```bash
python scripts/course.py run 16
python scripts/course.py check 16
```

## 不同起点怎么做

### 入门支持（Support）：跟着表格完成机制核对

使用 [SUPPORT.md](SUPPORT.md) 点名的行和完整算式，不需要实现注意力层。

### 必做任务（Core）：证明信息路径差异

所有人都要改变一个未来值，比较有无遮罩并重算至少一个权重，不能只截图输出。

### 提高任务（Upgrade）：同时改变键和值

复制数据，分别只改未来词元的 `key` 和只改 `value`，比较权重变化与加权内容变化。每次只改一个量。

### 换数据重测（Transfer）：换一段四词元序列

设置新的人工键和值，先列出目标位置可见范围，再运行相同检查。

### 自选拓展（Open extension）：加入二维向量

将标量查询、键和值扩展为二维小向量，保留可手算的一条记录并说明点积。

## 运行限制

只用 Python 标准库和两段四词元人工数据，普通 CPU 数秒内完成，不需要网络或模型下载。人工数值只验证注意力与遮罩机制；不能用来宣称真实语言理解、事实正确或所有 Transformer 都出现同样权重。

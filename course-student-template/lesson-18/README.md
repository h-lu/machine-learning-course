# 第 18 课（S16）：怎样补充资料，而不是期待模型猜对

## 本课要解决什么问题

提示写得清楚仍不能提供系统没有的课程事实。本课给离线问答助手加入三份本地资料，建立最小的**检索增强问答（retrieval-augmented question answering）**流程。你要分别判断：检索是否找到了正确资料，回答是否真的来自该资料，以及资料不足时是否停止。

**先打开 [入门支持](SUPPORT.md)**，不需要先会搜索引擎或大模型。程序根据实际查询词重新检索，再把本次找到的句子交给本地抽取器；修改查询或资料会产生匹配的新结果。提交两种阈值比较、一条检索成功但回答失败的案例、一个新查询和使用建议。若命令失败，保留报错、配置和已有开发结果，按 SUPPORT 核对路径和 JSON，修复后补跑；修复前不要打开 `data/final.json`。

## 本课要学会什么

- **文档切分（document chunking）**：把较长资料分成可检索的小段；过大或过小都会影响结果。
- **检索（retrieval）与相关性**：根据查询找候选资料；关键词重合是本课的简化相关性分数。
- **证据支持（evidence support）**：回答中的事实能在检索资料中找到，不只是附了一个来源编号。
- **检索失败与回答失败**：没找到正确资料属于检索问题；找对资料却选错句子属于回答步骤问题。
- **拒绝回答（abstention）**：资料不足时明确停止，比没有依据地猜测更符合本课用途。

## 90 分钟安排

0–15 分钟读三份资料与查询；15–28 分钟运行阈值 1；28–42 分钟核对检索分数和句子；42–55 分钟比较阈值 2；55–70 分钟添加个人查询并判断失败环节；70–75 分钟整理连续证据；75–90 分钟概念检查和提交。

## 完成步骤

下面的命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。

1. 报告先预计提高 `min_overlap` 会减少哪些错误，又会漏掉什么。说明最终答案必须来自本次实际检索结果。
2. 运行起点：

```bash
python scripts/course.py start 18
python lesson-18/analysis.py --config lesson-18/config-start.json --output lesson-18/artifacts/threshold-1
```

3. 先看 `retrieval.csv` 的检索词重合数和 `selected`，再看 `answers.csv`。`dev-03` 找到 D2，却抽取了不包含“三个阶段”的第一句；`checks.csv` 应把它列为回答步骤失败，而不是检索失败。
4. `config-support.json` 只把最小重合数从 1 改为 2：

```bash
python lesson-18/analysis.py --config lesson-18/config-support.json --output lesson-18/artifacts/threshold-2
```

比较 `dev-02`：更严格的阈值减少弱匹配，也会漏掉只有一个有效检索词的问题。不能只按总正确率选择而不说明用途。
5. 复制 `data/base.json` 为 `data/mine.json`，只在 development 增加一条查询，写清 `search_terms`、期望资料和答案要点。不要改程序输出。运行：

```bash
python -m json.tool lesson-18/data/mine.json
python lesson-18/analysis.py --data lesson-18/data/mine.json --config lesson-18/config-start.json --output lesson-18/artifacts/my-query
```

可以在文件管理器或编辑器中使用“复制／另存为”；`cp` 不是完成任务所必需的命令。

6. 方案确定后，把选定的 `min_overlap` 写入 `config-final.json`，保持 `evaluation_split` 为 `final`。不要提前打开 `data/final.json`；复制 final 提交清单后由 `course.py run` 生成根目录最终结果：

```bash
cp lesson-18/submission-final.json lesson-18/submission.json
python scripts/course.py run 18
```

确认 `artifacts/summary.json` 使用 `final`，`checks.csv` 只有 4 个 `final-` 查询。报告引用上一课的提示证据，说明本课补资料解决了哪类失败，又没有解决哪类回答选择问题。

## 必须提交什么

提交配置、个人查询数据、`summary.json`、`retrieval.csv`、`answers.csv`、`checks.csv` 和 `evidence.json`。报告要包含一个检索分数手算、阈值取舍、检索失败案例、回答失败案例、无法回答案例、新查询结果，以及资料和本地抽取器的能力限制。

完成任务说明和报告后，确认 `submission.json` 已是 final 清单，把其中 `status` 从 `in_progress` 改为 `complete`，再运行：

```bash
python scripts/course.py check 18
```

## 不同起点怎么做

### 入门支持（Support）：沿完整检索路径做同一任务

[SUPPORT.md](SUPPORT.md) 指出先看哪个文件、哪一行和怎样判别失败环节。

### 必做任务（Core）：分开检查检索和回答

比较两个阈值，核对一个成功、一个失败和一个资料不足问题，再添加一条自己的查询。

### 提高任务（Upgrade）：比较文档切分

把 D2 的两句合成一个单元与分开两个单元比较，保持查询不变，解释为什么检索正确仍可能抽取错句。

### 换数据重测（Transfer）：替换一份课程资料

保存新来源、更新对应查询和期望资料，不允许继续使用与旧资料不匹配的回答。

### 自选拓展（Open extension）：加入词形或同义词处理

为“晚交/逾期”等同义表达设计明确规则，比较前后检索，不把规则说成语义理解。

## 运行限制

标准库、3 份短资料、9 个问题，普通 CPU 数秒内完成，不需要网络和模型下载。关键词检索和逐字抽取用于检查流程，不代表真实大模型生成；资料只覆盖课程示例，不支持校园全部问题。

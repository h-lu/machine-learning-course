# S18 入门支持：先分项打分，再讨论总分


以下命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。
这是本模块最后一条必做路径。第一项小任务：不运行程序，先给 `dev-01` 候选 A 的四个维度各读一次分数，指出它“完成了问题但没有资料支持”，避免被流畅短句误导。

## 1. 运行开发评价

```bash
python scripts/course.py start 20
python lesson-20/analysis.py --config lesson-20/config-start.json --output lesson-20/artifacts/order-ab
```

打开 `dimension_scores.csv`。`dev-01,A` 的四项平均是 2、1、0、2，权重是 0.3、0.3、0.3、0.1。手算：

```text
2×0.3 + 1×0.3 + 0×0.3 + 2×0.1 = 1.1
```

程序中的 `weighted_total` 应为 1.1。单位是量表分，不是准确率或概率。

## 2. 不让平均数遮住分歧

打开 `disagreements.csv`，选择一行回到 `data/base.json`。例如 `dev-02,B` 的任务完成分别为 1 和 0；两位评分者都认为事实与支持是 0，但对“猜了一个楼层是否算部分回应”理解不同。你要提出量表澄清，例如“没有依据地给出地点，任务完成记 0”。不要只写平均 0.5。

## 3. 只交换呈现顺序

```bash
python lesson-20/analysis.py --config lesson-20/config-support.json --output lesson-20/artifacts/order-ba
```

两次人工分维度总分应相同，因为人工标注没变；`fixed_proxy_score` 会出现预设差异。记录一例差多少，并明确这是课程构造的模拟评价器，不是对真实 AI 的测试。

## 4. 选择自己的权重

另存 `config-mine.json`，只改四项权重，确保总和为 1。先写用途理由。例如课程事实风险高时，可提高 `factuality` 和 `evidence_support`，但不能为了让喜欢的候选胜出而倒改权重。

```bash
python -m json.tool lesson-20/config-mine.json
python lesson-20/analysis.py --config lesson-20/config-mine.json --output lesson-20/artifacts/my-rubric
```

至少核对一个案例的手算。若推荐没变，也可以是有意义的结果。

## 5. 确定规则后运行 final

把采用权重复制到 `config-final.json`，只把 `evaluation_split` 改为 `final`。在此之前不打开 `data/final.json`。然后复制 final 清单并运行：

```bash
cp lesson-20/submission-final.json lesson-20/submission.json
python scripts/course.py run 20
```

Windows PowerShell 不识别 `cp` 时，使用 `Copy-Item lesson-20/submission-final.json lesson-20/submission.json`，也可以在文件管理器中复制并覆盖。复制后，`course.py run` 会按 `submission.json` 显式读取 `data/final.json` 和 `config-final.json`。

final 有 4 个案例。先打开根目录的 `artifacts/summary.json`，确认配置是 `final`；再打开 `dimension_scores.csv`，确认只有 `final-01`–`final-04`。看过结果再改权重时，应把它降为开发材料，并说明需要新的最终案例。

## 6. 完成本模块证据链

报告按 S13 到 S18 各写一行：文件、验证对象、能支持的结论、不能支持的结论。最后给离线课程问答助手提出采用、修改或暂缓建议。完成 `contract.json` 和报告后，在复制过来的 `submission.json` 中把 `status` 从 `in_progress` 改为 `complete`，再运行：

```bash
python scripts/course.py check 20
```

无法运行时可先完成 `dev-01` 手算和一项分歧解释，标明未运行；修复后重跑上面的 `course.py run`，不把本页核对值当自己的新实验。`course.py ci` 会用同一条 final 命令重建结果。

# 第 32 课（S30）：怎样交付作品，并说明下一轮该学什么

## 本课要解决什么问题

本课整理前几课一直改进的服务台路由作品。这个作品读取一条文字请求，并把它送到查规则、查馆藏、算费用或人工处理中的一条路线。你要交付选定的方案、评价证据、可重跑命令、已知限制和下一项实验，让另一位同学能够复核你的结论。

本课有两个严格分开的阶段。默认的 `analysis.py`、`python scripts/course.py run 32` 和仓库自带的 `submission.json` **只读取 `data/base.json` 中的开发数据**。先用这些证据选定候选，写下指标和停止条件，再复制最终提交清单；只有最终清单中的命令会显式传入 `--final-data data/final.json`。如果默认开发运行在你尚未准备好时就显示最后评价，请停止并报告，因为那不是本课预期流程。

先从 [入门支持](SUPPORT.md) 开始。命令失败时保留报错和原有输出，再核对当前处于开发阶段还是最后评价阶段；旧输出不能代替本次运行。

## 本课要学会什么

| 标准术语 | 本课需要掌握的含义 |
|---|---|
| 开发数据（development data） | 用于比较、修改和选择方案的数据；看过后仍可继续调整。 |
| 最后评价（final evaluation） | 候选、指标和停止条件固定后才使用的一批新数据；看过后不能再把同一批数据当作未见评价。 |
| 可重现运行（reproducible run） | 使用保存的数据、配置和命令，可以重新生成相同的确定性结果。 |
| 文件摘要（checksum） | 根据文件内容计算的标识；它能发现文件改变，不能证明数据或结论正确。 |
| 下一项实验 | 能减少一个关键未知、并可能改变建议的具体比较。 |

完成后，你应能说明开发证据怎样支持候选选择，完成一次独立的最后评价，并让同伴重建相同结果。

## 90 分钟安排

| 时间 | 活动 |
|---|---|
| 0–18 分钟 | 运行开发评价，逐条核对两个方案 |
| 18–33 分钟 | 根据开发证据固定候选、指标和停止条件 |
| 33–48 分钟 | 显式切换到最后评价并手算结果 |
| 48–62 分钟 | 在新输出目录重跑，核对 manifest 和文件摘要 |
| 62–75 分钟 | 写继续、修改或停止的建议与下一项实验 |
| 75–90 分钟 | 完成 A 版概念检查、AI 学习、B 版检查并提交 |

## 完成步骤

1. 从仓库根目录开始，复制起点配置并登记本课：

   ```bash
   cp lesson-32/config-start.json lesson-32/config.json
   python scripts/course.py start 32
   python scripts/course.py run 32
   ```

   这时打印的命令不应包含 `--final-data`。成功后先打开 `lesson-32/artifacts/summary.json`，确认 `evaluation_stage` 是 `development`；再看 `records.csv` 中编号以 `T` 开头的开发请求。不要打开 `data/final.json`。

2. 在 `records.csv` 中分别手算原方案和适配方案的正确数，分母都是开发请求总数。选择至少一条两个方案路线不同的请求，写清输入中的哪个词改变了路线、参考路线是什么，以及这个变化是否支持适配。这里得到的是开发证据，可以用于选择方案。

3. 在 `campus_original` 和 `library_adapted` 中选择一个准备交付的候选，把名称写入 `config.json` 的 `release_candidate`。在 `report.md` 的第一部分写下：选择理由；最后评价使用“正确请求数/全部请求数”；涉及个人信息或预约的请求必须送人工；出现什么结果时你会停止自动使用。根据 README 第 2 步填写 `contract.json`，其中 `split_plan` 要明确“候选固定后只使用最后评价一次”。

4. 再运行一次开发阶段，确认输出中的 `selected_candidate_evaluation.scheme` 对应你的选择。固定后执行：

   ```bash
   cp lesson-32/config.json lesson-32/config-final.json
   cp lesson-32/submission-final.json lesson-32/submission.json
   python scripts/course.py run 32
   ```

   第二条命令把可重现命令明确切换到最后阶段；终端打印的命令必须包含 `--final-data lesson-32/data/final.json` 和 `--config lesson-32/config-final.json`。只有到这一步，程序才读取最后评价。

5. 打开新生成的 `summary.json`，确认 `evaluation_stage` 是 `final_evaluation`，并确认 `selected_candidate_evaluation` 对应你事先固定的候选。再打开 `records.csv`，对两个方案使用相同分母手算正确数，单独核对涉及个人信息或预约的请求，并追踪至少一条路线发生变化的请求。看过这批结果后，不要再调关键词并把同一批数据称为未见的最后评价。

6. 打开 `manifest.json`。核对开发数据、最后评价数据、固定配置和输出文件的 SHA-256 摘要。`run_command` 中的 `<OUTPUT_DIR>` 是占位符；把它替换为 `lesson-32/artifacts/replay`，按列表中的参数顺序重跑。两个目录中的 `summary.json`、`records.csv` 和 `manifest.json` 应逐字节一致。摘要一致只能说明文件内容一致，不能证明方案适合真实图书馆。

7. 完成 `report.md`，写明开发选择、最后评价、限制、继续/修改/停止的决定和下一项实验。把 `submission.json` 的状态改成 `complete`，然后运行：

   ```bash
   python scripts/course.py check 32
   python scripts/course.py ci
   ```

   `ci` 会在临时副本中删除已提交结果并按最终清单重建；它通过才说明最终命令可以确定性复现。

## 必须提交什么

- `contract.json`、固定后的 `config-final.json`、`analysis.py` 和已经切换到最终命令的 `submission.json`。
- 最终运行生成的 `artifacts/summary.json`、`records.csv` 和 `manifest.json`。
- 报告中保留开发阶段的两个方案比较、候选选择理由、指标和停止条件。
- 最后评价中同分母的手算、严重条件核对和至少一条逐步解释。
- 从新输出目录重跑的结果，以及摘要能证明和不能证明什么。
- 继续、修改或停止的理由、一个仍未解决的问题和一项具体下一实验。

## 不同起点怎么做

### 入门支持（Support）：按两阶段清单完成同一核心任务

使用 [SUPPORT.md](SUPPORT.md) 先完成开发评价和候选固定，再显式切换到最后评价。使用清单不降低完成标准。

### 必做任务（Core）：让同学能重跑并判断证据

所有人都要保存固定配置、数据、命令、确定性输出、限制和下一项实验，并清楚区分开发结果与最后评价。

### 提高任务（Upgrade）：由同伴独立复核

请同伴只读 README 和你的交付文件重跑，记录其停顿点并修正文档；不要先做口头演示。

### 换数据重测（Transfer）：设计下一批评价

写清新批次的来源、覆盖条件和标注办法。已经看过的最后评价只能转为开发数据，不能重新命名后继续使用。

### 自选拓展（Open extension）：形成小规模试用方案

写清人工复核比例、报警条件、恢复版本、资源预算和停止条件，让下一轮证据能够改变建议。

## 运行限制

实验是离线确定性文字路由，不执行真实预约或账户操作。开发数据和最后评价都由课程编写者制作，不能证明真实部署效果。运行通常数秒内完成，不需要显卡或网络；概念检查按课堂安排联网。

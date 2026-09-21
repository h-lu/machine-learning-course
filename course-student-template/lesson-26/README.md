# 第 26 课（S24）：怎样用下一项实验改进整件作品

## 本课要解决什么问题

前五课围绕同一个校园设备请求流程，依次保存了路线、资料、工具返回值、权限判断和故障位置。本课把这些证据连起来：先在**开发数据**上选择一项修改，固定配置后，再用一份没有参与选择的 **holdout 数据**做最后一次评价。holdout 是“留到最后的数据”，作用是检查候选方案在新请求上是否仍然成立。

你要提交一个实际运行的原方案、一项只改变一个设置的候选方案、两者的开发结果、一次独立的最终评价，以及采用、限制使用、保留原方案或停止自动处理的建议。命令失败时，先保留报错、配置和已有结果，再按 [SUPPORT.md](SUPPORT.md) 核对；旧输出不能代替本次运行。

## 本课要学会什么

| 标准术语 | 本课中的含义 | 掌握表现 |
|---|---|---|
| 原方案（baseline workflow） | 本模块提供并实际运行过的流程，是候选方案的对照。 | 能指出原方案的配置和运行结果来自哪里。 |
| 候选修改（candidate change） | 为检验一个失败解释，只改变的一项设置。 | 能说明改了哪个字段、为什么改，以及其他字段为何保持不变。 |
| 公平比较（controlled comparison） | 两个方案使用相同输入和评价规则，只让目标因素不同。 | 能追踪哪条请求因该因素而改变。 |
| 开发数据（development data） | 用于发现问题、选择配置和设计候选的数据。 | 看过结果后继续修改时，能把该数据继续称为开发证据。 |
| 最终评价数据（holdout data） | 在候选设置固定后才使用、没有参与选择的数据。 | 能把自动处理、自动错误和转人工分别报告，而不是合成一个“总正确率”。 |

本课的数据角色和每个字段见 [data/DATA.md](data/DATA.md)，关键关系的解释与最小数值例子见 [LEARN.md](LEARN.md)。

## 90 分钟安排

| 时间 | 活动 |
|---|---|
| 0–15 分钟 | 回顾 S19–S23 的中间结果，写出两个可能的失败原因 |
| 15–35 分钟 | 在 W01–W12 开发数据上运行无修改对照和单因素候选 |
| 35–52 分钟 | 追踪改变的请求，设计一条新的开发条件并决定候选设置 |
| 52–60 分钟 | 把最终选择写入 `config-final.json`，检查只有一个候选字段改变 |
| 60–70 分钟 | 明确固定配置后，单独运行 F01–F06 holdout |
| 70–78 分钟 | 分开核算自动处理结果和转人工数量，形成使用建议 |
| 78–90 分钟 | 完成概念检查与提交检查 |

## 完成步骤

以下命令都在学生仓库根目录运行。

1. 开始本课并运行“候选没有实际变化”的程序检查：

   ```bash
   python scripts/course.py start 26
   python lesson-26/analysis.py --data lesson-26/data/base.json --config lesson-26/config-start.json --output lesson-26/artifacts/no-change
   ```

   成功时终端会提示先查看 `development_cases.csv`。这个文件只含 W01–W12 开发请求；`summary.json` 的 `evaluation_mode` 应为 `development`。原方案与候选设置完全相同，所以两者结果也应相同。若不同，先检查比较程序，不能把差异当作改进。

2. 运行只改变 `candidate_filter_untrusted` 的候选：

   ```bash
   python lesson-26/analysis.py --data lesson-26/data/base.json --config lesson-26/config-support.json --output lesson-26/artifacts/filter-source
   ```

   打开 `filter-source/development_cases.csv`，先找 `W11`。比较 `baseline_document`、`candidate_document`、`baseline_status` 和 `candidate_status`，再用 [data/DATA.md](data/DATA.md) 解释过滤来源不可信的资料为何改变这一行。W07–W12 在前课已经出现，本课仍把它们作为**既有开发证据**，不能叫最终评价。

3. 分开核算自动处理和转人工。默认开发运行共有 12 条请求，其中 8 条由程序自动处理，4 条按任务定义应转人工。核对 `summary.json` 中两条流程各自的 `automatic_count`、`automatic_correct`、`automatic_errors`、`appropriate_handoffs` 和 `deferred_automatable`。手算时，自动准确率的分母是自动处理条数；转人工数量另报，不能把转人工算成答错，也不能把尚未知晓的人工结果算成答对。

4. 设计一条自己的开发条件，让它有机会改变轨迹或决定。复制开发数据：

   ```bash
   cp lesson-26/data/base.json lesson-26/data/mine.json
   ```

   在 `mine.json` 中只改一条 W 请求的 `text`，保持它的用途、`expected_route` 和 `expected_value` 不变。例如把熟悉说法改成同义但较少见的说法。先在报告中预计路线、资料或转人工状态会怎样变，再用 `config-support.json` 运行：

   ```bash
   python lesson-26/analysis.py --data lesson-26/data/mine.json --config lesson-26/config-support.json --output lesson-26/artifacts/my-development-check
   ```

   如果你选择阈值作为候选，则复制配置并让资料过滤回到原方案值，只改变 `candidate_confidence_threshold`。程序会拒绝一次改变多个候选设置。根据开发证据决定最终候选；候选不必获胜。把选定的 development 配置写入 `config.json`，再运行 `python scripts/course.py run 26`。终端只能提示 `development_cases.csv`；打开根目录结果，确认 `evaluation_mode=development`。此时不要把提交状态改成完成。

5. **先固定候选，再进行最终评价。** 把选择写入 `config-final.json`，确认 `evaluation_mode` 为 `final`，并记录“从此不再依据 F01–F06 修改这份候选”。在这一步之前不要打开 `data/holdout.json`。然后只运行一次：

   ```bash
   python lesson-26/analysis.py --data lesson-26/data/holdout.json --config lesson-26/config-final.json --output lesson-26/artifacts
   ```

   成功后先看 `artifacts/final_cases.csv` 的 F01–F06，再看 `artifacts/summary.json`。默认有 6 条请求：4 条自动处理、2 条按定义转人工。若看过结果后又改配置，这 6 条就参与了选择；必须把它们降为开发证据，另备新的 holdout 才能再次声称是独立最终评价。

6. 完成 `report.md`。写清原方案来源、候选只改了什么、自设计开发条件造成的实际变化、holdout 中自动正确数/自动处理数、自动错误数和适当转人工数，以及证据支持的使用建议。模板中的 `submission.json` 默认只运行开发数据，避免开发阶段误看 holdout。候选固定并完成上一步后，再把现成的 final 提交清单复制过去：

   ```bash
   cp lesson-26/submission-final.json lesson-26/submission.json
   python scripts/course.py run 26
   ```

   第一条命令把可复现命令明确切换为 `holdout.json + config-final.json`；第二条命令重新生成根目录下的 final 结果。不要在开发阶段提前复制这个文件。

7. 确认 `submission.json` 所列文件存在，把状态从 `in_progress` 改为 `complete`，再执行：

   ```bash
   python scripts/course.py check 26
   ```

## 必须提交什么

- `config-final.json`：已经在开发阶段固定、且相对原方案只改变一项候选设置。
- `artifacts/summary.json` 与 `artifacts/final_cases.csv`：显式 final 命令产生的独立最终评价。
- 一组开发比较结果，以及一条自拟开发条件的预计、实际轨迹和它是否改变决定；在报告中写出文件路径。
- `report.md`：分别报告自动处理、自动错误、适当转人工和不必要转人工，并说明采用、限制使用、保留原方案或停止的理由。
- `submission.json`：在最后阶段从 `submission-final.json` 复制得到，包含提交状态、报告路径、结果路径和显式 final 命令；仓库默认版本仍只运行开发数据。

## 不同起点怎么做

### 入门支持（Support）：按现成单因素候选完成全流程

使用 [SUPPORT.md](SUPPORT.md) 的命令比较“不过滤来源”和“过滤不可信来源”，追踪 W11，并在配置固定后运行 F01–F06。使用支持路径仍完成同一关键关系，也不降低评分上限。

### 必做任务（Core）：根据开发证据完成一次可归因的修改

写出两个竞争解释，选择一个因素，运行自己的开发条件，固定候选，再做一次 holdout 评价。评价结论必须同时包含自动结果和人工工作量。

### 提高任务（Upgrade）：比较另一项候选的开发证据

在查看 holdout 之前，可把候选改成只提高置信度阈值，比较自动错误与转人工的变化。若已看过 holdout，只能在新的开发数据上继续探索，不能重复使用原 holdout 选择方案。

### 换数据重测（Transfer）：改成另一种服务请求

重新定义路线、资料、工具、允许动作和人工处理条件，并另备开发数据与 holdout。设备请求上的比例不能直接迁移。

### 自选拓展（Open extension）：接入受控的文本生成步骤

资源统一可得时，可以增加本地文本生成，但每个新输入必须得到与之匹配的新输出，并分别评价事实依据、任务完成和副作用；固定记录不能冒充新生成。

## 运行限制

必做实验离线运行，只需要普通 CPU、Python 3.10 以上和约 8 GB 可用内存；不需要网络、付费服务或显卡。单次运行目标不超过 3 分钟，从头重跑目标不超过 5 分钟。仓库中的小数据与规则程序只证明这些人工案例的行为，不证明真实用户、生产系统或通用 AI 能力。由于课程仓库对学生可见，holdout 的“未见”依赖按步骤不提前打开；正式高风险评价还需要由教师在配置固定后另行提供未公开数据。

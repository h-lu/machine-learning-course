# S15 入门支持：先开发提示，再检查新问题


以下命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。
本页是一条完整必做路径。第一项小任务：在 `report.md` 写下两个预计——资料充足时新提示会不会改变核心答案；资料为空时“资料不足”要求会不会减少没有依据的说法。

## 1. 运行原提示

从仓库根目录执行：

```bash
python scripts/course.py start 17
python lesson-17/analysis.py --config lesson-17/config-start.json --output lesson-17/artifacts/prompt-original
```

先打开 `prompt_features.json`，确认四个规则都是 `false`，再打开 `responses.csv`。6 个 development 问题中有 4 个有资料、2 个无资料。原提示三次运行的任务完成均约为 `4/6=0.667`，来源比例为 0，无资料说法比例约为 `2/6=0.333`。重复三次仍只有 6 个不同问题。

## 2. 运行新提示

```bash
python lesson-17/analysis.py --config lesson-17/config-support.json --output lesson-17/artifacts/prompt-revised
```

新提示明确“先写依据、引用来源、资料不足时停止”。先用 `prompt_features.json` 核对四个程序开关，再读输出。`metrics.csv` 中任务和来源比例应为 `6/6=1`，无资料说法比例为 0。格式比例是 `4/6`，因为无资料回答没有“结论：”这一标题；这不等于它们内容错误。指标定义必须和用途一起解释。

## 3. 看具体问题，不只看平均

对照两份 `responses.csv`：

- `dev-01` 的核心时间不变，新提示增加资料与结构。
- `dev-04` 没有办公室资料。原提示会从三种模糊猜测中选一句，新提示返回资料不足。
- `dev-05` 的回答内容正确，但只有新提示写出来源。

随机种子只选择预设措辞，不能模拟真实模型全部波动。

## 4. 改一条提示要求

从 `config-support.json` 另存 `config-mine.json`。只删掉“先写依据”或只删掉“资料不足”，保持问题和重复次数不变。这个教学程序只识别“引用来源”“先写依据”“资料不足”和“结论”四个字面短语，运行后必须用 `prompt_features.json` 核对改变确实生效：

```bash
python -m json.tool lesson-17/config-mine.json
python lesson-17/analysis.py --config lesson-17/config-mine.json --output lesson-17/artifacts/my-check
```

比较你预计变化的那一项，并检查是否出现意外变化。新提示必须引用这个新目录，不能引用 `prompt-revised` 冒充结果。其他同义表达可作为拓展，但如果开关没有变化，程序就没有测试那条表达。

## 5. 选好以后再读 final 数据

在 development 上确定采用提示和评价规则，把同样的 `prompt_text` 写入 `config-final.json`，并确认 `evaluation_split` 是 `final`。在此之前不打开 `data/final.json`。

然后用现成清单明确切换到 final：

```bash
cp lesson-17/submission-final.json lesson-17/submission.json
python scripts/course.py run 17
```

Windows PowerShell 不识别 `cp` 时，使用 `Copy-Item lesson-17/submission-final.json lesson-17/submission.json`，也可以在文件管理器中复制并覆盖。复制后，`course.py run` 会按 `submission.json` 显式读取 `data/final.json` 和 `config-final.json`，而不再运行默认 development。

final 有 4 个不同问题，分母是 4。先打开根目录的 `artifacts/summary.json`，确认配置是 `final`；再打开 `responses.csv`，确认只有 `final-01`–`final-04`。若你看过这些结果后又改提示，就把它们称为继续开发，并说明需要新的最终数据。

## 6. 完成提交

报告保留最初预计、三次开发比例、一个具体失败、个人改动和 final。说明模板生成器每次都生成匹配输出，但不能代表真实大模型。完成 `contract.json` 和报告后，在复制过来的 `submission.json` 中把 `status` 从 `in_progress` 改为 `complete`，再运行：

```bash
python scripts/course.py check 17
```

`check` 通过只证明 final 文件齐全。后续 `course.py ci` 会用同一条 final 命令重建它们。

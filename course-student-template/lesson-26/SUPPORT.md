# 第 26 课入门支持：先定候选，再看最终数据

这条路径完成与必做任务相同的核心关系。所有命令都在学生仓库根目录运行。

## 1. 先确认比较程序不会凭空产生差异

```bash
python scripts/course.py start 26
python lesson-26/analysis.py --data lesson-26/data/base.json --config lesson-26/config-start.json --output lesson-26/artifacts/no-change
```

成功标志是终端提示 `development_cases.csv`。先打开该文件任意一行：原方案和候选的路线、资料、数值与状态应相同。这里的 W01–W12 都是开发数据。

## 2. 只改变资料来源过滤

```bash
python lesson-26/analysis.py --data lesson-26/data/base.json --config lesson-26/config-support.json --output lesson-26/artifacts/filter-source
```

打开 `lesson-26/artifacts/filter-source/development_cases.csv` 的 W11 行，依次看：

1. `baseline_document`：原方案实际用了哪份资料；
2. `candidate_document`：过滤来源后用了哪份资料；
3. 两条 `status`：自动结果是正确还是错误；
4. `expected_value`：人工参考的目标数值。

默认核对示例是：12 条开发请求中有 8 条自动处理、4 条适当转人工；原方案自动正确 7/8，候选自动正确 8/8。这个数值只用于发现运行或理解错误，不是必须得到的个人结论。

## 3. 加一条自己的开发条件

```bash
cp lesson-26/data/base.json lesson-26/data/mine.json
```

在 `mine.json` 中只改一条请求的 `text`，保持同一用途及其 `expected_route`、`expected_value` 不变。先写预计，再运行：

```bash
python lesson-26/analysis.py --data lesson-26/data/mine.json --config lesson-26/config-support.json --output lesson-26/artifacts/my-development-check
```

检查修改行的 `predicted_route`、`executed_route`、`document` 和 `status`。即使结果没有变，也要说明这条检查排除了什么担忧。

## 4. 用默认提交命令运行并检查开发结果

把选定的开发配置写入 `config.json`。若采用来源过滤候选，运行：

```bash
cp lesson-26/config-support.json lesson-26/config.json
python scripts/course.py run 26
```

终端应只提示 `development_cases.csv`。打开 `lesson-26/artifacts/summary.json`，确认 `evaluation_mode=development`；再确认同目录有 `development_cases.csv`。此时不要把 `submission.json` 改为 `complete`，也不要运行提交检查，因为 final 证据尚未产生。模板的默认提交命令不会读取 holdout。

## 5. 固定最终配置

把你选择的单因素候选写入 `lesson-26/config-final.json`。检查：

- `evaluation_mode` 是 `final`；
- 三组 `candidate_...` 设置中，最多一项与对应的 `baseline_...` 不同；
- 报告已经写明候选为何由开发证据选出。

完成这三项之前，不打开 `data/holdout.json`。

## 6. 单独运行最终评价

```bash
python lesson-26/analysis.py --data lesson-26/data/holdout.json --config lesson-26/config-final.json --output lesson-26/artifacts
```

成功标志是本次运行产生或更新 `final_cases.csv`，终端不会报告生成 `development_cases.csv`。如果你先前把开发结果写在同一个 `artifacts/` 目录，旧的 `development_cases.csv` 会保留；它不是这次 final 运行的新产物，不要把两个文件混成同一批评价。默认共有 6 条最终请求，其中 4 条自动处理、2 条适当转人工。分别核算：

- 自动正确数 ÷ 4 个自动处理请求；
- 自动错误数；
- 适当转人工数 ÷ 2 个应转人工请求；
- 不必要转人工数。

转人工后的真实处理结果没有观察到，所以不能把它记为自动答对或自动答错。

## 7. 完成报告与提交检查

在 `report.md` 中填写开发选择、自拟条件、final 结果和建议。模板中的 `submission.json` 默认仍读取开发数据；只有到这一步才切换为 final 提交清单并重跑：

```bash
cp lesson-26/submission-final.json lesson-26/submission.json
python scripts/course.py run 26
```

复制后，`run 26` 应明确显示它使用同一份 `config-final.json` 和 `holdout.json`，并复现根目录中的最终结果。若失败，保留终端报错、配置和已有开发结果；修正后再运行，不能复制核对示例充当自己的实验。

确认 `lesson-26/artifacts/summary.json` 和 `final_cases.csv` 存在，在 `submission.json` 把 `status` 从 `in_progress` 改成 `complete`，最后运行：

```bash
python scripts/course.py check 26
```

检查通过只证明 final 命令可复现且文件齐全；使用建议仍要依据自动结果、人工量和结论限度人工审阅。

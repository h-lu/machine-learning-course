# S13 入门支持：先认出谁改变了


以下命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。
这是完成本课必做任务的一条详细路径，不是额外作业。第一项小任务只需五分钟：运行起点，然后在 `routes.csv` 圈出哪一行改了参数。

## 1. 先写预计

在 `report.md` 写三句：固定记录不会改变输入或参数；输入规则只改变送入当前判断的信息；输出头训练会改变 `bias` 和 `weight`。这只是预计，运行后用文件核对。

## 2. 从仓库根目录运行

终端当前目录应同时看到 `scripts` 和 `lesson-15`：

```bash
python scripts/course.py start 15
python lesson-15/analysis.py --config lesson-15/config-start.json --output lesson-15/artifacts/support-start
```

成功提示包含“先看 routes.csv”。打开该文件，不要先在很长的 JSON 中找数字。三行都在相同 6 条 evaluation 记录上：固定记录准确率约 `4/6=0.667`；输入规则和训练输出头约 `5/6=0.833`。数字只是给定人工数据的核对值，不是评分目标。

## 3. 核对一条记录和一次更新

在 `records.csv` 找 `ev-02`。固定分数是 0.49，输入规则触发后是 0.65；0.49 小于 0.5，0.65 大于 0.5，因此分类改变。它发生在推理时，`changed_parameters` 仍是 False。

打开 `parameter_trace.csv`。第 0 步 `weight=1`，第 120 步约为 2.340；训练损失约从 0.664 降到 0.626。这里训练的是输出头。基础分数没有重算，所以不能写“完成了预训练”。输出头路线的评价准确率虽提高，但对数损失可能没有更好；这提醒你不能只选一个好看的数。

## 4. 只撤掉输入增量

```bash
python lesson-15/analysis.py --config lesson-15/config-support.json --output lesson-15/artifacts/support-compare
```

这份配置只将 `context_boost` 从 0.16 改为 0。输入规则路线应退回与固定记录相同的分数和指标；输出头训练不受影响。把“改了什么、哪些行变化、哪些不变”写入报告。

## 5. 做自己的单因素检查

从 `config-start.json` 另存 `config-mine.json`，只改 `context_boost`。先预计 `ev-02` 的新分数，再运行：

```bash
python -m json.tool lesson-15/config-mine.json
python lesson-15/analysis.py --config lesson-15/config-mine.json --output lesson-15/artifacts/my-check
```

若选 0.08，`ev-02` 应约为 0.57。先自己算 `0.49+0.08`，再对照。这个加法是人工规则，不是神经网络学到的语义。

## 6. 写报告并检查提交

报告分别写“固定材料观察”“输入变化”“参数更新”，引用实际目录；再列出至少两条不能推出的结论。填写 `contract.json`，将采用配置保存为 `config.json`，完成后把 `submission.json` 标成 `complete`。

```bash
python scripts/course.py run 15
python scripts/course.py check 15
```

找不到输出时先检查是否在仓库根目录、配置文件名和输出目录。运行失败后旧文件不会证明本次成功；保留报错，修复后用新目录重跑。

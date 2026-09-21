# S16 入门支持：先找资料，再核对回答


以下命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。
这是本课必做任务的详细路径。第一项小任务：读 `data/DATA.md` 后在纸上写出 `dev-01` 的两个检索词“作业、提交”，到三份资料中各数出现几个。

## 1. 运行重合阈值 1

```bash
python scripts/course.py start 18
python lesson-18/analysis.py --config lesson-18/config-start.json --output lesson-18/artifacts/threshold-1
```

先开 `retrieval.csv`。`dev-01` 与 D1 重合 2 个词，因此选中 D1。再开 `answers.csv`，确认回答中的句子逐字来自 D1，`retrieval_ok`、`answer_supported`、`task_ok` 都为 True。

## 2. 找出两个不同失败环节

- `dev-03` 与 D2 重合两个词，检索正确；抽取器却在两个句子打平时选了第一句，没有回答“三个阶段”。`checks.csv` 将它标为 `answer` 失败。
- `dev-05` 在所有资料中重合数为 0，系统返回资料不足。这是正确停止，不是把空答案当成事实。

“有来源编号”不足以证明回答正确；还要检查句子是否回答了问题。

## 3. 只提高检索阈值

```bash
python lesson-18/analysis.py --config lesson-18/config-support.json --output lesson-18/artifacts/threshold-2
```

这次 `dev-02` 只有“补交”一个重合词，所以 D1 不再入选，失败环节变为 retrieval。两种阈值各有取舍：阈值 1 容易接受弱匹配，阈值 2 会漏掉短查询。

## 4. 添加自己的查询

复制数据文件：

```bash
cp lesson-18/data/base.json lesson-18/data/mine.json
```

Windows 终端不识别 `cp` 时，在文件管理器复制，或在编辑器中把 `base.json` “另存为” `mine.json`；两种做法得到同一个文件。

在 `queries` 数组中增加一项 development 查询。入门例子可以问“运行成功能证明理解吗”，检索词写 `程序运行` 和 `理解`，期望资料写 D3；也可以设计自己的问题。每个字段都要说明，不能查看程序输出后再改期望答案。

```bash
python -m json.tool lesson-18/data/mine.json
python lesson-18/analysis.py --data lesson-18/data/mine.json --config lesson-18/config-start.json --output lesson-18/artifacts/my-query
```

新增后 development 分母应从 5 变为 6。核对新问题的检索、抽取句子和任务结果。

## 5. 最终检查与提交

阈值选好后，先把采用的 `min_overlap` 写入 `config-final.json`，确认其中 `evaluation_split` 仍为 `final`。在此之前不打开 `data/final.json`。然后复制 final 清单并运行：

```bash
cp lesson-18/submission-final.json lesson-18/submission.json
python scripts/course.py run 18
```

Windows PowerShell 不识别 `cp` 时，使用 `Copy-Item lesson-18/submission-final.json lesson-18/submission.json`，也可以在文件管理器中复制并覆盖。复制后，`course.py run` 会按 `submission.json` 显式读取 `data/final.json` 和 `config-final.json`。

先打开根目录的 `artifacts/summary.json`，确认配置是 `final`；再打开 `checks.csv`，确认只有 `final-01`–`final-04`。报告分别写检索成功率与任务完成率，不混成一个“准确率”；引用 S15 的提示结果，说明清楚提示不能补出不存在的资料。

完成 `contract.json` 和报告后，在复制过来的 `submission.json` 中把 `status` 从 `in_progress` 改为 `complete`，再运行：

```bash
python scripts/course.py check 18
```

JSON 报错时按显示的行列检查英文双引号、逗号和括号。旧输出可能仍存在；修复后重跑上面的 `course.py run`，确认终端本次成功。`course.py ci` 会用同一条 final 命令重建结果。

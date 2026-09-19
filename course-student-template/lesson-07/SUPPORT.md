# S05 入门支持：同样的新增条数，信息可能不同

这是 [本课任务](README.md) 的详细做法，不是额外作业。完成下面的比较、自己的检查和解释，就覆盖必做任务；不用再把 README 的另一条路径重复一遍。你可以使用现成程序和教师帮助，不需要先会写训练代码。**先做第一项小任务：找到四种方案各增加几条样本、来自什么时段。**

## 1. 先知道今天在检查什么

**候选池**是可以从中选取新样本的集合；**标注预算**是能用于获取标签的资源，本课用最多增加的样本条数表示。**合成数据**是人工或程序生成的数据；本课由原模型生成新增标签，不是新增的真实观察。这里的候选池也只是人工数据模拟。

先读 [LEARN.md](LEARN.md) 的对应例子。术语表按需查，不要为了开始上课把整张表背完。在 `report.md` 先写一句你的用途和预计结果；其余栏目等拿到结果再填写。

## 2. 不改代码，先跑通并找到结果

在学生仓库根目录运行，那里同时有 `scripts` 和 `lesson-07`。不知道终端或根目录在哪里，按 [第一次运行指南](../docs/FIRST_RUN.md) 的目录与环境检查操作；不要在 Python 的 `>>>` 中输入命令。只能识别 `python3` 的电脑，将以下 `python` 换成 `python3`。

```bash
python scripts/course.py start 07
python lesson-07/analysis.py --config lesson-07/config-start.json --output lesson-07/artifacts/support-start
```

`config-start.json` 是随课准备的起始配置，先不要改；数据仍来自本课 `data/base.json`。终端出现“结果写入”后，在 `lesson-07/artifacts/support-start/` 找到 `comparison.csv`、`records.csv`、`added_samples.csv` 和 `summary.json`。CSV 可以用表格软件或文本编辑器打开；文本编辑器中每行是记录，逗号隔开列。先看下面点名的列，不要求一次看懂所有指标。

## 3. 停下来核对，不只看运行成功

先打开 `comparison.csv`，暂时不看全部指标，只看方法名、`added_n`（新增条数）、`evening_train_n`（训练中晚间条数）和 MAE。所有方案使用同一组 6 条验证样本。

| `method` | 新增条数 | 晚间训练条数 | MAE（分钟，约） |
|---|---:|---:|---:|
| no_addition：不补数据 | 0 | 0 | 4.333 |
| random_sample：随机抽样 | 4 | 2 | 3.836 |
| group_first：优先补晚间 | 4 | 4 | 3.000 |
| synthetic：模型生成标签 | 4 | 0 | 4.333 |

“不补数据”是参照，不要求它也增加 4 条。其他三种方案新增条数相同，但实际采集与生成的成本不一定相同。

再打开 `added_samples.csv`，找 `method=group_first` 的 B01–B04；核对全是晚间。然后找 synthetic 的 `label_source`，它标明模型生成。候选池选择先看人数、时段和编号，选中后才取标签；本课不需要你联网采集或调用 AI。

在 `records.csv` 找 B05：原方案预测 3、实际 8；优先补晚间后预测 5，绝对误差从 5 变为 3。终端还列出分组 MAE，请各抄一项午间、晚间结果，不只看总体。

以上数值是给定数据和起始配置的**自查参考**，四舍五入造成的小差异正常。它们不是必须达到的评分标准。先自己算或数，再对照；出现较大差异时检查方法名、配置路径和输出目录，不手改结果文件。

## 4. 跑一个已经准备好的对照

`config-support.json` 已经准备好，不用从空白文件写 JSON。

这个副本只把 `budget` 从 4 改为 2。三种补充方案各增加 2 条，不补数据仍是 0。优先晚间的方案现在训练 6 条，其中晚间 2 条，验证 MAE 约 3.222。不要因为样本减少后一次结果变化，就断言任意任务都需要同样预算。

```bash
python lesson-07/analysis.py --config lesson-07/config-support.json --output lesson-07/artifacts/support-compare
```

并排打开两次结果，把“改了什么、哪项结果变了、哪项不变”记在报告。两个输出目录分开，不覆盖第一份。

## 5. 做一次有理由的个人选择

从 `config-start.json` 另存 `config-mine.json`。预算保持 4，自己选另一个整数随机种子，只改 `seed`（如 11）。保留两次随机抽样的编号、时段和 MAE，说明哪类输入仍缺少；不要只保留较好的一次，也不要先看候选标签再选编号。

另存文件时在编辑器中使用“另存为”，文件名是 `lesson-07/config-mine.json`。只改刚才点名的字段值，保留英文双引号、逗号和冒号，其他字段先不动。文件名不要多出 `.txt` 后缀。检查格式，再运行：

```bash
python -m json.tool lesson-07/config-mine.json
python lesson-07/analysis.py --config lesson-07/config-mine.json --output lesson-07/artifacts/my-check
```

这次填写自己的预计、实际结果和理由，不照抄例子中的采用建议。允许结果支持保留原方案，也允许暂不使用。需要 AI 帮助时，可以提问：“请只解释这条命令和这一行数据，先让我计算，再帮我核对；不要替我填最终建议。”

## 6. 写完报告，确认文件已保存

在 `report.md` 回答本课的问题，每项几句话；删除模板提示语，写出配置和结果路径。最少保留：用途与预计、一项手算或计数、同条件比较、自己的检查及原因、仍不能得出的结论。把想保留的参数写回本课 `config.json`，不要改课次字段。

`contract.json` 是任务说明，保留 `lesson` 并填其余六项：`question` 写问题，`user` 写使用者，`data_source` 写人工数据来源，`metric` 写指标和单位/分母，`split_plan` 写数据用途，`initial_expectation` 写实验前预计。完成实际工作后再将 `submission.json` 的 `status` 改为 `complete`。

```bash
python scripts/course.py run 07
python scripts/course.py check 07
git add lesson-07
git add -f lesson-07/artifacts
git diff --cached --name-only
```

最后一条只列出准备提交的文件；确认报告、任务说明、配置副本和引用的结果都在。你改过共享代码时，还要保存相应代码。上面没有提交到远程，接着按 [操作与提交步骤](../docs/WORKFLOW.md) 创建提交和本课 `v2-l07-final` 标签；不要覆盖已存在的标签。

## 卡住时先这样做

找不到脚本：回到学生仓库根目录。找不到 `config-mine.json`：检查是否另存到了本课目录或多了 `.txt`。JSON 报错：先运行上面的格式检查，修正显示的行列。运行失败后旧输出可能还在，不能当作新结果；换新目录重跑并确认成功提示。

环境仍不能运行时，先用第 3 节表格完成手算、计数和一段解释，明确注明“仅手算，尚未运行”，把命令与报错交给教师处理，之后补跑。这是不中断学习的办法，不是用给定答案冒充已完成实验。已完成核心比较后再选提高或拓展任务；不需要把全部层次做一遍。

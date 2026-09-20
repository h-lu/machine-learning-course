# 第 03 课入门支持：先核对一条预测，再做一次比较

这是第 03 课必做任务的一条完整路径，不是额外作业。你会先手算一条记录，再运行起始实验，比较同一批验证记录，最后只改一个设置做自己的检查。每一步都写清“从哪里开始、成功后看什么、报告写什么”。

## 1. 第一项任务：先在纸上算 B05

B05 是一个虚构窗口在第 5 天的一次排队记录，不是第五位同学的姓名。开始排队时前面有 **1 人**，结束后实际等了 **8 分钟**。人工规则是：

```text
预计等待分钟数 = 1 + 2 × 前面人数
```

先不要打开程序，在草稿写下：

1. 输入是多少人？
2. 规则的预测是多少分钟？
3. 预测和实际相差多少分钟？
4. 如果只在预测至少 8 分钟时提醒，是否提醒？

核对时再看答案：预测是 `1 + 2 × 1 = 3` 分钟，绝对误差是 `|3 − 8| = 5` 分钟，预测低于 8，所以不提醒。这里的 **特征（feature）** 是预测时可用的前面人数；**标签（label / target）** 是事后记录的实际等待分钟数；**预测值（prediction）** 是规则算出的 3 分钟。不要用事后才知道的 8 分钟决定提醒。

打开 `lesson-03/report.md`，先填写第 1 节中的使用者、输入、输出、用途和预计。不会写时可以先写：“给准备排队的同学显示大致等待分钟数；输入是加入队伍时看到的人数；输出是预计分钟数；我预计线性回归在验证集上误差较小。”这只是起点，运行后要用自己的结果修改。

## 2. 从仓库根目录运行起始实验

仓库根目录是能同时看到 `scripts`、`lesson-03`、`mlcourse` 和 `requirements.txt` 的文件夹。不要在 Python 的 `>>>` 后输入下面命令。电脑只识别 `python3` 时，把 `python` 换成 `python3`。

```bash
python scripts/course.py start 03
python lesson-03/analysis.py --config lesson-03/config-start.json --output lesson-03/artifacts/support-start
```

第一条只记录本课开始；第二条读取 `lesson-03/data/base.json` 和 `config-start.json`，把结果写到 `lesson-03/artifacts/support-start/`。看到终端显示“结果写入”后，先打开 `records.csv`，再打开 `comparison.csv`，最后需要时看 `summary.json`。

## 3. 在 records.csv 中找到同一条记录

在 `lesson-03/artifacts/support-start/records.csv` 中找到 `id=B05` 且 `method=rule` 的一行。文件是 CSV，也就是用逗号分隔列的表格文本；第一行是列名。只核对这 6 列：

| 列名 | 含义 | B05 的核对值 |
|---|---|---:|
| `queue_length` | 开始排队时前面人数 | 1 人 |
| `actual` | 事后记录的实际等待 | 8 分钟 |
| `prediction` | 人工规则的预测 | 3 分钟 |
| `absolute_error` | 预测与实际的绝对差 | 5 分钟 |
| `alert` | 是否显示提醒 | `False`，不提醒 |
| `method` | 产生预测的方法 | `rule`，人工规则 |

三种方法会各写一行 B05，所以看到三个 B05 是正常的；它们仍是同一条样本，不是增加了三条数据。把这次核对写进报告第 2 节。

## 4. 用六条验证记录重算 MAE

打开同一目录的 `comparison.csv`，确认 `baseline`、`rule`、`linear` 各有 `n=6`。`n` 是评价样本数；本课的六个编号是 A05、A06、B05、B06、C05、C06。三种方法必须比较同样的六条记录。

在 `records.csv` 中只看 `method=rule` 的这六行，绝对误差依次是 1、1、5、5、7、7 分钟。手算：

```text
MAE = (1 + 1 + 5 + 5 + 7 + 7) ÷ 6
    = 26 ÷ 6
    ≈ 4.333 分钟
```

**平均绝对误差（MAE）** 是每条绝对误差的平均值；分母是参加评价的 6 条样本，不是全部数据的 24 条，也不是 CSV 中三种方法合计的 18 行。把三种方法的 `n`、`mae` 和单位抄入报告，并至少写出一次这样的加法和除法。

`no_action` 表示不提供分钟预测，也不发提醒，所以 MAE 为空或 `null`，不是 0。它不能因为提醒数是 0 就被说成误差最小。

## 5. 只改变提醒阈值

打开 `lesson-03/config-support.json`，和 `config-start.json` 对照。你会看到只有 `alert_minutes` 从 8 改成 10；它是“预测达到多少分钟才提醒”的阈值，不是回归系数。

先写预计：B06 的线性回归预测约为 8.333 分钟。阈值改成 10 后，B06 的预测值会不会改变？它的提醒状态会不会改变？MAE 会不会改变？然后运行：

```bash
python lesson-03/analysis.py --config lesson-03/config-support.json --output lesson-03/artifacts/support-compare
```

打开 `original` 和 `support-compare` 两个目录中的 `records.csv`，只比较 B06 的 `method=linear` 行；再看两个 `comparison.csv` 的 `linear` 行。核对示例是：预测仍约为 8.333，提醒从 `True` 变为 `False`，MAE 仍约为 2.556，提醒总数从 3 变为 1。示例只用于检查你有没有读对列，不是你报告必须得到的评分目标。若你希望把这个对照目录命名为 `trial`，等价命令是 `python lesson-03/analysis.py --config lesson-03/config-support.json --output lesson-03/artifacts/trial`。

如果你只看 B05，它两次都不会提醒，因为预测是 3，低于 8 和 10 两个阈值。这不代表阈值实验没有运行；要看指定样本和指定方法。

## 6. 做自己的一个选择

从 `lesson-03/config-start.json` 复制出 `lesson-03/config-mine.json`，只做下面一种选择：

- 把 `alert_minutes` 改成 9 或 12，并说明这个提醒标准服务谁、可能漏掉什么；
- 把 `stress_queue` 改成另一个人数，并说明这是没有实际标签的新输入，只能比较预测，不能计算误差。

先在报告第 3 节写预计，再检查 JSON 格式并运行：

```bash
python -m json.tool lesson-03/config-mine.json
python lesson-03/analysis.py --config lesson-03/config-mine.json --output lesson-03/artifacts/my-check
```

成功后：

1. 打开 `my-check/records.csv`，或查看终端的“新输入检查”；
2. 找一个指定方法和样本，记录预测值、提醒状态和单位；
3. 在报告写出实际结果与原预计的差别；
4. 如果是新人数，写明没有真实标签，所以不能算 MAE。

输出目录必须不同，不能让新结果覆盖 `support-start` 或 `support-compare`。

## 7. 写报告并检查提交文件

在 `report.md` 中完成 5 节：

- 任务与预计：谁使用、输入和标签是什么、你预计什么；
- 起始实验：B05 的一条计算、三种方法的同样本 MAE；
- 个人试验：只改了什么、实际变了什么；
- 建议：保留哪种用途、还缺什么证据、为什么不能说提醒让人少等；
- 运行记录：实际命令、配置文件和输出目录。

再填写 `contract.json` 的六个字段，保留 `lesson` 字段不动。把最后一次选择复制到 `config.json`，确认 `submission.json` 中的报告和结果路径正确，最后再把 `status` 改为 `complete`。

```bash
python scripts/course.py run 03
python scripts/course.py check 03
git add lesson-03
git add -f lesson-03/artifacts
git diff --cached --name-only
```

`check` 只检查提交文件是否齐全，不替你判断结论是否有依据。暂存清单至少应包含报告、任务说明、配置和报告引用的结果文件。

## 8. 如果卡住时怎么办

- **找不到脚本：**确认终端位于学生仓库根目录；不要在 `lesson-03` 目录里重复写 `lesson-03/`。
- **命令找不到 Python：**试 `python3`，并把所有命令中的 `python` 一起替换。
- **JSON 报错：**看报错中的行号和列号，检查英文双引号、逗号和数字，不要把数字写成带引号的文字。
- **结果数字不一样：**先核对配置文件、方法名、样本编号、输出目录和分母，不要手改 CSV。
- **暂时无法运行：**保留完整报错，完成 B05 手算和 MAE 手算，在报告中写“仅手算，尚未运行”，然后请教师协助补跑。

完成这条路径后，再进入教师通知的概念检查：A 版 5 题、学习阶段、B 版 5 题。概念检查检查的是本课关系，不替代报告；提交后不能返回修改。

### 3.1 看一个尚未使用的因素

回到 `data/base.json` 看 B05 的 `staff_count`、`weather` 和 `event_flag`。如果两个样本人数相同但工作人员或天气不同，你预计平均误差可能怎样变化？把它写成待检查的预计；起点程序没有使用这些字段。

# 第 8 课数据、模型与结果说明

## 真实主任务：一行代表什么

`../../data/bike/hour.csv` 是UCI提供的Capital Bikeshare 2011–2012逐小时租借记录，本课程保存官方原始字节。每行表示一个已记录小时，共17,379行、17列。没有空字段，也没有重复的日期与小时组合；从起始到结束日期应有的小时中，缺165个小时的记录。**未记录不是零租借**。本课不补造行，不把公开数据说成学生调查。

固定时间切分：训练日期 `<2012-07-01` 为13,003行；验证 `[2012-07-01,2012-10-01)` 为2,208行；测试 `>=2012-10-01` 为2,168行。默认起点用训练集计算均值，只输出验证误差；可选回归工具可输出训练与验证误差。两者默认都不报告测试预测。

| 原字段 | 意义与本课使用 |
|---|---|
| `dteday`、`hr` | 记录日期和0–23小时；合并成唯一时间；hr是本次可改变表示方式的输入 |
| `cnt` | 当小时记录租借总次数，预测目标；不代表没有车时未满足的需求 |
| `casual`、`registered` | 非注册与注册租借组成项，每行相加=cnt；禁作输入，避免答案泄漏 |
| `instant` | 记录编号，禁作业务输入 |
| `yr`、`mnth`、`weekday` | 年份编码（0为2011，1为2012）、月份（1–12）、星期编码（0–6，0为星期日）；月份和星期有顺序及周期，示例用指示变量表示 |
| `holiday`、`workingday` | 0/1编码，1表示是；数据把既不是周末、也不是假日的日期定义为工作日 |
| `weathersit` | 官方天气类别1–4；基础输入使用类别指示变量，数字不是天气大小 |
| `temp`、`atemp` | 官方已归一化的温度与体感温度；归一化在这里指按来源说明缩放数值，CSV中的值不直接以摄氏度计。0.5不能解释成0.5摄氏度；可选回归示例用 `temp`，不同时放入 `atemp` |
| `hum`、`windspeed` | 官方已缩放的湿度、风速数值，均不能直接当作原单位测量值；可选回归示例将它们作为基础输入 |
| `season` | 官方季节编号1–4。可选回归示例只用它检查分组；本地Readme与官网文字标签有冲突，保留 `season_1` 至 `season_4`，不擅自改译 |

天气类别4只有3条记录，全部在训练集中；验证和测试中没有该类记录，无法计算该组误差。实际天气可用于**当小时给定天气的条件估计**；提前一天用途要改用天气预报版本并重新验证。

来源、作者、DOI、CC BY4.0和字节审计见 [LICENSE_AND_SOURCE](../../data/bike/LICENSE_AND_SOURCE.md)。数据SHA-256为 `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`。

## 人工热身

本目录 `base.json` 有24条人工排队记录，12训练/6验证/6测试。只用它解释 `null`、训练均值和一致处理。`warmup` 命令读取训练集中9个已知人数，均值为13/9人，用给定规则 `等待分钟数=1+2×排队人数` 演示训练记录C04的计算，不报告人工数据的测试误差。这不是今天的真实数据实验。

## 开放起点与自己的实现

默认 `analysis.py` 调用 `load_development`，获得训练记录、验证记录和数据检查信息，不读取最后测试标签。它用训练集 `cnt` 的均值预测每条验证记录，作为基线。`candidate_predictions` 默认返回 `None`（尚未实现候选），所以默认输出只有基线。你可在该函数中返回自己算出的预测列表，或 `{自定方法名: 预测列表}`；也可另写自己的入口。

方法字典可同时包含自己实现的原方案和候选方案；`baseline` 是训练均值参照的保留名称。自行实现与假设匹配的原方案，从均值改成完整回归并非只改变小时编码，说明见 [README](../README.md#课堂任务)。

候选函数收到训练输入、训练 `cnt` 列表和评价输入。评价输入已排除 `cnt`、`casual`、`registered`、`instant`，避免把目标或其组成项带入预测。从训练集学习自己的处理参数，再将它们用于评价输入。默认程序不选择重点分组、解释误差原因或写报告。

默认基线结果保存在 `artifacts/baseline/`：

- `comparison.csv`：`split`（训练／验证／测试中的哪一部分）、`method`（方法名）、`n`（评价记录数）、`mae`（平均绝对误差）。
- `records.csv`：日期与输入条件、`cnt`（记录中的观测租借次数）、`prediction`（预测次数）、`err_signed`（预测−真实）、`err_absolute`（绝对差），以及方法名。
- `summary.json`：`training_n`（训练记录数）、`baseline_training_mean`（训练集租借次数均值）、`starter_only`（是否只有起点基线）等。
- `data_audit.json`：文件行数、时间范围等数据检查信息，不含默认测试误差。

默认重跑只更新这四份结果。自主方案新增的输出和字段需要在报告中说明，并更新 `submission.json` 的 `run` 和 `artifacts`；课堂任务还需要自己的两方案比较与核算。

保存测试前选择记录后，可调用 `load_test(root, decision_path)` 读取测试数据，再用自己的程序只评价所选方法。读取函数只检查选择文件已保存且非空，不要求统一方法或数值规则，也不会自动拟合或判断结论。`analysis.py` 提供 `--split test` 参数，默认命令不使用它；先实现自己的比较方案并保存选择，再进行最后测试，调用示例见 [SUPPORT](../SUPPORT.md)。

## 配置文件：哪些会影响当前程序

`config.json`、`config-start.json` 和 `config-support.json` 保留了旧人工例子的字段。默认 `analysis.py` 和 `warmup` 命令都不读取这三份文件，修改它们不会改变默认输出。自主方案的配置需要由你自己的程序读取；可选回归工具读取下面两份配置。

## 可选示例工具：两项配置怎样比较

| 配置 | 原方案kind | 候选kind |
|---|---|---|
| `config-hour-onehot.json` | `hour_numeric` | `hour_onehot` |
| `config-workingday-interaction.json` | `hour_onehot` | `workingday_interaction` |

两方案共用的天气和日历特征保持相同。第一种实验将连续 `hr` 替换为23个小时指示变量，省略0点这一参照类别；第二种实验只增加23个“小时指示变量×workingday”交互项。两种实验都保持回归算法与数据不变。

该示例算法固定为普通最小二乘回归，`ridge_alpha=0`，非零不允许。每列中心与总体标准差只从训练学习，验证和测试沿用；零标准差以1处理。日历列可能重复表达同一信息。输出保存 `design_rank`（设计矩阵的秩，即独立信息的数量）和 `design_columns`（列数），供按需检查；不能把单个系数当作因果效果。两方案都把负线性预测截为0。

通勤组固定为workingday=1且hr属于7、8、9、16、17、18、19。没有实测通勤者身份，不能称“通勤人群”。高租借次数分组的阈值只从训练目标值计算。其他参数含 `condition_hour_shift`（模拟小时登记偏移，模型不重训）等，保存于config-used；使用该示例作单因素比较时不同时调整它们；自主方案可选择其他合理处理，说明控制条件。

## 可选示例工具的结果格式

1. `comparison.csv`：split,method,kind,n,overall_mae,commute_n,commute_mae。`overall_mae`全体平均，`commute_mae`固定组平均，单位次租借／已记录小时。
2. `records.csv`：datetime、split、cnt、hr、workingday、分组字段、method、prediction、err_signed（预测−真实）、err_absolute（绝对差）。同一时间两方法两行是配对预测，不是独立加倍样本。
3. `group_metrics.csv`：dimension/group/method/n/mae等。无样本n=0，指标CSV空白、JSONnull，status=unavailable；不是零误差。
4. `feature_trace.csv`：取评价期第一条通勤组记录，保存每列原值、训练center/scale、转换值、权重和贡献；截距加各贡献后负数置0。它是核算起点，不替你作全部诊断。
5. `models.json`：feature_names、center、scale同序；weights第0项截距，之后对应各特征；design_rank/design_columns说明秩与列数。
6. `condition_check.json`：小时登记偏移敏感性检查，固定真实cnt和参数，不是改变现实时间的因果效果。

`metrics.json`与`summary.json`内容相同，保存训练／验证或测试指标；`error_cases.csv`每种方法最多12条绝对误差最大的记录，供开始分析失败；`data_audit.json`审计行、缺小时、组成恒等式等，不含默认测试误差。`config-used.json`、`preregister-used.json`、`source_manifest.json`保存实际配置、比较前的实验计划、源码／数据与结果文件的哈希及环境信息。哈希是由文件内容计算的校验值，可用来核对文件是否改变。

使用 `--output` 指定结果目录时，必须使用新目录，以保留旧结果。省略该参数时，示例工具在 `artifacts/run/` 重新生成验证结果；它不打开测试，也不覆盖单独保存的验证或测试目录。没有成功信息时不要把旧文件当新结果；不要手改生成的分数、记录或哈希。报告引用路径、字段、分母与命令。程序不会自动写报告或把status改为complete。

## 可选示例工具的完整调用资料

只有采用这个工具接口时才需要以下JSON文件；主任务的自由计划／选择不受其硬规则限制。命令在学生根目录运行；python3可替换python。hour-onehot是一个示例，另一示例换成config-workingday-interaction.json。

```bash
python scripts/lesson08.py preregister --config lesson-08/config-hour-onehot.json --output lesson-08/example-preregister.json
```

生成后填写以下字段，保留自动生成的配置哈希：

| 字段 | 要填写什么 |
|---|---|
| `primary_metric` | 主要指标：`overall_mae`（总体MAE）或 `commute_mae`（通勤组MAE） |
| `hypothesis` | 准备检查的解释 |
| `explanation` | 为什么这项改动能检查该解释 |
| `check_reason` | 为什么选这些评价条件 |
| `check_rule.minimum_primary_improvement` | 主要MAE下降必须超过的阈值；非负数 |
| `check_rule.maximum_secondary_mae_increase` | 另一项MAE最多允许上升多少；非负数 |

最后两个值的单位都是“次租借／已记录小时”。该工具把“主要MAE下降超过第一项、另一MAE上升不超过第二项”作为候选通过条件；它不会代填数值。这只是示例工具支持的一种选择规则，自主方案可以使用其他有依据的规则。

```bash
python scripts/lesson08.py bike --config lesson-08/config-hour-onehot.json --preregister lesson-08/example-preregister.json --output lesson-08/artifacts/example-validation
python scripts/lesson08.py decision --validation-run lesson-08/artifacts/example-validation --output lesson-08/example-decision.json
```

`decision` 命令生成文件后，填写 `selected_method`（所选方法名）和 `reason`（依据验证结果作出选择的理由），保留自动路径与哈希，再只评价已选方法：

```bash
python scripts/lesson08.py bike --config lesson-08/config-hour-onehot.json --unlock-test --decision lesson-08/example-decision.json --output lesson-08/artifacts/example-test
```

显式结果目录必须新建，不覆盖旧证据；示例工具test只报告所选方法。自己的选择理由、核算与建议仍需写进报告。若你采用／改写示例，请如实说明给定与自己构建部分。

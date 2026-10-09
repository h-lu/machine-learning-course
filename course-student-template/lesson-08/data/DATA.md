# 第 8 课数据、模型与结果说明

## 真实主任务：一行代表什么

`../../data/bike/hour.csv` 是UCI提供的Capital Bikeshare 2011–2012逐小时租借记录，本课程保存官方原始字节。17,379行、17列，无空字段、无重复日期小时；完整时间网格少165小时，**未记录不是零租借**。本课不补造行，不把公开数据说成学生调查。

固定时间切分：训练日期 `<2012-07-01` 为13,003行；验证 `[2012-07-01,2012-10-01)` 为2,208行；测试 `>=2012-10-01` 为2,168行。程序默认只报告前两部分误差，不报告测试预测。

| 原字段 | 意义与本课使用 |
|---|---|
| `dteday`、`hr` | 记录日期和0–23小时；合并成唯一时间；hr为可比较表示的输入 |
| `cnt` | 当小时记录租借总次数，预测目标；不代表没有车时未满足的需求 |
| `casual`、`registered` | 非注册与注册租借组成项，每行相加=cnt；禁作输入，避免答案泄漏 |
| `instant` | 记录编号，禁作业务输入 |
| `yr`、`mnth`、`weekday` | 年份编码、月份、星期类别；日历特征，weekday=0至6 |
| `holiday`、`workingday` | 是否假日、是否工作日，0/1编码；工作日需结合周末与假日定义 |
| `weathersit` | 官方天气类别1–4；基础输入使用类别指示变量，数字不是天气大小 |
| `temp`、`atemp` | 已归一化的温度与体感温度，不能把0.5直接说成0.5摄氏度；本课用temp，不重复放atemp |
| `hum`、`windspeed` | 已归一化的湿度、风速，本课作为基础输入 |
| `season` | 官方季节数值1–4，仅审计分组。本地Readme与官网文字标签有冲突，保留season_1至season_4，不静默改译 |

天气4仅3条，全部在训练中，验证和测试没有该组记录。无样本误差不可评估。实际天气可用于**当小时给定天气的条件估计**；提前一天用途要改用天气预报版本并重新验证。

来源、作者、DOI、CC BY4.0和字节审计见 [LICENSE_AND_SOURCE](../../data/bike/LICENSE_AND_SOURCE.md)。数据SHA-256为 `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`。

## 人工热身

本目录 `base.json` 有24条人工排队记录，12训练/6验证/6测试。只用它解释null、训练均值和一致处理。warmup读取训练的9个已知人数，均值13/9，用给定 `1+2×人数` 规则追踪训练C04，不报告toy测试分数，不是今天的标准模型实验。

## 开放起点与自己的实现

默认analysis.py调用load_development，仅返回训练与验证行和审计，不返回最后测试标签。它计算训练cnt均值作为必要基线，candidate_predictions默认为None，因而没有正式候选对照。可在该函数自行实现预测列表，或返回 `{自定方法名: 预测列表}`；也可另写自己的入口。

候选函数收到训练输入、训练cnt列表和评价输入。评价输入已排除cnt、casual、registered、instant，不能让目标进入预测；训练自己的处理参数后沿用到评价。默认不会替你选择失败组、输出诊断或写报告。

基线默认artifacts/baseline中：comparison.csv字段split/method/n/mae，records.csv含datetime/hr/workingday/weathersit/mnth/cnt/method/prediction/err_signed/err_absolute，summary说明training_n、baseline_training_mean和starter_only；data_audit只元数据。默认重跑只更新自己的四项科学产物。自主方案需要在报告说明新增输出和字段，并改自己的run/artifacts清单，不能只提交基线宣称完成。

最后评价可以在自己保存的报告／选择文件之后调用load_test(root,decision_path)读取测试，再由自己的程序只评价所选方法；loader只要求已保存非空选择记录，不强统一方法菜单或数字规则。它不替你证明记录质量，也不自动拟合或选择。开放起点已留显式test命令参数，默认验证不调用它；先完成自己的候选实现与选择再用。

## 可选示例工具：两项配置怎样比较

| 配置 | 原方案kind | 候选kind |
|---|---|---|
| `config-hour-onehot.json` | `hour_numeric` | `hour_onehot` |
| `config-workingday-interaction.json` | `hour_onehot` | `workingday_interaction` |

共有天气／日历／归一化天气数值输入相同。连续hr被替换为23个小时指示列，省略0点参照；交互路线只增加23个小时指示×workingday列。不是同时换模型和数据。

该示例算法固定为普通最小二乘回归，`ridge_alpha=0`，非零不允许。每列中心与总体标准差只从训练学习，验证和测试沿用；零标准差以1处理。可能有冗余日历列，保存设计矩阵的秩与列数；单个系数不当作唯一因果效果。两方案都把负线性预测截为0。

通勤组固定为workingday=1且hr属于7、8、9、16、17、18、19。没有实测通勤者身份，不能称“通勤人群”。需求尾部分组的阈值只从训练目标计算。其他参数含 `condition_hour_shift`（模拟小时登记偏移，模型不重训）等，保存于config-used；使用该示例作单因素比较时不同时调整它们；自主方案可选择其他合理处理，说明控制条件。

## 可选示例工具的结果格式

1. `comparison.csv`：split,method,kind,n,overall_mae,commute_n,commute_mae。`overall_mae`全体平均，`commute_mae`固定组平均，单位次租借／已记录小时。
2. `records.csv`：datetime、split、cnt、hr、workingday、分组字段、method、prediction、err_signed（预测−真实）、err_absolute（绝对差）。同一时间两方法两行是配对预测，不是独立加倍样本。
3. `group_metrics.csv`：dimension/group/method/n/mae等。无样本n=0，指标CSV空白、JSONnull，status=unavailable；不是零误差。
4. `feature_trace.csv`：固定取评价期第一条工作日时段组记录，保存每列原值、训练center/scale、转换值、权重和贡献；截距加各贡献后负数置0。它是核算起点，不替你作全部诊断。
5. `models.json`：feature_names、center、scale同序；weights第0项截距，之后对应各特征；design_rank/design_columns说明秩与列数。
6. `condition_check.json`：小时登记偏移敏感性检查，固定真实cnt和参数，不是改变现实时间的因果效果。

`metrics.json`与`summary.json`内容相同，保存训练／验证或测试指标；`error_cases.csv`每方法最多12条最大错误供诊断起点；`data_audit.json`审计行、缺小时、组成恒等式等，不含默认测试误差。`config-used.json`、`preregister-used.json`、`source_manifest.json`保存真实配置、预登记、源码／数据与产物哈希及环境。

显式结果目录只能新建，拒绝覆盖独立证据。省略output时默认artifacts/run只重建本课科学产物，用于主验证重现；它不打开测试，不覆盖chosen-validation/test。没有成功信息时不要把旧文件当新结果；不要手改生成的分数、记录或哈希。报告引用路径、字段、分母与命令。程序不会自动写报告或把status改为complete。

## 可选示例工具的完整调用资料

只有采用这个工具接口时才需要以下JSON文件；主任务的自由计划／选择不受其硬规则限制。命令在学生根目录运行；python3可替换python。hour-onehot是一个示例，另一示例换成config-workingday-interaction.json。

```bash
python scripts/lesson08.py preregister --config lesson-08/config-hour-onehot.json --output lesson-08/example-preregister.json
```

生成后亲自填primary_metric（overall_mae或commute_mae）、hypothesis、explanation、check_reason，以及check_rule的minimum_primary_improvement和maximum_secondary_mae_increase两个非负数，单位次租借／记录小时。保留自动config哈希。该工具要求候选主要误差降幅超过前者且副指标升幅不超过后者；它不会给你填写值，不能代表所有自主决策规则。

```bash
python scripts/lesson08.py bike --config lesson-08/config-hour-onehot.json --preregister lesson-08/example-preregister.json --output lesson-08/artifacts/example-validation
python scripts/lesson08.py decision --validation-run lesson-08/artifacts/example-validation --output lesson-08/example-decision.json
```

decision生成后填selected_method和具体验证reason，保留自动路径与哈希，再只评价已选方法：

```bash
python scripts/lesson08.py bike --config lesson-08/config-hour-onehot.json --unlock-test --decision lesson-08/example-decision.json --output lesson-08/artifacts/example-test
```

显式结果目录必须新建，不覆盖旧证据；示例工具test只报告所选方法。示例仍不自动完成自己的设计、独立检查、建议或报告。若你采用／改写示例，请如实说明给定与自己构建部分。

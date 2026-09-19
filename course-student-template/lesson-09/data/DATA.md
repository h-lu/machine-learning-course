# S07 数据、配置与阅读表格

180 条数据由课程脚本生成，没有真实业务含义，也没有现实单位。120 条 `split=train` 用于训练；其余 60 条 `split=evaluation` 用于开发比较。它不是另外留出的最终测试集，本课不支持 `--split`。不要复制 S01–S06 的数据或配置到这里。

| 字段 | 本课怎样使用 |
|---|---|
| id | 样本编号，阅读表用它对应原记录 |
| x1、x2 | 两个无量纲数值特征，都参与线性回归 |
| target | 回归要预测的真实值，也是人工生成的标签 |
| split | train 训练；evaluation 开发评价 |
| group | 人工分组，仅供观察残差，不作为拟合特征 |
| label | 公共数据读取接口还要求此列；本课回归不使用该二分类标签 |
| score、user、time | 其他课使用的兼容字段，本课不需要据此作判断 |

不要把 `label` 当成本课回归目标；真正使用的是 `target`。修改数据时同时确认读取接口，不只换列名。

## 三个配置字段

| 参数 | 含义 |
|---|---|
| seed | 随机种子，默认 7；本课对固定数据的拟合没有随机步骤，改变它不会重新生成数据 |
| ridge | 系数平方惩罚强度，非负；0 为普通最小二乘，正数为岭回归，截距不惩罚 |
| extrapolation_distance | 给评估输入的 x1 加多少，用于人工范围外情境；不改变 x2 |

`config-start.json` 是起点，`config-support.json` 只把 `ridge` 从 0 改为 10。`config.json` 用于最后的默认重跑；自己的改动另存 `config-mine.json`。完整步骤见 [SUPPORT.md](../SUPPORT.md)。

## 输出从哪里看

| 文件 | 先读哪些列 |
|---|---|
| comparison.csv | method_name 方法名、n 样本数、mae；unit 为无量纲 |
| records.csv | id、x1、x2、actual 真实值、prediction 预测值、baseline_prediction 基线预测 |
| records.csv | residual_actual_minus_prediction 为真实值减预测值；absolute_error 是其绝对值；group 为观察分组 |
| extrapolation.csv | original_x1、shifted_x1、x2、prediction、synthetic_target、outside_training_x1 |
| summary.json | metrics 为线性模型指标，comparison.training_mean 为均值基线，details.coefficients 按截距/x1系数/x2系数排列 |

同一个评估样本的回归与基线在 `records.csv` 同一行，不是两份不相关数据。外推表单独列出人工对照标签，`outside_training_x1` 只检查 x1 是否超过训练最小/最大值，不证明二维输入落在训练分布中。CSV 的 True/False 分别表示是/否。

外推对照使用已在 [LEARN.md](../LEARN.md) 声明的非线性公式，不是观测结果。距离改变后，输入和对照标签都可能改变，不能把两个距离的 MAE 当成同样本性能竞赛。所有误差均无量纲，不是分钟、百分比或实际损失。

程序不自动选择模型或填写采用建议。改动配置后用新输出目录；出错时旧文件可能还在，不能冒充新结果。原 summary.json 的数值字段保留，新增 CSV 只供阅读与核对。

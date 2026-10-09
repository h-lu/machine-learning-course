# 第07课支持：按卡点选用，不是统一研究路线

## 卡在环境、目录或第一份输入

如果只是想查看输入结构，从学生仓库根进入`cd lesson-07`，运行`python3 analysis.py --config config.json --output artifacts/start-a`。成功后先看`artifacts/start-a/summary.json`的训练/验证条数，再看sample.csv的一行输入；04只元数据，05额外固定时间清单。audit.json提供文件完整性。样本只是预览，不替代完整真实标准分析，起点没有全方案结果或报告。

## 卡在数据怎样进入自己的代码

你可修改analysis.py或另写my_analysis.py。`load_development(ROOT)`只返回训练和验证字典列表及审计；你决定输入/模型/规则/指标/保存内容。代码可让AI协助生成，但先解释自己的问题和不能偷看什么。

```python
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]  # 文件在lesson目录中
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import load_development, mae, fit_simple_line, write_csv
train, validation, audit = load_development(ROOT)
print("已读取训练/验证记录：", len(train), len(validation))
# 在此构建你自己的标准分析；训练统计只来自train。
# write_csv输出你构造的记录，不会替你选择研究策略。
```

如果把这段存为本课`my_analysis.py`，在本课目录运行`python3 my_analysis.py`；应先看到训练/验证记录数13,003和2,208，再构建自己的分析。这些是薄工具，不要求调用全部函数；读取之外由你组织自己的程序。04的标准分析使用全文件时点元数据，避免测试目标统计。可按CODE_TOOLKIT查示例片段，但不能把完整参考当自己的选择。

## 卡在本课关系或失败解释

卡在选择时，只把候选编号/日期/hr/workingday等已知信息交给选择逻辑，先写计划再用被选标签；不要把全表cnt交给AI让它替你倒选。 用LEARN小例核概念，再回自己选的真实范围；HINTS只提供检查方向，不给统一结论。默认起点无抽样策略、学习曲线或标签揭示答案。公开CSV含标签，课堂先选择是实验协议不是保密机制；预算回放不等于新真实采集。

## 卡在怎样保存与重跑

为每个比较保留配置、原始结果和运行命令；自己的程序建议写新试验目录，避免覆盖旧证据。report格式可改，引用具体文件/列/编号。更新submission.json的run和artifacts后再check/ci；默认起点结果不会证明完成研究。若你的代码有随机性，保存seed及全部重复结果；生成原始响应先保存再确定性重算。

使用已准备的Python与NumPy，命令示例为本机`python3`；你原环境若使用`python`或`py`，统一用已经成功的启动命令，不安装新环境。默认起点离线读取`data/bike/hour.csv`，只准备审计/样本预览，不能作为正式分析已完成证据。AI可帮助提出问题、写代码、核算和解释，不收集prompt记录、不要求所有人同路线或强制逐人答辩。

数据/依赖错误保留命令、工作目录和完整报错；先用不同数据的完整小例继续理解，明确写未实跑，再找教师修复。显式输出已存在拒覆盖，换新目录保留旧证据。默认`artifacts/starter`可重算。学生正式程序与输出由自己确定；submission.json的run必须真实重建其artifacts中列出的科学结果。比较试验若未列入CI，另保存配置和独立重跑命令，不宣称CI全核。

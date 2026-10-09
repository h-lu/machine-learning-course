# 第05课支持：按卡点选用，不是统一研究路线

## 卡在环境、目录或第一份输入

如果只是想查看输入结构，从学生仓库根进入`cd lesson-05`，运行`python3 analysis.py --config config.json --output artifacts/start-a`。成功后先看`artifacts/start-a/summary.json`的训练/验证条数，再看`artifacts/start-a/sample.csv`的一行输入；本课的样本只含编号、时间和所属数据集等信息，不含租赁次数。`split_manifest.csv`列出开发数据中每条记录属于训练还是验证。`audit.json`记录文件行数、空字段、重复时点和缺失小时等检查结果。样本只是预览，不替代使用真实数据的完整标准分析，起点没有全方案结果或报告。

## 卡在数据怎样进入自己的代码

你可修改`analysis.py`或另写`my_analysis.py`。`load_development(ROOT)`返回训练记录列表、验证记录列表和文件检查信息。每条记录是一个Python字典，用字段名取值；例如`train[0]["cnt"]`是第一条训练记录的租赁次数。输入、模型、规则、指标和保存内容由你决定。代码可让AI协助生成，但先解释自己的问题和不能偷看什么。

```python
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]  # 本程序放在 lesson-XX 目录中，ROOT 是学生仓库根目录
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import load_development, mae, fit_simple_line, write_csv
train, validation, audit = load_development(ROOT)
print("已读取训练/验证记录：", len(train), len(validation))
# 在此构建你自己的标准分析；训练统计只来自train。
# write_csv输出你构造的记录，不会替你选择研究策略。
```

如果把这段存为本课`my_analysis.py`，在本课目录运行`python3 my_analysis.py`；应先看到训练/验证记录数13,003和2,208，再构建自己的分析。这些是基础工具函数，不要求全部调用；读取后的分析由你组织。训练得到的统计量只用本方案的训练记录计算，不使用封存测试目标。可按[代码工具](../docs/CODE_TOOLKIT.md)查示例片段，但不能把完整参考当自己的选择。

## 卡在概念理解或失败原因

不知道从哪查时，先找2012-06-30/07-01/09-30边界记录；不知道参数来源时，保存参与拟合的编号与样本数。 用LEARN小例核概念，再回自己选的真实范围；HINTS只提供检查方向，不给统一结论。默认起点只给固定开发时间清单，不生成随机/回归完整答案。泄漏重构若自行展示应命名INVALID且不进入合法比较。

## 卡在怎样保存与重跑

`config.json`目前是空对象`{}`，不代表已经选定分析方法。你可以在自己的程序中定义并读取配置字段；只在配置中写入方法名称，不会让起点代码自动完成分析。`contract.json`记录研究问题（`question`）、使用者（`user`）、来源（`data_source`）、指标或审查规则（`metric`）、数据划分（`split_plan`）和观察结果前的预期（`initial_expectation`），请用自己的说明替换占位文字。

`submission.json`是提交清单：`report`是报告路径，`artifacts`是结果文件路径列表，路径都相对于学生仓库根目录；`run`是从该根目录执行的命令参数列表，例如`["python", "lesson-05/my_analysis.py"]`。`status`可为`not_started`（尚未开始）、`in_progress`（进行中）或`complete`（已完成）。

为每个比较试验保留配置、原始结果和运行命令；自己的程序建议写新试验目录，避免覆盖旧证据。`report.md`的结构可改，引用具体文件、列名和记录编号。更新`submission.json`的`run`和`artifacts`后，再运行README中的`check`和`ci`命令；默认起点结果不会证明完成研究。若代码有随机性，保存随机种子（`seed`）和每次重复的结果，便于重跑。如果使用AI生成的数据或回答，先保存原始输出，再用固定的程序计算指标。

使用已准备的Python与NumPy，命令示例为本机`python3`；你原环境若使用`python`或`py`，统一用已经成功的启动命令，不安装新环境。默认起点从学生仓库根目录的`data/bike/hour.csv`离线读取数据，只准备文件检查和样本预览，不能作为正式分析已完成证据。AI可帮助提出问题、写代码、核算和解释，不要求提交提示词记录、不要求所有人同路线或强制逐人答辩。

数据/依赖错误保留命令、工作目录和完整报错；先用不同数据的完整小例继续理解，明确写未实跑，再找教师修复。用`--output`指定的目录若已存在，程序会拒绝覆盖；请换新目录保留旧结果。不指定`--output`时，默认的`artifacts/starter`允许重新生成。正式程序和输出由你决定；`submission.json`中的`run`必须能重新生成`artifacts`列出的分析结果。未列入清单的比较试验，另存配置和重跑命令。

# 自己构建研究程序：代码工具

这些工具帮助你读取真实数据、核算误差和保存证据。它们不决定你的研究问题、方法、重要选择或结论，也不把一课的实验自动做完。你可以自由修改本课 `analysis.py`，或另写 `my_analysis.py`；可以借助 AI 编程，但需要解释自己的选择并核对结果。

## 从自己的程序导入

把文件放在 `lesson-XX` 目录，例如 `lesson-05/my_analysis.py`。下面只准备完整开发数据，不训练候选模型或生成报告：

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]  # 学生仓库根目录
sys.path.insert(0, str(ROOT))

from mlcourse.bike_starter import load_development

train, validation, audit = load_development(ROOT)
print("训练记录：", len(train))
print("验证记录：", len(validation))
print("第一条训练记录的字段：", list(train[0]))
# 在这里继续写你自己的研究程序。
```

从学生仓库根运行 `python3 lesson-05/my_analysis.py`；也可以先进入 `lesson-05`，再运行 `python3 my_analysis.py`。按自己已配置的环境使用 `python`、`python3` 或 `py`，无需为了这份程序更换原来的启动方式。若显示 `No module named mlcourse`，先检查文件是否放在课目录内，以及 `ROOT` 和 `sys.path.insert` 是否位于导入工具之前。

## 读取数据：`load_development`

`load_development(ROOT)` 返回三个对象：训练记录列表、验证记录列表、文件审计信息。每条记录是 Python 字典，例如可以用 `train[0]["temp"]` 读取第一条记录的标准化温度，用 `train[0]["cnt"]` 读取对应的实际小时租赁次数。

固定训练期为日期 `<2012-07-01` 的 13003 条记录；验证期为 `2012-07-01` 至 `2012-09-30` 的 2208 条记录。reader 不返回之后 2168 条测试记录的标签。`audit` 说明全文件有 17379 行、17 列；日历范围中缺 165 个小时记录，不能把缺行补成租赁次数 0。日期字段 `dteday` 和新增的 `datetime` 是字符串，其他官方数值字段是整数或浮点数。数据与来源说明见 [Bike 数据说明](../data/bike/LICENSE_AND_SOURCE.md)。

`cnt` 是要预测的标签，`casual + registered = cnt`。预测时不能把这三个字段作为输入。编号 `instant` 也不等于需求规律。你需要依据用途说明预测时已经知道哪些信息；当小时实际天气已知的需求估计，与前一天排班是不同任务。

工具不强制输入字段或方法菜单。如果改用其他数据，需要自己提供相应读取程序和来源说明；这个 reader 专门核对随包的官方 Bike 原件。

## 核算自己的预测：`mae`

```python
from mlcourse.bike_starter import mae

print(mae([10, 20, 30], [12, 17, 34]))  # 核对示例：3.0
```

MAE 是平均绝对误差：这里三条绝对差为 2、3、4，分母为 3。函数只核算你传入的两列，不自动选择模型或样本。实际值与预测值必须等长、非空、逐条对应同一批记录，并且都是有限数值。真实实验请传入自己的完整评价记录；不要把这个手算示例当成实验。

## 可选的简单直线：`fit_simple_line`

`intercept, slope = fit_simple_line(x, y)` 拟合一条 `intercept + slope * x` 的直线。你自己选择训练输入 `x` 和训练标签 `y`，两列等长且至少两条；输入没有变化时，无法据此学习斜率。函数不自动选列、切分、评价或与其他方案比较。直线只是可用的小工具，正式研究可以选择其他合理方法。训练参数时使用训练标签；不要把验证或测试标签混入拟合过程。

## 保存自己构造的证据：`write_csv` 和 `save_results`

`write_csv(path, rows, fieldnames=None)` 把你自行构造的字典行保存为 CSV。空记录列表需要给出 `fieldnames` 表头。它不生成预测或补造样本。

`save_results(output_dir, records, summary, fieldnames=None)` 把自己的记录和说明保存到新目录中的 `records.csv`、`summary.json`。记录列和说明内容由你决定，例如可以包含具体记录编号、输入条件、实际值、预测值、误差、方法名称和所作的重要选择。函数不计算比较结果或代写理由；既有目录会被拒绝，换一个名称可以保留每次实验的证据。

```python
from mlcourse.bike_starter import save_results

# records 和 summary 由你前面的研究代码构造；这里仅演示保存接口。
# 不要把未生成的结果或空报告当成完成。
save_results(ROOT / "lesson-05" / "artifacts" / "my-study-a", records, summary)
```

先运行自己的程序，打开文件核对具体记录，再按本课要求更新提交清单，使其指向自己的代码、真实产物和报告。默认数据起点的 `status: not_started` 只说明数据已经准备，不能证明研究已经完成。

## 最后才使用测试标签

只有本课明确要求最终测试评价时，才在验证完成、自己的方案已经选定后显式调用 `load_selected_test(ROOT, decision_path)`。`decision_path` 指向学生仓库内已经保存的非空决定文件，可以使用自由文字或 JSON；先记录选择、验证证据、理由和预期。函数只读取测试记录，不自动训练、评价或判断你的决定。`load_test` 是同一函数的另一个名称。

原始 CSV 公开，测试封存是研究协议与人工核查要求。工具不能保证别人无法直接读取原文件，也不能自动证明决定文件是在何时写成。看到最终测试结果后反复挑方案，会削弱结果作为独立评价证据的意义。

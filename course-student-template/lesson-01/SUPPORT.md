# 第01课支持卡：需要时查，不是统一实验流程

## 卡点：我还不能读取真实数据

在学生仓库根目录（有lesson-01、mlcourse、scripts）运行：

```bash
python3 lesson-01/analysis.py
```

使用自己的python/py启动命令也可。读取共享data/bike/hour.csv与本课config.json，将数据核对结果和结构预览写入 `lesson-01/artifacts/starter/`。先看sample.csv的instant（记录编号）、datetime（日期与小时）、partition（数据划分）：每行一个小时，train表示训练记录，validation表示验证记录。它只有6条训练和6条验证预览，不能替代标准项目完整评价。audit.json中的rows应为17,379，training_rows（训练条数）为13,003，validation_rows（验证条数）为2,208，sealed_test_rows（留到第08课评价的测试条数）为2,168。data_sha256是文件哈希，即根据文件内容计算的核对值，应与来源页一致。

默认起点没有整组预测、提醒或候选比较。只运行起点不等于标准项目完成。

## 卡点：我需要例题理解计算

[LEARN](LEARN.md)用不同情境人工小表给完整例题、半提示与独立练习。正式项目由你选择编号、参数、评价组和使用规则。本页不规定正式结果或结论。

## 卡点：我想自己写分析

可以在本课另建my_analysis.py，以下只读取开发数据（训练集和验证集，不含最后测试集）：

```python
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import load_development
train, validation, audit = load_development(ROOT)
print(len(train), len(validation))
# train/validation是由字典组成的列表，每个row字典是一条记录。
# row['temp']取归一化温度（不是摄氏度）；训练row['cnt']用于学习，验证row['cnt']用于核对。
# 在这里写你自己的规则、候选、检查与保存，不能只提交读取数量。
```

运行 `python3 lesson-01/my_analysis.py` 应只显示13,003和2,208。这只是工具起点，不是正式分析。mae(actual,predicted)帮助核算；write_csv保存自己构造的字典行；第02课可用fit_simple_line(x,y)拟合训练期一条直线。这些辅助函数不自动选字段、分组或方案。

## 卡点：配置、路径或软件报错

JSON用大括号保存字段和值，当前config.json为{}，表示没有设置参数；config-start.json和config-support.json也为空配置。你可保存自己的参数，代码必须实际读取它们；起点不会自动理解你的自定义字段。`python3 -m json.tool lesson-01/config.json`检查逗号与双引号。

另存起点可用：

```bash
python3 lesson-01/analysis.py --config lesson-01/config.json --output lesson-01/artifacts/starter-check
```

显式输出目录已存在则换名字，保留旧文件。命令在学生根的终端执行，不能写进Python的>>>。查看 [环境说明](../ENVIRONMENT.md)，不在课堂临时安装升级。保留完整报错；先用LEARN小表继续并标尚未运行，随后补跑。

## 卡点：我想保存自己的作品

report.md的结构可以重组。contract.json保留字段名，六个空字符串分别填写：

| 字段 | 填什么 |
|---|---|
| question | 你想回答的分析问题 |
| user | 谁使用预测结果；这里不是软件账号 |
| data_source | 数据来自哪里、使用哪个版本或文件 |
| metric | 怎样评价结果，写清指标或检查方法及单位 |
| split_plan | 哪些记录用于训练、验证，何时做最后测试 |
| initial_expectation | 运行前预计会看到什么及理由 |

submission.json的默认清单只对应起点。lesson保留本课课号；report填写报告路径；artifacts填写支持报告的实际结果文件路径列表。路径都从学生仓库根目录算起，例如`lesson-01/report.md`。run是按顺序拆开的命令参数列表：终端命令`python3 lesson-01/my_analysis.py`对应`["python3", "lesson-01/my_analysis.py"]`，不要把整条命令塞进一个字符串。将它改为自己的可重跑命令。

status可为not_started（未开始）、in_progress（进行中）或complete（完成）。完成项目后改为complete，再运行 `python3 scripts/course.py check 01`；它只检查文件，不证明分析完成。

用 `git add -f lesson-01/artifacts`保存结果，程序/配置也保存。CI只重新运行run中的命令并核对artifacts中的文件；其他试验给独立命令；不要只交截图。

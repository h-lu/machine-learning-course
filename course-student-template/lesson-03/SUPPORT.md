# 第03课支持卡：需要时查，不是统一实验流程

## 卡点：我还不能读取真实数据

在学生仓库根目录（有lesson-01、mlcourse、scripts）运行：

```bash
python3 lesson-03/analysis.py
```

使用自己的python/py启动命令也可。读取共享data/bike/hour.csv与本课config.json，将审计和结构预览写入 `lesson-03/artifacts/starter/`。先看sample.csv的instant、datetime、partition：每行一个小时，partition区分train/validation。它只有6条训练和6条验证预览，不能替代标准项目完整评价。audit.json核对rows=17,379，训练13,003、验证2,208、封存2,168；数据哈希与来源页一致（键名按产物）。

默认起点没有整组预测、提醒或候选比较。只运行起点不等于标准项目完成。

## 卡点：我需要例题理解计算

[LEARN](LEARN.md)用不同情境人工小表给完整例题、半提示与独立练习。正式项目由你选择编号、参数、评价组和使用规则。本页不规定正式结果或结论。

## 卡点：我想自己写分析

可以在本课另建my_analysis.py，以下只读取开发数据：

```python
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import load_development
train, validation, audit = load_development(ROOT)
print(len(train), len(validation))
# train/validation是由字典组成的列表，每个row字典是一条记录。
# row['temp']取温度；训练row['cnt']用于学习，验证row['cnt']用于核对。
# 在这里写你自己的规则、候选、检查与保存，不能只提交读取数量。
```

运行 `python3 lesson-03/my_analysis.py` 应只显示13,003和2,208。这只是工具起点，不是正式分析。mae(actual,predicted)帮助核算；write_csv保存自己构造的字典行；第02课可用fit_simple_line(x,y)拟合训练期一条直线。薄工具不自动选字段、分组或方案。

## 卡点：配置、路径或软件报错

JSON用大括号保存字段和值，当前config.json为{}。你可保存自己的参数，代码必须实际读取它们；起点不会自动理解你的自定义字段。`python3 -m json.tool lesson-03/config.json`检查逗号与双引号。

另存起点可用：

```bash
python3 lesson-03/analysis.py --config lesson-03/config.json --output lesson-03/artifacts/starter-check
```

显式输出目录已存在则换名字，保留旧文件。命令在学生根的终端执行，不能写进Python的>>>。查看 [环境说明](../ENVIRONMENT.md)，不在课堂临时安装升级。保留完整报错；先用LEARN小表继续并标尚未运行，随后补跑。

## 卡点：我想保存自己的作品

report.md提示可重组，contract六字段填任务与预计。submission默认清单只对应起点，完成时须改为自己的程序命令和实际证据路径，保持课号与字段。status改complete后 `python3 scripts/course.py check 03`，它只检查文件，不证明分析完成。

用 `git add -f lesson-03/artifacts`保存结果，程序/配置也保存。CI只重算提交清单，其他试验给独立命令；不要只交截图。

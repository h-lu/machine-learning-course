# 从一次更新，到两条训练曲线

命令在学生仓库根目录运行。继续使用第11课已准备的Python与NumPy，不下载新模型或数据。

## 1. 跑小例，先检查更新方向

```sh
python3 lesson-12/small_example.py
```

打开 `lesson-12/artifacts/small-example.json`，核对两条记录的p−y和乘x后的贡献。w梯度−0.5，b梯度0，学习率1使w更新为0.5，平均损失约从0.693147降至0.503204。这是人工两记录示范。

## 2. 跑一个真实SMS训练条件

先看 `lesson-12/config.json`。默认manual表示、lr=1、steps=400、l2=0.001、spam_weight=1、零初值、阈值0.5，容量比例1。

```sh
python3 scripts/course.py start 12
python3 lesson-12/analysis.py
```

输出在 `lesson-12/artifacts/baseline/`：

|文件|现在看什么|
|---|---|
|first_update.json|第一次更新前的系数、梯度、学习率、更新后系数与损失|
|curve.csv|每一步后的训练目标、训练BCE、开发BCE和追踪概率|
|loss.svg|训练与开发BCE的实际曲线|
|prediction_trace.json|最终一步的一条dev短信预测|
|summary.json、records.csv|最终指标与每条dev记录的概率、复核决定|

representation.json是训练得到的转换参数，model.npz是最终模型，config.json是本次实际设置。

默认垃圾短信权重为1。若把垃圾短信权重设为c、正常短信仍为1，梯度按记录权重求和，再除以全部训练记录的权重之和；L2项按原约定另加。为公平比较，本课不要同时改变权重与学习率。

## 3. 核对真实第一次更新

默认第一项是标准化后的字符数characters。运行：

```sh
python3 lesson-12/check_update.py --run lesson-12/artifacts/baseline --feature characters
```

工具重新读取全部train，按公式汇总一个坐标和截距，并与保存的第一次更新对照。first_update中的step=0表示“从尚未更新的第0步出发”，更新后对应curve中的step=1。应得到：

- 全体未除分母的贡献和约−483.523265，分母3877，梯度约−0.124716。
- 系数由0更新到约0.124716；截距由0更新到约−0.367939。
- 第一条train短信是sms-00001，其字符数坐标贡献约0.254499；这一项不能替代全部训练记录的和。

若采用bow或tfidf，`--feature`填写词表中一个实际词，或省略参数检查第一个坐标。词表名称在representation.json的names里。check_update输出核算过程，不修改训练结果。

`first_update.json`里默认 `objective_before`≈0.693147、`objective_after`≈0.462075，均是含正则的同一训练目标。`sample_p_after`只在人工特征的首次更新记录中出现，它描述第一条train记录；curve中的追踪概率描述第一条dev记录sms-00004，二者不同。

## 4. 怎样读曲线

默认curve的几个实际值如下，表内为约数：

|step|训练目标含正则|训练BCE|开发BCE|sms-00004概率|
|---|---:|---:|---:|---:|
|0|0.693147|0.693147|0.693147|0.500000|
|1|0.462075|0.461999|0.465767|0.338722|
|10|0.155289|0.154439|0.158281|0.084072|
|100|0.087941|0.083944|0.091370|0.015211|
|400|0.085874|0.080155|0.089150|0.010720|

loss.svg画的是train_bce与dev_bce，纵轴口径相同。`tracked_dev_probability`始终追踪该固定数据的第一条dev短信sms-00004；改变trace_id只改变最终prediction_trace，不改变这列追踪对象。

先看整个曲线，再看后期变化；不要只截取最低的一小段。单条正常短信的概率下降不能代表所有短信都改善，还要看records和整体指标。

## 5. 选一个变量，保存第二份配置

把config.json复制为 `lesson-12/my-config.json`。选择改变lr或steps中的一项，其他项保持相同，然后：

```sh
python3 lesson-12/analysis.py --config lesson-12/my-config.json --output lesson-12/artifacts/my-run
python3 lesson-12/compare_runs.py --first lesson-12/artifacts/baseline --second lesson-12/artifacts/my-run --output lesson-12/artifacts/comparison.csv
```

compare_runs检查数据、表示和配置，要求只改lr或steps，生成并列的最终损失与指标。它不替你选择设置或作出建议。如果使用自己的分析程序，也须说明同等比较条件。

计划沿用第11课某种表示时，把相同表示设置复制到两份配置，再各自训练；不要直接把TF–IDF换成人工特征后，将变化只归因于学习率。

若研究停止时机，用完整开发曲线选择候选步数，再以相同初值和其余设置重跑该步数，得到对应的最终模型与预测。最后一行始终是该次运行的末步，不能把末步model.npz当成更早最优步的模型。

## 6. 保存与提交

输出目录已有内容时，程序拒绝覆盖。新实验换目录，保留第一次方案与结果。

默认submission登记一次基线的9个文件。正式比较需要自己的重建脚本。例如保留两份配置后，可将以下结构写入 `lesson-12/my_study.py`，按自己的目录修改：

```python
import subprocess, sys
for config, output in [
    ('lesson-12/config.json', 'lesson-12/artifacts/study-a'),
    ('lesson-12/my-config.json', 'lesson-12/artifacts/study-b'),
]:
    subprocess.run([sys.executable, 'lesson-12/analysis.py',
                    '--config', config, '--output', output], check=True)
subprocess.run([sys.executable, 'lesson-12/compare_runs.py',
                '--first', 'lesson-12/artifacts/study-a',
                '--second', 'lesson-12/artifacts/study-b',
                '--output', 'lesson-12/artifacts/study-comparison.csv'], check=True)
```

在submission中把run改为 `["python3", "lesson-12/my_study.py"]`，artifacts列出两目录的所有生成文件及比较表。配置是输入，不列作生成产物。填写自己的报告与contract，完成后设complete再check。标记complete不会自动证明分析结论正确。

复现检查在临时副本中清除登记的输出再运行，原作业保留。沿用原标签和提交方式，不更改历史成绩。

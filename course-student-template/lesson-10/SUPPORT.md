# 第10课 · 卡住时看这里

## 我看不懂英文短信

可以按记录ID找到原文，请AI解释意思。但模型仍然接收同一段原英文；如果把译文换进去，输入已经改变，就不是本课固定模型概率下的比较。

不要点击短信中的网址或拨打号码。它们只是历史文本。

## 我先看哪个结果文件？

先看summary.json，知道当前复核了多少条、四类结果各是多少；再看records.csv，查某一条的probability与action。最后用prediction_trace.json核对一次计算。

文件名看起来多，但本课不要求分析训练曲线或第一次梯度更新。那些输出供后续课程使用。

## 如何读取固定概率？

在学生仓库根目录运行Python，或在自己的分析脚本里读取：

```python
import csv
from pathlib import Path

path = Path("lesson-10/artifacts/baseline/records.csv")
with path.open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

print(rows[0]["id"], rows[0]["probability"])
```

CSV读出的数字通常先是字符串。计算时要用float将probability转成数值；label等于spam时记作1，否则记作0。

## 只改行动规则，需要重新训练吗？

不需要。已经保存的概率足够比较阈值和容量。

mlcourse.sms_course中的actions接受概率、ID、阈值和容量比例；metrics接受标签、概率和行动，返回四类计数与指标。可以在自己的脚本中调用它们，也可以自己写清楚相同规则。

不要直接修改records.csv中原有的action列来冒充第二次模型输出。保存自己的新名单、设置和汇总，保留原结果。

## 不想另外写程序，也能比较两种规则吗？

可以。保留原来的config.json，复制一份命名为my_rule.json，只修改其中一个设置：

- threshold：概率门槛，例如0.5表示至少50%；
- capacity_fraction：容量比例，例如0.10表示最多复核整批的10%，条数向下取整。

其余训练设置保持原样。随后运行：

```bash
python3 lesson-10/analysis.py --config lesson-10/my_rule.json --output lesson-10/artifacts/my-rule
```

这种方式会重新运行相同的确定性训练过程。比较前核对两份records.csv的ID与probability一致，再比较action和summary。若概率也变了，就不只是行动规则发生变化。

也可以复用第一次的概率自己写分析，两条路线都可以。复制文件和指定新输出目录是为了保留原结果，不是要求多交一份作品。

## 怎样查一条预测？

在dev.csv按id找原文；用六项规则取得原始特征，再使用representation.json里的mean与scale标准化。

按照prediction_trace.json中的feature_names顺序，逐项计算 $x\times weights$ ，再加intercept，应该得到logit。对logit使用逻辑函数，应该得到probability。

显示的小数可能经过舍入，最后几位有小差异不一定是错误；核算应尽量使用文件中的完整数值。

## 达到阈值，却没有入选

先看容量。本课先筛出达标记录，再按概率取前若干条。名额满后，其他达标记录也不会入选。

还要看容量比例是按整批记录数计算，并向下取整。例如807条记录、比例0.10，容量是80条，不是81条。

## 程序说输出目录已经存在

这是为了保留旧结果，不是让你删除比较证据。换一个新的目录：

```bash
python3 lesson-10/analysis.py --output lesson-10/artifacts/baseline-02
```

若只是比较阈值，直接复用旧概率通常更清楚。

## 怎样选指标？

至少先列四个计数，确保相加等于这批记录总数；TP+FP等于复核总数，TP+FN等于真实垃圾总数。

随后解释查准率和召回率。它们不是越多小数越有说服力，关键是分母与实际后果。零分母应标为未定义，不能自行填成100%。

## 正式作品是不是运行默认程序就够了？

还不够。起点只提供一个固定模型和一种默认行动。你要说明自己的关注点，构建两个可比较的安排，核对真实预测，并解释取舍。

把自己的运行命令及实际输出写入submission.json；报告、设置、比较表应属于同一次分析。最终留出数据不参与本课选择。


## 一个可反复重建的双方案骨架

如果选择“固定概率，只改复核设置”，可以使用下面的骨架。先把自己的两个安排保存为 `lesson-10/my-rules.json`，示例只改变门槛：

```json
{
  "first": {"threshold": 0.5, "capacity_fraction": 1.0},
  "second": {"threshold": 0.3, "capacity_fraction": 1.0}
}
```

示例数值不替你决定关注点与成本。可以改为只比较容量，但应解释为何选这两个设置。

将下段保存为 `lesson-10/my_analysis.py`。它先重建一次固定模型，再将同一批概率交给两个安排，保存各自名单与比较表。临时目录避免与历史实验冲突。

```python
from pathlib import Path
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.sms_course import actions, metrics, write_csv

LESSON = ROOT / "lesson-10"
DEST = LESSON / "artifacts" / "rebuild"
FILES = ("config.json", "representation.json", "summary.json", "model.npz",
         "records.csv", "prediction_trace.json", "first_update.json", "curve.csv")
rules = json.loads((LESSON / "my-rules.json").read_text(encoding="utf-8"))
if set(rules) != {"first", "second"}:
    raise ValueError("Provide first and second rules")
for rule in rules.values():
    if set(rule) != {"threshold", "capacity_fraction"}:
        raise ValueError("Use threshold and capacity_fraction")
changed = [key for key in rules["first"]
           if rules["first"][key] != rules["second"][key]]
if len(changed) != 1:
    raise ValueError("Change exactly one review setting")

with tempfile.TemporaryDirectory(prefix="lesson10-") as temporary:
    fresh = Path(temporary) / "model"
    subprocess.run(
        [sys.executable, str(LESSON / "analysis.py"),
         "--config", str(LESSON / "config.json"), "--output", str(fresh)],
        cwd=ROOT, check=True,
    )
    target = DEST / "model"
    target.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(fresh / name, target / name)

with (target / "records.csv").open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
if any(row["label"] not in ("ham", "spam") for row in rows):
    raise ValueError("Expected ham/spam labels")
ids = [row["id"] for row in rows]
probability = np.array([float(row["probability"]) for row in rows])
truth = np.array([int(row["label"] == "spam") for row in rows])
comparison = {"partition": "dev", "changed": changed[0], "schemes": {}}
for name, rule in rules.items():
    selected = actions(probability, ids, **rule)
    result = [dict(row, action=int(action)) for row, action in zip(rows, selected)]
    write_csv(DEST / f"{name}-records.csv", result)
    comparison["schemes"][name] = {"settings": rule,
        "metrics": metrics(truth, probability, selected)}
for filename, value in (("rules.json", rules), ("comparison.json", comparison)):
    (DEST / filename).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

先连续执行两次，核对同一输入下产物可重建：

```sh
python3 lesson-10/my_analysis.py
python3 lesson-10/my_analysis.py
```

原baseline与其他历史目录不会被覆盖。新 `first-records.csv` 和 `second-records.csv` 使用同一组ID与probability，只重新计算action；原模型的records保留在rebuild/model中。

在 `submission.json` 中把run改为 `["python3", "lesson-10/my_analysis.py"]`，登记模型目录的8个文件，加rules.json、comparison.json和两份名单，共12个产物。可用以下代码列出路径，检查后填入artifacts：

```python
import json
names = ["config.json", "representation.json", "summary.json", "model.npz",
         "records.csv", "prediction_trace.json", "first_update.json", "curve.csv"]
paths = [f"lesson-10/artifacts/rebuild/model/{name}" for name in names]
paths += [f"lesson-10/artifacts/rebuild/{name}" for name in
          ("rules.json", "comparison.json", "first-records.csv", "second-records.csv")]
print(json.dumps(paths, ensure_ascii=False, indent=2))
```

my-rules.json是输入，rules.json是这次输出保存的设置快照，不要混淆。完成自己的报告与contract后再设complete，并按README检查和提交。骨架不会替你解释两种安排的取舍，也不打开最终留出数据。

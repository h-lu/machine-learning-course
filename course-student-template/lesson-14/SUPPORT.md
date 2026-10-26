# 第14课｜运行帮助

以下命令在学生仓库根目录执行，沿用已有Python与NumPy环境。预训练表示的缓存和本地模型沿用第13课；新文本编码依赖见[运行准备](../lesson-13/SUPPORT.md#运行前准备)。

## 1. 先完成开发实验

```sh
python3 lesson-14/analysis.py
```

默认使用TF–IDF，输出在 `lesson-14/artifacts/baseline/`。也可以沿用第13课已有结果。单独尝试新条件时，将配置另存后运行：

```sh
python3 lesson-14/analysis.py --config lesson-14/my-config.json --output lesson-14/artifacts/my-run
```

每次新实验使用新的输出目录，避免覆盖历史证据。manual、bow、tfidf沿用第11、12课字段；pretrained从第13课配置起步，不带词表构建参数。

### 保存两个比较条件

下面示范“固定表示，只改变训练步数”。先把 `lesson-14/config.json` 复制为 `old-config.json` 和 `new-config.json`，再只将new中的steps从400改为800。可在仓库根目录用Python完成：

```python
from pathlib import Path
import json
root = Path("lesson-14")
config = json.loads((root / "config.json").read_text(encoding="utf-8"))
for name, steps in (("old", 400), ("new", 800)):
    path = root / f"{name}-config.json"
    if path.exists():
        raise FileExistsError(f"Keep your existing configuration: {path}")
    current = dict(config, steps=steps)
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
```

这是操作示例，不是指定所有人研究训练步数。按自己的问题选择因素、预期与配置；若比较不同训练预算，应如实报告，不称预算相同。初始化配置只做一次，之后保留并编辑自己的文件。

## 2. 按证据顺序阅读输出

|文件|用途|
|---|---|
|config.json|本次训练与行动设置|
|representation.json|表示方法、词表或编码器信息|
|model.npz|分类器系数|
|summary.json|dev人数、指标与数据身份|
|records.csv|逐条dev概率、行动及标签|
|prediction_trace.json|一条记录的完整计算|
|first_update.json|第一次参数更新|
|curve.csv|训练过程|

1. 先在两份 `summary.json` 核对 `partition=dev`、`final_test_opened=false`，数据指纹及评价人数相同。
2. 按ID对齐两份 `records.csv`，核对标签，再比较概率与action。
3. 选择具体ID，到dev原文及 `prediction_trace.json` 追踪计算。若追踪的不是目标记录，在配置中用同一trace_id重跑开发实验。
4. 查看两份 `curve.csv` 与整体FP、FN等指标，将变化与预先的解释对照。

action以0/1表示是否送去复核；label用ham/spam表示真实类别，比较前将spam对应为1、ham对应为0。两者不一致记为本课行动错误。概率变化与行动变化要分开解释。

## 3. 可重复运行的开发脚本

将以下代码保存为 `lesson-14/my-analysis.py`。它在临时目录计算两个条件，把固定产物复制到专用 `artifacts/rebuild/`，并生成成对比较。它不读取最终留出，也不覆盖已定案系统。

```python
from pathlib import Path
import csv
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "lesson-14"
DEST = LESSON / "artifacts" / "rebuild"
FILES = (
    "config.json", "representation.json", "summary.json", "model.npz",
    "records.csv", "prediction_trace.json", "first_update.json", "curve.csv",
)
with tempfile.TemporaryDirectory(prefix="lesson14-") as temporary:
    for name in ("old", "new"):
        fresh = Path(temporary) / name
        subprocess.run(
            [sys.executable, str(LESSON / "analysis.py"),
             "--config", str(LESSON / f"{name}-config.json"),
             "--output", str(fresh)], cwd=ROOT, check=True,
        )
        destination = DEST / name
        destination.mkdir(parents=True, exist_ok=True)
        for filename in FILES:
            shutil.copyfile(fresh / filename, destination / filename)

runs = {}
for name in ("old", "new"):
    with (DEST / name / "records.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    indexed = {row["id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("Duplicate record IDs")
    runs[name] = indexed
if set(runs["old"]) != set(runs["new"]):
    raise ValueError("Compare the same development records")

counts = {"both_correct": 0, "corrected": 0, "introduced": 0, "both_wrong": 0}
changes = []
for record_id in sorted(runs["old"]):
    old, new = runs["old"][record_id], runs["new"][record_id]
    if old["label"] != new["label"] or old["text_sha256"] != new["text_sha256"]:
        raise ValueError("Record identity or label changed")
    if old["label"] not in ("ham", "spam"):
        raise ValueError("Expected ham/spam labels")
    truth = int(old["label"] == "spam")
    before = int(old["action"]) != truth
    after = int(new["action"]) != truth
    group = ("both_wrong" if after else "corrected") if before else (
        "introduced" if after else "both_correct")
    counts[group] += 1
    if before != after:
        changes.append({"id": record_id, "change": group,
                        "old_probability": float(old["probability"]),
                        "new_probability": float(new["probability"])})
result = {"partition": "dev", "n": len(runs["old"]), "counts": counts,
          "old_errors": counts["corrected"] + counts["both_wrong"],
          "new_errors": counts["introduced"] + counts["both_wrong"],
          "changes": changes}
(DEST / "paired-comparison.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

连续运行两次，确认均成功：

```sh
python3 lesson-14/my-analysis.py
python3 lesson-14/my-analysis.py
```

固定数据、配置和环境时，产物应一致。脚本更新专用rebuild目录中的已知文件，不删除历史baseline、my-run、selected或教师返回文件。若研究因素不同，调整配置与必要分析，但保留同一数据的比较。

## 4. 完成比较后再保存选定系统

先根据dev证据决定选哪个方案，再执行一次定案。例如选new时：

```sh
python3 lesson-14/lock_system.py --run lesson-14/artifacts/rebuild/new --output lesson-14/artifacts/selected --reason "替换为自己的开发证据和选择理由"
```

若选择old、baseline或第13课结果，将run改为实际目录。理由应说明比较结果与成本，不写“因为模型更新”。

selected中有5个文件：model.npz、representation.json、config.json、summary.json、system_lock.json。最后一个记录文件、代码与数据身份，以及选择理由。它用于核对，不是阻止重新选择的技术锁，也不自动决定哪个方案最好。

保留该目录，不把定案命令放进每次重建的脚本。若尚未查看最终留出而确需重新开发，另存实验、记录改选理由；看过最终结果后作的修改则需要新的独立评价。换目录不能消除已经看过的信息。

## 5. 教师最终评价单独保存

将selected目录交教师。教师返回 `final_records.csv` 与 `final_result.json`，请在报告中记录对应系统、首次评价及结果限制，并将文件单独保存，例如 `lesson-14/artifacts/final/`。

日常开发脚本不调用教师最终评价，也不把最终结果用于重选门槛、容量或模型。若教师尚未返回文件，在报告中标明待评价，不编造最终数字。

## 6. 登记与提交

三类文件用途不同：

|材料|如何处理|
|---|---|
|开发重建产物|由my-analysis.py重建，登记到submission.json的artifacts|
|selected定案目录|保留所选版本和理由，随作品交教师，不反复覆盖|
|教师最终评价|单独保留，报告首次评价，不放入开发重建命令|

在 `submission.json` 中保留lesson与report等字段，将run字段设为：

```json
{"run": ["python3", "lesson-14/my-analysis.py"]}
```

这只是字段示例，不要覆盖整个提交文件。示例脚本生成两方案各8个文件，加paired-comparison.json，共17个开发产物。可用下面代码列出路径，核对后填写artifacts：

```python
import json
names = [
    "config.json", "representation.json", "summary.json", "model.npz",
    "records.csv", "prediction_trace.json", "first_update.json", "curve.csv",
]
paths = [f"lesson-14/artifacts/rebuild/{case}/{name}"
         for case in ("old", "new") for name in names]
paths.append("lesson-14/artifacts/rebuild/paired-comparison.json")
print(json.dumps(paths, ensure_ascii=False, indent=2))
```

输入配置和报告是重建所需材料，不是生成产物。自己的脚本若增加必要输出，也应登记并保证可重建。作品完成后设 `status=complete`，运行：

```sh
python3 scripts/course_l1314.py check 14
python3 scripts/course_l1314.py ci 14
```

ci在临时副本中重建登记的开发产物；检查通过不替代教师最终评价和报告判断。

## 常见问题

|现象|先检查什么|
|---|---|
|开发输出目录已存在|新实验另取目录；重复重建用上述临时目录脚本|
|比较人数或ID不一致|核对划分与数据身份，不直接逐行相减|
|概率变了、行动没变|检查是否跨过门槛及容量排序，分别报告两个变化|
|重复运行完全一样|默认训练是确定性的；这验证重建，不增加独立样本|
|selected已存在|保留已有选择证据，不把定案放进重建脚本|
|Stale code or data|核对代码和数据版本，重做开发，不手改指纹绕过检查|
|Inconsistent run settings|不要混用不同运行的配置、表示与模型文件|
|最终结果不支持开发预期|如实报告限制，不回流调参后仍称首次独立评价|

保留实际命令与报错，先处理具体问题，再重新核查结果。

# 操作与提交步骤

## 建立个人仓库

在课程模板页面点击“使用此模板”，以自己的账号创建个人私有仓库（例如 `machine-learning-2026-yourname`），复制页面显示的克隆地址。不要把密码、令牌或私钥提交到仓库，也不要把它们提供给 AI。

```bash
git clone 你的仓库地址
cd 你的仓库目录
git config user.name "你的姓名"
git config user.email "你的学校邮箱"
python --version
```

Python 需要 3.10 或以上。若使用 `python3`，把下文命令中的 `python` 换成 `python3`。额外依赖写入仓库根目录的 `requirements.txt`。

## 每课的流程

从仓库根目录执行（以下以第 3 课为例）：

```bash
python scripts/course.py start 03
python scripts/course.py run 03
```

先阅读 `lesson-03/README.md` 和 `lesson-03/LEARN.md`，再修改 `analysis.py` 完成 Core（必做任务）。在 `contract.json` 写明任务说明、使用者、数据、指标、划分办法和预计结果；在 `report.md` 记录分析、失败案例或条件变化，以及修改后的决定。

完成后在 `lesson-03/submission.json` 填写报告、结果文件和运行命令，并把 `status` 设为 `complete`：

```json
{
  "lesson": "lesson-03",
  "status": "complete",
  "report": "lesson-03/report.md",
  "artifacts": ["lesson-03/artifacts/evidence.csv"],
  "run": ["python", "lesson-03/analysis.py"]
}
```

路径和命令都相对于仓库根目录；`evidence.csv` 只是示例，请替换为你实际生成的文件。若使用其他程序或参数，照实修改 `run`。固定随机种子、排序和输出精度，让别人能得到相同的主要结果。

本地检查和提交：

```bash
python scripts/course.py run 03
python scripts/course.py check 03
git status
git add lesson-03 requirements.txt
git commit -m "完成第03课机器学习项目"
git push
git tag v2-l03-final
git push origin v2-l03-final
```

`ml-check` 和 Gitea Actions 会检查目录、字段、运行命令和结果是否可重现；它不会替你选择模型或判断结论是否适合使用。自动检查会在临时副本中移除列出的结果文件，再运行程序重新生成；原提交不受影响。图表也应提交，但包含生成时间的文件不必列入逐字节比较清单。

## 补交与作品修订

项目在下一次课开始前补齐，仍可获得项目完成部分的补交分。修订代表作品时保留原 `v2-l03-final` 标签，在报告末记录改了什么及其依据，再创建 `v2-l03-revision-1`、`v2-l03-revision-2` 等标签。修订用于代表作品质量评价，不改变原版本的按时完成记录；详细规则见[成果与评分](ASSESSMENT.md)。

# 操作与提交步骤

## 建立个人仓库

在课程模板页面点击“使用此模板”，以自己的账号创建个人私有仓库（例如 `machine-learning-2026-yourname`），复制页面显示的克隆地址。不要把密码、令牌或私钥提交到仓库，也不要把它们提供给 AI。

```bash
git clone 你的仓库地址
cd 你的仓库目录
git config user.name "你的姓名"
git config user.email "你的学校邮箱"
python3 --version
```

Python 需要 3.10 或以上。下文以 `python3` 为例；如果已准备的环境使用 `python` 或 `py`，替换命令开头即可，具体见[环境说明](../ENVIRONMENT.md)。额外依赖写入学生仓库根目录的 `requirements.txt`。

目录和任务字段见[第一次运行指南](FIRST_RUN.md)，提交内容见[提交说明](SUBMISSION.md)。下面以第03课演示命令；用于其他课时，将课次、路径和标签中的编号改为实际课次。

## 运行与提交示例

从仓库根目录执行（以下以第 3 课为例）：

```bash
python3 scripts/course.py start 03
python3 scripts/course.py run 03
```

`start` 把本课的提交状态设为 `in_progress`（进行中）；`run` 执行 `submission.json` 中记录的命令。默认命令只运行数据起点，不会完成研究。

阅读本课 `README.md` 的课堂任务，按需要查阅 `LEARN.md`、`SUPPORT.md` 和 `HINTS.md`。你可以修改 `analysis.py`，也可以另写程序。在 `contract.json` 写明任务说明和看结果前的预计；在 `report.md` 记录分析、失败案例或条件变化，以及自己据此作出的决定。

完成后在 `lesson-03/submission.json` 填写报告、结果文件和运行命令，并把 `status` 设为 `complete`。下面假设你已经修改 `analysis.py`，使它重新生成自己的 `evidence.csv`；默认数据起点不会生成这个文件：

```json
{
  "lesson": "lesson-03",
  "status": "complete",
  "report": "lesson-03/report.md",
  "artifacts": ["lesson-03/artifacts/evidence.csv"],
  "run": ["python3", "lesson-03/analysis.py"]
}
```

路径和命令都相对于学生仓库根目录；`evidence.csv` 只是示例，请替换为你实际生成的文件。若使用其他程序或参数，照实修改 `run`；命令中的每一部分分别写成一个列表元素。使用随机过程时固定并记录随机种子；同时固定结果的排序和输出精度，让别人能得到相同的主要结果。

本地检查和提交：

```bash
python3 scripts/course.py check 03
python3 scripts/course.py ci
git status
git add lesson-03 requirements.txt
git add -f lesson-03/artifacts/evidence.csv
git diff --cached --name-only
git commit -m "完成第03课机器学习项目"
git push
git tag v2-l03-final
git push origin v2-l03-final
```

`artifacts/` 默认被忽略；上面的 `git add -f` 显式加入报告需要的结果。将 `evidence.csv` 换成当课实际文件，并在暂存列表里核对。`check` 和 `ci` 都是本地检查，不表示已上传。

本地的 `course.py check` 检查提交状态、报告和清单列出的结果文件是否存在且非空，不会重跑实验。`course.py ci` 不带课号，扫描当前可用课次清单中的全部课次：跳过 `not_started`，按清单运行 `in_progress`，对 `complete` 进行自动复现检查。

复现检查在一次性的临时副本中移除清单列出的结果文件及因此变空的结果目录，再执行 `run` 中的命令，逐文件比较重新生成的内容。目录里未列入清单的文件会保留，原提交也不受影响。Gitea Actions（仓库的自动检查服务）也使用这个命令；按课次标签触发时，只检查对应课次。检查不会替你选择模型或判断结论是否适合使用。

在自己的工作目录直接重跑使用 `--output` 或保存函数 `save_results(...)` 的程序时，仍要选择新目录以保留旧证据。通过 `course.py run` 重跑时，先在 `submission.json` 的 `run` 列表中更新输出参数，或修改研究程序实际读取的输出配置；相应更新 `artifacts` 的路径。`course.py run` 不会自动清空已有目录。正式结果的重建由上述 `ci` 临时副本完成。

图表也应提交；包含生成时间等每次都会变化的文件，可以随仓库保存而不列入逐字节复现的 `artifacts` 清单。若程序要求输出目录尚不存在，应把该目录中每次生成的文件完整列入清单，并把输入、手写记录或不做逐字节比较的文件放在其他目录；否则临时副本保留的文件会使这个目录无法重新创建。线上 ml-check 用于概念检查，另见[概念检查说明](KNOWLEDGE_CHECK.md)。

## 补交与作品修订

项目在下一次课开始前补齐，仍可获得项目完成部分的补交分。修订代表作品时保留原 `v2-l03-final` 标签，在报告末记录改了什么及其依据，再创建 `v2-l03-revision-1` 标签。这个标签标明修订版本，不增加计分机会；每模块的一次质量修订机会和截止期限见[成果与评分](ASSESSMENT.md)。修订不改变原版本的按时完成记录。

# C01–C02：第一次运行、改参数和提交

这页只解释两节入门课需要的文件操作，不要求先学会 Python 或 Git。先由教师确认你拿到的是本班指定版本。需要时查阅本页，再回到当课任务，不必先背术语表。

## 先找到运行命令的位置

**终端**是输入命令的窗口，不是 Python 文件。用编辑器打开课程文件夹，再打开终端。输入下面的命令，每行输入完按回车；不要复制代码框外的文字。

```bash
python --version
```

应显示 Python 3.10 或以上。若电脑只认 `python3`，后续每条命令都用 `python3` 代替 `python`。都不能运行时请教师协助准备环境，不要在课堂临时下载多个 Python 版本。

**学生仓库根目录**指能同时看到 `lesson-01`、`lesson-02`、`mlcourse`、`scripts` 和 `requirements.txt` 的文件夹。若你打开的是完整 GitHub 仓库，先进入其中的 `course-student-template`；若下载的本来就是学生模板，就不要再进入一次。运行下面的检查：

```bash
python -c "from pathlib import Path; print(Path.cwd()); print(Path('scripts/course.py').is_file())"
```

第一行是当前文件夹，第二行应为 `True`。若为 `False`，说明终端所在位置不对；先进入上面描述的文件夹，再继续。教师可在课前用 `python -m pip install -r requirements.txt` 安装依赖；学生用 `python -c "import numpy; print(numpy.__version__)"` 检查是否可用。出现 `No module named numpy` 时先解决环境问题，不修改实验数据。

## 文件分别用来做什么

| 文件 | 你需要做什么 |
|---|---|
| `README.md` | 按顺序阅读当课任务和命令 |
| `LEARN.md` | 用小例子理解术语与计算 |
| `data/base.json` | 查看样本，字段含义见同目录 `DATA.md` |
| `config.json` | 用文本编辑器修改参数，保存后才会生效 |
| `analysis.py` | 本课程序入口；可请 AI 解释或修改，不需要在终端粘贴整份代码 |
| `artifacts/` | 程序产生的结果文件夹，不是输入文件 |
| `report.md` | 把提示问题替换成自己的分析，可直接写中文段落 |
| `contract.json` | 课程的任务说明文件，不是新的机器学习概念；填写方法见下表 |
| `submission.json` | 说明交哪些文件、怎样重跑；不是实验参数 |

**JSON** 是用“字段名：值”保存信息的文本格式。使用英文双引号 `"`、冒号 `:` 和逗号 `,`；文字放在双引号中，数值不加引号，最后一个字段后不加逗号。不要插入注释或省略号。文件名不要多出 `.txt`。

保留原文件时，用编辑器“另存为”创建副本。新文件应与原文件放在同一课次文件夹中。`--config` 后面写配置文件路径，`--output` 后面写结果文件夹路径；这些不是单独运行的命令，要接在 `python lesson-01/analysis.py` 等完整命令后面。

## 怎样填写任务说明和报告

打开本课 `contract.json`，保留字段名，只把右侧空字符串 `""` 改成自己的中文说明。不要改 `lesson` 的值。

| 字段 | 用自己的话回答 |
|---|---|
| `question` | 想预测什么，结果准备怎样使用？ |
| `user` | 谁会使用这个结果？ |
| `data_source` | 数据来自哪里？例如这两课使用人工教学数据，不是真实调查。 |
| `metric` | 怎样核对结果？C01 可说明一条预测的绝对误差；C02 说明 MAE 及其单位。 |
| `split_plan` | 哪些数据做什么？C01 只核对样本、不训练；C02 分别说明训练集、验证集和测试集。 |
| `initial_expectation` | 运行前预计会怎样，理由是什么？不要事后把实际结果冒充原来的预期。 |

可以检查 JSON 格式。例如在第 01 课运行：

```bash
python -m json.tool lesson-01/contract.json
```

成功时它会显示文件内容，但不修改文件；报错时按行号检查引号、逗号等。第 02 课把路径换为 `lesson-02/contract.json`。

在 `report.md` 保留标题，把开头的填写说明和各个问题替换成自己的回答。不要只在模板最后附上答案而留下所有待填提示。写出实际使用的命令和结果路径；参考例子可以帮助理解，不能代替自己的选择。

## 怎样确认提交包含结果

完成实验、报告和任务说明后，在 `submission.json` 中只将 `"status": "in_progress"` 改为 `"status": "complete"`。两课默认清单都列出本课 `artifacts/summary.json` 和 `artifacts/predictions.csv`。其他文件位置未改时，保留默认路径和 `run` 命令。不要修改结果文件里的 `example_only`。

运行当课 `check` 后，仍需将文件提交到个人仓库。**`artifacts/` 默认被 Git 忽略，仅执行 `git add lesson-01` 会漏掉结果**。下面的 `git add -f` 是明确选中需要提交的结果，不是把所有临时文件都加入仓库。

第 01 课第一次提交，在学生仓库根目录依次运行：

```bash
python scripts/course.py check 01
git status
git add lesson-01
git add -f lesson-01/artifacts/summary.json lesson-01/artifacts/predictions.csv
git diff --cached --name-only
git commit -m "完成第01课入门实验"
git push
git tag v2-l01-final
git push origin v2-l01-final
```

第 02 课第一次提交，确认已按课内步骤生成最终结果和验证阶段材料，再运行：

```bash
python scripts/course.py check 02
git status
git add lesson-02
git add -f lesson-02/artifacts/summary.json lesson-02/artifacts/predictions.csv
git add -f lesson-02/artifacts/validation/summary.json lesson-02/artifacts/validation/predictions.csv
git diff --cached --name-only
git commit -m "完成第02课模型比较"
git push
git tag v2-l02-final
git push origin v2-l02-final
```

在 `git diff --cached --name-only` 的输出中确认有报告、任务说明、配置和上述结果。原本已提交且未变化的文件不会重复列出。报告引用了其他试验目录或改过共享代码时，还要逐个加入对应文件，不提交密码、令牌、个人数据或环境目录。验证阶段文件作为过程材料提交，不必改变默认结果清单；报告同时给出重算命令。

从 ZIP 解压的文件夹可能没有 Git 仓库，报 `not a git repository` 时请按 [操作与提交步骤](WORKFLOW.md) 建立个人仓库，或按教师安排先保存本地成果。推送失败不等于实验失败，不要把失败写成已提交。已有同名标签时不要强行覆盖，修订办法也见该页。

## 报错时先看哪里

找不到 `analysis.py`：检查当前文件夹和命令中的课次。找不到配置副本：检查“另存为”的位置和文件名。JSON 格式错误：检查英文标点。新人数被拒绝：区分负数等无效输入和超出已见人数的合法输入。

输入检查失败后，应修正配置再跑。旧输出可能仍在原目录，不能当成本次成功的结果。不要为了“通过检查”编造实际等待时间。环境和网络故障可请教师协助或按安排补做。

# 第11课首次使用

使用前面课程已建立的学生仓库，按[环境说明](../ENVIRONMENT.md)确认 Python 和 NumPy 可用。尚未建立仓库时，从[学生发布仓库](https://hblu.top/gitea/machine-learning-2026/course-student-release-2026)创建并克隆自己的私有仓库。

在自己的学生仓库 `main` 工作树根目录操作。若缺少 `lesson-11/`，先取得本课材料：

```sh
(
  set -eu
  lesson11_helper=$(mktemp)
  trap 'rm -f "$lesson11_helper"' EXIT
  git fetch ssh://git@hblu.top:2222/machine-learning-2026/course-student-release-2026.git main
  git show FETCH_HEAD:scripts/course_l11.py > "$lesson11_helper"
  python3 "$lesson11_helper" sync --destination "$PWD"
)
```

开始本课并运行起点程序：

```sh
python3 scripts/course.py start 11
python3 lesson-11/analysis.py
```

起点程序生成一份人工特征基线，结果在 `lesson-11/artifacts/baseline`。接着按[本课任务](../lesson-11/README.md)选择两套表示进行比较；每次实验使用新的输出目录。

完成作品后，按[提交流程](WORKFLOW.md)登记报告、运行命令和产物，再检查与提交：

```sh
python3 scripts/course.py check 11
```

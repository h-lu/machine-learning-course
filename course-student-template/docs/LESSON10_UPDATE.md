# 第10课更新与检查

教师确认第10课已发布后，在已有学生仓库根目录执行。更新助手写入临时文件，不覆盖旧的 scripts/course.py；已有课目录整课跳过，支持文件只补缺，同名共享代码不兼容时停止。

```sh
(
  set -eu
  lesson10_helper=$(mktemp)
  trap 'rm -f "$lesson10_helper"' EXIT
  git fetch ssh://git@hblu.top:2222/machine-learning-2026/course-student-release-2026.git main
  git show FETCH_HEAD:scripts/course_l10.py > "$lesson10_helper"
  python3 "$lesson10_helper" sync --destination "$PWD"
)
```

更新后运行：

```sh
python3 scripts/course.py start 10
python3 scripts/course.py run 10
```

完成自己的分析，填写实际报告、运行命令和结果文件，将 submission.json 状态设为 complete，再运行：

```sh
python3 scripts/course.py check 10
```

本地检查核对提交接口，不代替分析质量评价，也不表示服务器检查已经通过。重复运行需要保留旧结果；机器学习请选择新输出目录并同步修改实际 run 和 artifacts。

按照现有提交流程提交自己的改动和实际产物。第10课更新使用本页新助手，无需执行旧第09课更新说明中的覆盖 scripts/course.py 命令。正式选择题场次以教师明确开放为准，本次课包发布不会启用或改变场次。

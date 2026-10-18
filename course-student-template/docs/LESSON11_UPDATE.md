# 第11课更新与检查

本页随第11课课包准备，须等教师明确确认发布后再更新。在已有学生 Git 仓库根目录执行；只使用 `main` 发布线。助手只补缺少的第11课目录和必要支持文件，并在 `active_student_lessons` 末尾登记 `lesson-11`；不合并远端分支，不替换旧课、报告、结果、工作流或 `course.py`。

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

已有 `lesson-11/` 整个跳过，助手不补改个人课目录。既有短信训练集、开发集、分组清单及来源记录继续复用，不重新划分、不增加或开放最终评价集。同名执行模块或固定数据若与发布字节不同，助手会在新增文件前停止；保留个人版本，先核对其兼容性，不能用覆盖文件来掩盖差异。

查看 `git status`、`git diff` 与课次清单后，沿用现有运行入口：

```sh
python3 scripts/course.py start 11
python3 scripts/course.py run 11
```

本课新增的表示工具为 `mlcourse/text_representations.py`；旧 `sms_course.py`、旧课程序及评分接口不变。README 说明正式任务，LEARN 解释概念，SUPPORT 按卡点使用。学生仍需自行选择和比较表示、训练与用途，程序起点不会自动完成整个研究。

完成自己的工作后，在 `submission.json` 填写实际报告、运行命令与产物，将状态改为 `complete`，再检查与复现：

```sh
python3 scripts/course.py check 11
GITHUB_REF=refs/tags/v2-l11-final python3 scripts/course.py ci
```

现有 `course.py` 按课次清单读取第11课，无需替换程序或改写工作流。若自己的旧工作流使用其他入口，应先检查实际配置；本地复现成功不表示远端 CI 已通过。重复实验使用新输出目录，并相应修改实际 `run` 和 `artifacts`，保留已有证据。

按原提交流程提交自己的工作和成果，保留既有最终／修订标签。课包更新不会启用、替换或开放线上正式选择题场次，也不会重判旧记录。

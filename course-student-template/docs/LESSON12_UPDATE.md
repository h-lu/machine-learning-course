# 第12课材料与运行入口

沿用自己的学生仓库、Python 环境及第10–11课的 SMS 数据和工具。本课固定表示，比较训练设置。

## 已有学生仓库怎样取得材料

先保存并提交自己的作业。尚未设置 course-release 时，先按仓库首页添加该远端。在仓库根目录运行：

```sh
git fetch course-release main
if [ -e lesson-12 ] || [ -L lesson-12 ]; then
  echo "保留已有第12课目录，不覆盖个人内容。"
else
  git restore --source=course-release/main -- lesson-12 docs/LESSON12_UPDATE.md
fi
python3 -c "import json; from pathlib import Path; p=Path('active_lessons.json'); c=json.loads(p.read_text()); a=c['active_student_lessons']; a.append('lesson-12') if 'lesson-12' not in a else None; p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')"
```

这一步只登记第12课，不替换前课清单。查看 git status 和 git diff，按原流程提交新材料。

## 开始与提交

```sh
python3 scripts/course.py start 12
python3 lesson-12/analysis.py
```

先读本课 README 和 SUPPORT，完成两套训练设置的比较后，再运行 python3 scripts/course.py check 12，并按原流程提交 v2-l12-final 标签。在线检查题以教师开放的场次为准。

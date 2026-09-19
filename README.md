# 现代机器学习课程

这是面向 AI 时代的项目制机器学习课程资料库。课程按 16 周、32 次课组织，学生可以使用 AI 完成编程、计算、分析与写作，但需要对问题定义、评价方式、结果依据和适用条件负责。

## 当前材料状态

C01–C02 和 S01–S06 已提供成套候选材料；S01–S07 有详细入门指导，S07 保留现行线性回归实验并修订概念题。其余课次未按新地图完成重写。合并源码不等于班级启用或生产服务升级，教师需指定匹配的材料与题库版本；详见[本次审核记录](course-instructor/reviews/premerge-review-2026-09-19.md)。

## 目录

- `course-instructor/`：教师课程标准、32 课设计、运行手册、概念检查题库与参考材料。
- `course-student-template/`：完整 32 课学生模板；实际 Gitea 学生仓库按教学进度逐课使用。
- `ml-check/`：课末机器学习概念检查服务，支持 Gitea 登录、A 版基础题、AI 学习、B 版变式题和教师统计。
- `machine-learning-course/`：课程地图、发布说明和整体规划入口。

## 课程设计入口

- [32 课学习地图](machine-learning-course/COURSE_MAP.md)
- [教师课程设计标准](course-instructor/COURSE_DESIGN.md)
- [教师评分标准](course-instructor/GRADING.md)
- [学生项目模板](course-student-template/README.md)
- [学生成果与评分说明](course-student-template/docs/ASSESSMENT.md)
- [学生概念检查说明](course-student-template/docs/KNOWLEDGE_CHECK.md)

## 本地运行检查

```bash
python3 tools/validate_course.py
PYTHONPATH=ml-check pytest -q ml-check/tests
```

生产环境的服务入口是 [ml-check](https://hblu.top/ml-check)，教师页面为 [ml-check/teacher](https://hblu.top/ml-check/teacher)。生产凭据和数据库不放入 Git；部署说明见 [ml-check/deploy/README.md](ml-check/deploy/README.md)。

## 发布仓库

- [GitHub 完整课程](https://github.com/h-lu/machine-learning-course)
- [Gitea 学生模板](https://hblu.top/gitea/machine-learning-2026/course-student-template)
- [Gitea 教师材料](https://hblu.top/gitea/machine-learning-2026/course-instructor)
- [Gitea ml-check](https://hblu.top/gitea/machine-learning-2026/ml-check)

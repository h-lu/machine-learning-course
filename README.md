# 现代机器学习课程

这是面向 AI 时代的项目制机器学习课程资料库。课程按 16 周、32 次课组织，学生可以使用 AI 完成编程、计算、分析与写作，但需要对问题定义、评价方式、结果依据和适用范围负责。

## 目录

- `course-instructor/`：教师课程标准、32 课设计、运行手册、知识自查题库与参考材料。
- `course-student-template/`：完整 32 课学生模板；实际 Gitea 学生仓库按教学进度逐课使用。
- `ml-check/`：课末机器学习知识自查服务，支持 Gitea 登录、A 版基础题、AI 学习、B 版变式题和教师统计。
- `machine-learning-course/`：课程地图、发布说明和整体规划入口。

## 课程设计入口

- [32 课学习地图](machine-learning-course/COURSE_MAP.md)
- [教师课程设计标准](course-instructor/COURSE_DESIGN.md)
- [教师评分标准](course-instructor/GRADING.md)
- [学生项目模板](course-student-template/README.md)
- [学生成果与评分说明](course-student-template/docs/ASSESSMENT.md)
- [知识自查设计](course-instructor/knowledge-check/DESIGN.md)

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

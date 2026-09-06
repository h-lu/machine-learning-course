# 课程发布

课程作者选择公开完整课程，包括学生任务、教师参考、参考检查和概念题答案。GitHub 仓库用于共享完整源码；Gitea 保留三个独立课程仓库，方便教学维护。

| 位置 | 内容 |
|---|---|
| [GitHub：h-lu/machine-learning-course](https://github.com/h-lu/machine-learning-course) | 32 课完整材料、128 道题和运行工具，公开 |
| [Gitea：course-student-template](https://hblu.top/gitea/machine-learning-2026/course-student-template) | 学生课包、数据和实验工具 |
| [Gitea：course-instructor](https://hblu.top/gitea/machine-learning-2026/course-instructor) | 教师运行单、参考分析和题目答案 |
| [Gitea：ml-check](https://hblu.top/gitea/machine-learning-2026/ml-check) | 格式检查与概念题读取代码 |

## 发布办法

1. 从完整工作区运行 `python3 tools/validate_course.py`，检查学生实验、教师参考、题库与三个材料目录。
2. 提交三个独立仓库的改动，在 Gitea 为重建前提交保留归档标签，然后快进更新原默认分支。
3. 用 `python3 tools/export_public_release.py --output /path/to/new-empty-directory` 生成 GitHub 发布包。目录中保留完整新教材，排除嵌套 Git、旧版压缩包、环境与临时产物。
4. 在导出目录再次运行验证，再提交到 GitHub。发布后对照远程默认分支与本地提交，并从远程重新检出验证。

公开仓库中的教师答案不嵌入学生任务目录。学生应先作判断，再用 AI 和参考材料学习；项目仍按自己的实验、检查与理由评价。

本次发布指课程仓库及模板。`ml-check` 的读取服务源码一同发布，但仓库推送不表示登录、答题存储或生产服务已部署。

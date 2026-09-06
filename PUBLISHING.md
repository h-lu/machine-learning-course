# 课程发布

课程作者选择公开完整课程，包括学生任务、教师参考、参考检查和概念题答案。GitHub 仓库用于共享完整源码；Gitea 保留三个独立课程仓库，方便教学维护。

| 位置 | 内容 |
|---|---|
| [GitHub：h-lu/machine-learning-course](https://github.com/h-lu/machine-learning-course) | 32 课完整材料、128 道题和运行工具，公开 |
| [Gitea：course-student-template](https://hblu.top/gitea/machine-learning-2026/course-student-template) | 学生课包、数据和实验工具 |
| [Gitea：course-instructor](https://hblu.top/gitea/machine-learning-2026/course-instructor) | 教师运行单、参考分析和题目答案 |
| [Gitea：ml-check](https://hblu.top/gitea/machine-learning-2026/ml-check) | 格式检查与在线概念练习代码 |

## 发布办法

1. 从完整工作区运行 `python3 tools/validate_course.py`，检查学生实验、教师参考、题库与三个材料目录。
2. 提交三个独立仓库的改动，在 Gitea 为重建前提交保留归档标签，然后快进更新原默认分支。
3. 用 `python3 tools/export_public_release.py --output /path/to/new-empty-directory` 生成 GitHub 发布包。目录中保留完整新教材，排除嵌套 Git、旧版压缩包、环境与临时产物。
4. 在导出目录再次运行验证，再提交到 GitHub。发布后对照远程默认分支与本地提交，并从远程重新检出验证。

公开仓库中的教师答案不嵌入学生任务目录。学生应先作判断，再用 AI 和参考材料学习；项目仍按自己的实验、检查与理由评价。

课程仓库发布后，已于 2026-09-06 将概念练习服务部署到 [hblu.top/ml-check](https://hblu.top/ml-check)。覆盖 32 课、128 题，提供 A/B 两轮答题和提交后的解释；无需登录，不保存个人答题记录。服务器配置见 `ml-check/deploy/README.md`。

## 2026-09-06 发布记录

GitHub 公开仓库已创建，完整课程已推送到 `main`。从公开 HTTPS 地址重新克隆后，学生 19 项测试、检查器与 API 的 21 项测试、32 课教师参考覆盖及三个材料目录的严格检查全部通过。

本次课程内容初始提交为 [`38c117d26924`](https://github.com/h-lu/machine-learning-course/commit/38c117d26924a1e975550d2c16b6d5047c0a1fff)；后续提交补充发布记录。

| Gitea 仓库 | 默认分支 | 已核对的提交 | 可见性 |
|---|---|---|---|
| course-student-template | `main` | [`70d0eb9dbc69`](https://hblu.top/gitea/machine-learning-2026/course-student-template/commit/70d0eb9dbc691f5af8b6bf59d2ba7cd6b2f377fd) | 公开，保留模板标记 |
| course-instructor | `main` | [`988f21e532ed`](https://hblu.top/gitea/machine-learning-2026/course-instructor/commit/988f21e532ed72b92c44c7ac0835de2eaa5d1d41) | 保留原私有设置 |
| ml-check | `master` | [`eba461dd8a45`](https://hblu.top/gitea/machine-learning-2026/ml-check/commit/eba461dd8a45bff26caea36aa12429e5a5d5bb85) | 保留原私有设置 |

服务器上的默认分支提交与本地一致；三个仓库的 452 个已跟踪文件也逐文件与 GitHub 发布包比较一致。Gitea 各仓保留 `archive/pre-redesign-2026-09-06` 标签，指向重建前版本；没有强制推送或改写旧历史。

## 在线服务验收

新增页面与表单测试覆盖所有 32 课的 A/B 两轮、正确和错误回答、缺失答案、无效课次、静态样式和 HEAD 请求。全部 25 项检查器/HTTP 测试通过，课程整体严格验收通过。公网浏览器已实测首页、课次选择、提交与解释显示；Docker 健康检查和 HTTPS 入口正常。

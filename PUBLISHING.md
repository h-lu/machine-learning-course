# 课程发布

课程作者选择公开完整课程，包括学生任务、教师参考、参考检查和概念题答案。GitHub 仓库用于共享完整源码；Gitea 保留三个源仓库和一个学生发布仓库，方便教学维护。

| 位置 | 内容 |
|---|---|
| [GitHub：h-lu/machine-learning-course](https://github.com/h-lu/machine-learning-course) | 32 课完整材料、320 道 A/B 题和运行工具，公开 |
| [Gitea：course-student-template](https://hblu.top/gitea/machine-learning-2026/course-student-template) | 学生课包、数据和实验工具 |
| [Gitea：course-instructor](https://hblu.top/gitea/machine-learning-2026/course-instructor) | 教师运行单、参考分析和题目答案 |
| [Gitea：ml-check](https://hblu.top/gitea/machine-learning-2026/ml-check) | 格式检查与在线概念练习代码 |
| [Gitea：course-student-release-2026](https://hblu.top/gitea/machine-learning-2026/course-student-release-2026) | 2026 班学生直接使用的完整发布仓库 |

## 发布办法

1. 从完整工作区运行 `python3 tools/validate_course.py`，检查学生实验、教师参考、题库与三个材料目录。
2. 提交三个独立仓库的改动，在 Gitea 为重建前提交保留归档标签，然后快进更新原默认分支。
3. 用 `python3 tools/export_public_release.py --output /path/to/new-empty-directory` 生成 GitHub 发布包。目录中保留完整新教材，排除嵌套 Git、旧版压缩包、环境与临时产物。
4. 在导出目录再次运行验证，再提交到 GitHub。发布后对照远程默认分支与本地提交，并从远程重新检出验证。

公开仓库中的教师答案不嵌入学生任务目录。学生应先作判断，再用 AI 和参考材料学习；项目仍按自己的实验、检查与理由评价。

课程仓库发布后，已于 2026-09-06 将概念练习服务部署到 [hblu.top/ml-check](https://hblu.top/ml-check)，后续改为使用 Gitea 账号参与教师场次。当前服务覆盖 32 课、每课 A/B 各五题，共 320 题；历史发布记录保留在下文，当前题库与部署状态以[教师发布说明](course-instructor/RELEASE.md)为准。服务器配置见 `ml-check/deploy/README.md`。

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

新增页面与表单测试覆盖所有 32 课的 A/B 两轮、正确和错误回答、缺失答案、无效课次、静态样式和 HEAD 请求。全部 27 项检查器/HTTP 测试通过，课程整体严格验收通过。公网浏览器已实测首页、课次选择、提交与解释显示；Docker 健康检查和 HTTPS 入口正常。

## 2026-09-21 v13 发布记录

第 01–04 课已经完成教学，本次没有修改其学生课件和作业要求。第 05–32 课按新课程主线成套更新；学生任务、教师材料、概念题、学生发布仓库和在线服务使用同一批内容。发布内容基线为 GitHub `fea7ab2144394876c8f07b7e3f7f5f38e7eebf99`，对应的 Gitea 提交为：

| Gitea 仓库 | 提交 |
|---|---|
| course-student-template | `f0807a400e6ebe32ae37f771016e1b5d617937f9` |
| course-instructor | `19a1d2a1670517ddd6b62484cc94c773cddf8bf8` |
| ml-check | `e7bf5a0f043270456a3190fbb67bf2b847e47d16` |
| course-student-release-2026 | `4f7406faa10e3f8072f51c2b98af0dab21eb6af7` |

学生发布仓库保留通用首页和已授课的第 01–04 课原内容；第 05–32 课、`docs`、`mlcourse` 和 `scripts` 与学生模板逐文件一致。远程重新克隆后，32 课严格检查为 0 项问题，`run 05`、`run 32` 和整仓 `ci` 均通过。

题库版本为 `ml-v13-course-map-2026-09-21`，文件 SHA-256 为 `537bf31972b8cb3655f1cd1e9fcd245ea7bf6713ae3187d899e4c4e446c9720f`，包含 32 课、160 个知识点和 320 道成对的 A/B 题。整仓统一验证的八组检查全部通过：学生实验 131 项，教师参考 32 课共 117 项独立核算，教师脚本 15 项，`ml-check` unittest 81 项，三个材料目录严格检查均通过；独立 pytest 复核也是 81 项通过。另在全新学生副本中实际执行第 05–32 课共 151 条操作命令和最终整仓 `ci`，均成功。以上是模拟冷读和命令实跑，不是真人学生 90 分钟试读。

生产服务在 2026-09-21 18:33:59–18:34:03 UTC 切换到 `ml-check:2026-09-21-v13`。切换前后的用户、场次、作答和学习完成记录分别保持为 64、4、1649、169；SQLite 完整性和外键检查通过。四个已结束场次保存其原题库快照：C01 为 v4、C02 为 v6、S01 和 S02 为 v11，因此新题不会改变已经完成的练习和解释。数据库备份为 `/home/ubuntu/ml-check/data/ml-check.before-v13-20260921T182552Z.sqlite3`，旧源码和 compose 备份为 `/home/ubuntu/ml-check/backups/source-before-v13-20260921T182552Z.tar.gz`，旧镜像与三份历史题库继续保留。

切换前先在 8897 隔离实例验证了历史场次、新建 v13 场次、课次编号和 AI 学习页；学习页只显示知识点与学习说明，不显示 A/B 题干。切换后容器为 healthy，本机和公网健康接口均返回 32 课及 v13，公开登录页返回 200。

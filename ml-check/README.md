# ml-check：课程材料检查与概念练习

本仓库同时提供两项功能：`ml_check` 命令检查 32 课材料的结构、路径和 Python 语法；FastAPI 服务为课堂提供 A 版判断、AI 学习、B 版换情境判断和教师统计。当前源码题库为 `ml-v14-s03-readability-2026-09-22`，共 32 课、320 道题。

2026 班第 01–04 课已经完成，历史场次继续读取创建时使用的题库快照。当前题库只用于以后新建的场次，不会重新解释旧作答。首次部署快照功能和本轮生产切换按 [部署说明](deploy/README.md) 操作。

## 检查课程仓库

在 `ml-check` 目录运行。结构检查需要 Python 3.10 以上；运行 Web 测试还需安装 `requirements.txt`。

```bash
python3 -m ml_check --repo ../course-student-template --profile student --strict
python3 -m ml_check --repo ../course-instructor --profile instructor --strict
python3 -m ml_check --repo ../machine-learning-course --profile planning --strict --json
python3 -m unittest discover -s tests -v
```

退出码 0 表示相应自动检查通过。学生仓库的 `scripts/course.py run/ci` 会执行课程程序；`ml_check` 本身不执行学生提交，也不评价报告结论。结构、关键词和语法检查不能证明文案易懂、实验正确或学生能在 90 分钟内完成，这些仍需命令实跑、教师审阅和真人试读。

## 在线概念练习

访问 [ml-check](https://hblu.top/ml-check)，使用 Gitea 账号登录。教师在 `/ml-check/teacher` 创建场次并依次开放 A、学习、B 和结果阶段；学生在 `/ml-check/current` 进入当前场次。每个页面标题显示“第 NN 课（Cxx/Sxx）”和课名，避免只看内部编号。

每课有五个知识点，每个知识点对应一对 A/B 题：

- A 版先独立判断；
- AI 学习阶段只显示知识点标题和学习说明，不显示或复述 A/B 题；
- B 版换一个情境检查同一概念；
- A、学习、B 默认分别为 240、300、240 秒，另留约 2 分钟提交。

题号使用 `C01-A-01`、`S07-B-05` 这样的稳定格式。教师题库保存答案和解释；学生读取接口在作答前只返回题干与选项。参与情况与正确率用途不同，具体计分以课程评分说明为准。

## 本地运行服务

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8896
```

本地服务通过 `DATABASE_PATH` 使用 SQLite。生产还要配置 `SESSION_SECRET`、Gitea OAuth、`TEACHER_LOGINS`、公开地址和安全 Cookie，示例见 `.env.example`；密钥和数据库不得提交到 Git。

主要页面和接口保留 `/ml-check` 前缀：

- `/ml-check/`：入口；
- `/ml-check/current`：学生当前场次；
- `/ml-check/teacher`：教师控制、进度、历史统计和 CSV；
- `/ml-check/healthz`：服务、题库和历史快照健康状态；
- `/ml-check/api/lessons` 与 `/ml-check/api/lessons/{lesson_id}`：兼容的题库读取接口。

旧匿名凭据和课次读取接口继续保留兼容。新建场次会保存该课完整题干、选项、答案、解释、学习说明、计时和题库版本；历史页面、统计和反馈都从场次快照读取。任何旧场次缺少或损坏快照时，健康检查会失败，部署人员应先修复映射，不能直接换题库。

## 题库来源与发布

教师源题位于完整 GitHub 课程仓库的 [`course-instructor/lessons`](https://github.com/h-lu/machine-learning-course/tree/main/course-instructor/lessons)。在完整工作区根目录使用下面的命令生成服务汇总文件：

```bash
python3 tools/sync_question_bank.py
```

生成后仍需人工核对 A/B 是否检查同一概念、B 是否真正换情境、学习说明是否没有泄露题干，以及术语和干扰项是否清楚。生产部署还要核对题库文件 SHA-256、数据库数量、旧场次快照、新场次完整流程和 HTTPS 健康接口；详见 [部署说明](deploy/README.md) 与 [教师发布说明](https://github.com/h-lu/machine-learning-course/blob/main/course-instructor/RELEASE.md)。

# ml-check：检查材料，帮助发现概念误解

**本分支使用候选题库 `ml-v7-intro-2026-09-19`，未部署到生产服务。**新 C01–C02 的材料和题目需要按班级版本一并采用；旧场次不得直接切换当前题库。

本工具检查 32 课材料是否齐全、学生说明是否可读、提交文件是否有效、结果路径能否找到，以及 Python 代码是否有语法错误。它不运行学生提交命令，也不按指定模型、指标分数或采用结论判分。

模板状态与项目完成分开：`template` 可通过课程材料结构检查；`complete` 还需要填写任务说明、写报告并提供实际结果文件。能否据此支持学生的建议，仍需教师阅读和实验核对。

## 检查课程仓库

在本目录运行。材料结构检查仅需 Python 3.10 以上；运行包含 Web 服务的测试集，还需预先安装 `requirements.txt` 中的依赖：

```bash
python3 -m ml_check --repo ../course-student-template --profile student --strict
python3 -m ml_check --repo ../course-instructor --profile instructor --strict
python3 -m ml_check --repo ../machine-learning-course --profile planning --strict --json
python3 -m unittest discover -s tests -v
```

退出码 0 表示结构检查没有错误；严格模式还会将警告视为失败。工具不通过搜索“开放”等关键词证明教学质量。是否存在实质自主选择，需要对照任务和参考分析阅读。

## 在线概念练习

访问 **https://hblu.top/ml-check**，使用 Gitea 账号登录。教师在 `/ml-check/teacher` 创建场次并切换 A、学习、B 阶段；学生在 `/ml-check/current` 作答并查看解释。教师页面提供场次进度、统计和 CSV 导出，概念练习结果用于形成性评价，不直接替代项目报告评分。

## 概念题

32 课各有五个独立定义的知识点，每个知识点配一对 A、B 题，共 320 题。每题使用 `C01-A-01`、`S01-B-05` 这样的稳定编号，页面标题也直接显示课次编号。学生先完成 A 版判断；AI 学习阶段只看到知识点标题与学习说明，不会看到或复述 A、B 题；最后由教师开放 B 版换场景检验。题库版本为 `ml-v6-2026-09-16`。本版本继续使用完整小场景；C01、C02 还把记录对象、预测时点、分母、目标记录数量和人工处理容量直接写进题干，避免用“这些记录”“找回目标”等省略说法。题目答案与解释保留在教师/服务文件中；学生读取接口只返回题干与选项。

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8896
```

接口保留 `GET /ml-check/healthz`、`GET /ml-check/api/lessons` 和 `GET /ml-check/api/lessons/{lesson_id}`。页面入口为 `GET /ml-check/`，答题页面为 `GET /ml-check/lessons/{lesson_id}?phase=A`（或 B），核对提交为 `POST /ml-check/lessons/{lesson_id}/check`。提交后可通过 `GET /ml-check/api/receipts/{receipt_id}` 读取凭据。读取接口不会提前返回参考答案；凭据 API 也不会返回答案。

本地服务通过 `DATABASE_PATH` 配置 SQLite；部署时使用 `/data/ml-check.sqlite3`。生产环境还需设置 `SESSION_SECRET`、Gitea OAuth 客户端和 `TEACHER_LOGINS`，示例见 `.env.example`。旧匿名凭据 API 保留兼容，但新场次数据均按账号和场次持久化。

## 与旧版的关系

课次编号、检查命令的主要选项、HTTP 路径和 `contract.json`、`submission.json` 等文件名保留。任务字段精简为自然语言说明；提交清单允许学生更换运行入口与报告路径。JSON 内容为第 2 版接口，不能将旧前端直接视为兼容。

服务现使用 FastAPI、Session 和 Gitea OAuth，页面与 statistics-course 的 stat-check 保持一致；匿名 API 和旧答题路径继续可用。运行方式见 [部署说明](deploy/README.md)。

## C01–C02 候选题库版本

本分支重新同步后的题库版本为 `ml-v7-intro-2026-09-19`：只改写 C01–C02 的五知识点与 A/B 题，S01–S30 保留原题。上文 `ml-v6-2026-09-16` 为此前发布记录，不代表本分支候选已部署。健康接口的版本从题库文件读取，避免页面与文件各自维护不同版本号。

生产服务不在本次变更中切换。旧场次只记录课号且读取当前题库，不能在使用旧题的实例原地替换题库后宣称历史仍兼容；隔离实例、备份及班级版本安排按教师发布说明执行。

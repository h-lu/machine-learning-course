# hblu.top 部署

入口：https://hblu.top/ml-check

部署于服务器 `/home/ubuntu/ml-check`。容器 `machine-learning-ml-check` 只绑定主机 `127.0.0.1:8896`，由现有 `hblu-nginx-proxy` 提供 HTTPS。容器非 root、文件系统只读，`/data` 使用服务器目录保存 SQLite 场次、答题和凭据数据，题库随镜像发布。登录、教师场次控制和统计页面与 statistics-course 的 stat-check 一致；OAuth 密钥只放在服务器 `.env`。

## 更新

如果生产数据库还没有 `course_sessions.bank_json`，先执行下面的“首次启用场次题库快照”，不能直接重建容器。完成过快照迁移后，日常更新才使用本节命令。

将本仓库的 `app/`、`Dockerfile`、`.dockerignore`、`docker-compose.yml` 和 `deploy/` 同步到服务器目录，随后运行：

```bash
cd /home/ubuntu/ml-check
docker compose up -d --build
docker compose ps
curl --fail http://127.0.0.1:8896/ml-check/healthz
```

## 首次启用场次题库快照

每个新场次现在会保存当时的题干、选项、答案、解析、学习说明和计时。生产库中已有的四个场次跨越三份题库，不能用一份现行题库统一回填。`session-snapshot-map-2026-09-21.json` 明确绑定了场次 7/C01/v4、8/C02/v6、9/S01/v11 和 11/S02/v11，并校验原始题库文件的 SHA-256。

先在本地课程工作区根目录从历史提交导出 v4 和 v6：

```bash
HIST_BANK_DIR=/tmp/ml-check-session-banks-20260921
mkdir -p "$HIST_BANK_DIR"
git -C ml-check show 351dad01c26a9e36b37f8f6a05978761f8f22101:app/question_bank/lessons.json \
  > "$HIST_BANK_DIR/lessons-351dad0-ml-v4.json"
git -C ml-check show df707d90a621c712c551a951bd6f99871a1bb7be:app/question_bank/lessons.json \
  > "$HIST_BANK_DIR/lessons-df707d9-ml-v6.json"
sha256sum "$HIST_BANK_DIR"/*.json
```

预期哈希为：

```text
7b6e5968ce5fd1ef7ce99e83930fc5461cca41d2ea98568a121de12cb4d3d42b  lessons-351dad0-ml-v4.json
31552ecd340a6c8cc1ebb2434372892b5b01b6baff74e40c02e5f39123d99e16  lessons-df707d9-ml-v6.json
```

把这两份文件上传到服务器：

```bash
ssh -i /home/hblu/.ssh/id_ed25519 root@hblu.top \
  'mkdir -p /home/ubuntu/ml-check/data/session-banks'
scp -i /home/hblu/.ssh/id_ed25519 "$HIST_BANK_DIR"/*.json \
  root@hblu.top:/home/ubuntu/ml-check/data/session-banks/
```

生产 v11 是 2026-09-20 构建的现行镜像内容，与后来同版本名的 Git 文件不完全相同。**版本名相同仍必须核对整个文件的 SHA-256，不能用版本名代替内容校验。**在服务器上停止服务后，直接从保留的生产容器导出：

```bash
cd /home/ubuntu/ml-check
docker compose stop
mkdir -p data/session-banks
docker cp machine-learning-ml-check:/app/app/question_bank/lessons.json \
  data/session-banks/lessons-production-c044440b-ml-v11.json
sha256sum data/session-banks/lessons-production-c044440b-ml-v11.json
```

这份文件的预期哈希是 `c044440b1d2efe5a5f485632567502a758835004de334ae9f49e240e12cb7f81`。如果不符，不要继续。此时再同步新版 `app/` 和 `deploy/`，但不要删除 `data/session-banks/` 中的历史题库。先用场次映射做只读检查：

```bash
python3 deploy/backfill_session_snapshots.py \
  --database data/ml-check.sqlite3 \
  --session-map deploy/session-snapshot-map-2026-09-21.json
```

检查必须报告 4 个待回填场次和 4 个数据库场次。任何未知、遗漏、课号不符、版本不符或哈希不符都必须先调查，不要修改映射来绕过检查。然后指定一个尚不存在的备份文件并实际回填：

```bash
python3 deploy/backfill_session_snapshots.py \
  --database data/ml-check.sqlite3 \
  --session-map deploy/session-snapshot-map-2026-09-21.json \
  --apply \
  --backup data/ml-check.before-session-snapshots-20260921.sqlite3
```

脚本会拒绝覆盖已存在的备份，并在一个锁定写入的 SQLite 事务中回填所有场次。任何课号不匹配、已有快照损坏或中途异常都会整体回滚。重复运行映射时，已有快照必须与映射内容完全一致，脚本只验证而不覆盖。成功后再重建并检查健康接口：

```bash
docker compose up -d --build
docker compose ps
curl --fail http://127.0.0.1:8896/ml-check/healthz
```

健康接口会在任何场次缺少快照时返回失败。这种情况下不要继续切换题库；保留备份和旧题库，停止服务后检查回填报错。

`nginx-location.conf` 已加入现有 HTTPS server 块，路径保留 `/ml-check` 前缀。首次添加或更改代理时，先备份 `/home/ubuntu/medical-bid-review-codex-repo/infra/nginx-hblu-proxy.conf`，然后测试并重载：

```bash
docker exec hblu-nginx-proxy nginx -t
docker exec hblu-nginx-proxy nginx -s reload
curl --fail https://hblu.top/ml-check/healthz
```

首次部署前配置备份文件名为 `nginx-hblu-proxy.conf.before-ml-check-20260906192317`，与原配置同目录。需要撤销入口时恢复该备份，测试并重载 nginx，然后在服务目录运行 `docker compose stop`。之后若其他代理配置也已更新，应只移除本服务的两个 location 块，避免覆盖其他改动。

## 本轮 v13 切换检查

本轮镜像标签为 `ml-check:2026-09-21-v13`，题库版本为 `ml-v13-course-map-2026-09-21`。切换前先确认当前场次均为 `result` 或 `closed`，再记录 SQLite 的完整性以及用户、场次、作答、学习完成数量。服务目录中的 `.env`、生产数据库和历史题库不随源码同步删除。

首次回填后，至少核对：

```bash
cd /home/ubuntu/ml-check
python3 - <<'PY2'
import sqlite3
connection = sqlite3.connect("data/ml-check.sqlite3")
print("integrity", connection.execute("PRAGMA integrity_check").fetchone()[0])
for table in ("users", "course_sessions", "responses", "learning_completions"):
    print(table, connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
print(connection.execute(
    "SELECT id, lesson_id, phase, bank_version FROM course_sessions ORDER BY id"
).fetchall())
PY2

curl --fail http://127.0.0.1:8896/ml-check/healthz
curl --fail https://hblu.top/ml-check/healthz
```

健康接口必须报告 32 课和 `ml-v13-course-map-2026-09-21`。历史四个场次应分别显示 v4、v6、v11、v11；用户、作答与学习完成数量在切换前后保持一致。再检查首页、教师历史场次、学生当前入口、A/学习/B/结果、课次编号和 CSV 导出。AI 学习页只能显示五个知识点和学习说明，不能显示题干或答案。

新建场次后应保存 v13 快照；以后更新题库时，新场次使用新版本，已经创建的场次继续读取自己的快照。健康检查失败时不要创建课堂场次。

## 恢复

至少保留旧镜像、旧 compose 文件、迁移前 SQLite 备份、v4/v6/v11 历史题库和场次映射。需要恢复时先停止容器，同时恢复旧数据库与旧镜像配置，再启动并检查内外网健康接口。不能只恢复数据库或只切回镜像，因为两者必须匹配。

```bash
cd /home/ubuntu/ml-check
docker compose stop
cp data/ml-check.before-session-snapshots-20260921.sqlite3 data/ml-check.sqlite3
# 恢复备份的 docker-compose.yml 后再启动旧镜像
docker compose up -d --no-build
```

实际备份文件若使用带时刻的名称，以发布记录为准；恢复前不要覆盖唯一备份。Nginx 路径本轮不变，无需重载。若以后修改代理，先执行 `nginx -t`，只调整本服务的 location，避免覆盖其他站点配置。

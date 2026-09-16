# hblu.top 部署

入口：https://hblu.top/ml-check

部署于服务器 `/home/ubuntu/ml-check`。容器 `machine-learning-ml-check` 只绑定主机 `127.0.0.1:8896`，由现有 `hblu-nginx-proxy` 提供 HTTPS。容器非 root、文件系统只读，`/data` 使用服务器目录保存 SQLite 场次、答题和凭据数据，题库随镜像发布。登录、教师场次控制和统计页面与 statistics-course 的 stat-check 一致；OAuth 密钥只放在服务器 `.env`。

## 更新

将本仓库的 `app/`、`Dockerfile`、`.dockerignore`、`docker-compose.yml` 和 `deploy/` 同步到服务器目录，随后运行：

```bash
cd /home/ubuntu/ml-check
docker compose up -d --build
docker compose ps
curl --fail http://127.0.0.1:8896/ml-check/healthz
```

`nginx-location.conf` 已加入现有 HTTPS server 块，路径保留 `/ml-check` 前缀。首次添加或更改代理时，先备份 `/home/ubuntu/medical-bid-review-codex-repo/infra/nginx-hblu-proxy.conf`，然后测试并重载：

```bash
docker exec hblu-nginx-proxy nginx -t
docker exec hblu-nginx-proxy nginx -s reload
curl --fail https://hblu.top/ml-check/healthz
```

首次部署前配置备份文件名为 `nginx-hblu-proxy.conf.before-ml-check-20260906192317`，与原配置同目录。需要撤销入口时恢复该备份，测试并重载 nginx，然后在服务目录运行 `docker compose stop`。之后若其他代理配置也已更新，应只移除本服务的两个 location 块，避免覆盖其他改动。

## 检查

首页应显示 32 课；教师登录后可在 `/ml-check/teacher` 创建场次、切换 A/学习/B 阶段并导出 CSV，学生在 `/ml-check/current` 作答。每课有 5 个独立知识点及对应的 A/B 题；AI 学习页只显示知识点标题和学习说明。健康接口报告题库版本 `ml-v6-2026-09-16`，旧题库读取 API 和匿名答题路径仍保留兼容。

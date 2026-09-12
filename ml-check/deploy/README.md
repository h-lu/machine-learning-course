# hblu.top 部署

入口：https://hblu.top/ml-check

部署于服务器 `/home/ubuntu/ml-check`。容器 `machine-learning-ml-check` 只绑定主机 `127.0.0.1:8896`，由现有 `hblu-nginx-proxy` 提供 HTTPS。容器非 root、文件系统只读，`/data` 使用 Docker 数据卷保存匿名 A/B 完成凭据，自动随 Docker 重启，题库随镜像发布。

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

首页应显示 32 课、128 题；选择一课，提交两道 A 轮题，确认解释出现，再进入 B 轮。健康接口报告题库版本 `ml-v2-open-2026-09-06`。题库读取 API 保持原路径和字段。

服务不要求登录，不保存姓名或账号。提交会保存匿名凭据（课次、轮次、得分、时间和答案哈希），通过凭据 URL 可读取；答案本身不入库。常规访问日志包含请求路径，不记录表单内容；日志限制为 3 个 10 MB 文件。凭据仅供课末完成情况核对，项目分数仍按教师评分规则和提交快照评定。

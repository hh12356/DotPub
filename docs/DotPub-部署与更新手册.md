# DotPub 部署与更新手册

> 更新日期：2026-09-22（Docker + CI/CD 版）
> 服务器：阿里云 ECS · Ubuntu 24.04 · http://47.122.126.63 （**仅 IP，无域名，无 HTTPS**）

---

## 一、架构

```
浏览器 ──:80──> web 容器(nginx) ──/api/*──> backend 容器(uvicorn:8010) ──> db 容器(mysql:8.4)
```

三个容器由 `/opt/dotpub/docker-compose.yml` 编排，都 `restart: unless-stopped`（顶替了 systemd 的开机自启）。

**服务器的约束（整套设计的出发点）**：只做「拉镜像」和「跑容器」，**不构建、不访问 GitHub、不拉 Docker Hub**。

镜像存在**阿里云 ACR（杭州）**。宿主机原来的 nginx / mysqld / dotpub systemd 服务都已停用并禁用。

**安全组只开 22 和 80。** 8010 和 3306 必须保持关闭。

---

## 二、怎么更新

```bash
git add -A && git commit -m "改了什么" && git push
```

**完了。** GitHub Actions 自动：构建两个镜像 → 推 ACR → scp compose 文件 → 服务器 `pull + up -d`。

去 Actions 页面看结果。**绿了不等于部署成功了**，一定要用下面那条命令确认。

> 服务器不需要碰 GitHub，所以不用（也不能）在服务器上 `git pull`——国内到 GitHub 的 TLS 时通时断。

---

## 三、怎么确认部署成功

**本地**（拿到刚推上去的 sha）：

```bash
git rev-parse HEAD
```

**服务器**：

```bash
cd /opt/dotpub
docker inspect $(docker compose --env-file ./backend/.env ps -q web) --format '{{.Config.Image}}'
```

输出的 sha 必须和本地那个一致。

> 别在服务器上 `git rev-parse HEAD` 取这个值——`/opt/dotpub` 虽然是 git 克隆，但它拉不到 GitHub，HEAD 停在你最后一次手动同步的位置，**是旧的**。

> **别用「刷新页面看变化」判断部署成没成。** 浏览器会缓存旧 JS，旧容器也一直在正常返回 200——两者都会让你以为部署失败（或成功）。**镜像名是唯一不骗人的证据。**

---

## 四、回滚

```bash
cd /opt/dotpub
export IMAGE_TAG=<目标 sha>

docker compose --env-file ./backend/.env pull
docker compose --env-file ./backend/.env up -d

docker inspect $(docker compose --env-file ./backend/.env ps -q web) --format '{{.Config.Image}}'
```

**能回滚到什么，由 ACR 的标签列表决定**（控制台 → `dotpub-frontend` → 标签），**不是 `git log`**——构建红过或推送失败的 commit 在 ACR 里根本没有镜像，拿它回滚会报 `manifest unknown`。

三个必须知道的边界：

1. **回滚是临时的**，`IMAGE_TAG` 只活在这次 shell 里，**下次 `git push` 就会把它冲掉**。要长期停在旧版，得 `git revert` 那个 commit 再推。
2. **数据库不回滚**——容器启动时 backend 跑 `aerich upgrade`，它只会往前迁。
3. **验证同样靠镜像名**，不靠眼睛。

---

## 五、手工维护的东西（不在 CI/CD 里）

| 东西 | 说明 |
|---|---|
| `backend/.env` | 密钥，**服务器上唯一不可再生的文件**。改之前先备份 |
| `backup.sh` + crontab | 每天 3:30 备份到 `/root/backup`，保留 14 天。改了手动 scp 并 `chmod +x`（scp 不保留可执行位，覆盖后 cron 会静默失效） |
| `mysql:8.4` 镜像 | 服务器拉不动 Docker Hub，已手工推到 ACR 一次，**不用再管** |

---

## 六、常用命令

```bash
cd /opt/dotpub

docker compose --env-file ./backend/.env ps                   # 三个容器状态
docker compose --env-file ./backend/.env logs -f backend      # 实时日志
docker compose --env-file ./backend/.env restart backend      # 重启单个服务
docker compose --env-file ./backend/.env up -d                # 按当前 compose 文件收敛
```

**每条 compose 命令都必须带 `--env-file ./backend/.env`**，漏了会触发 compose 里的 `${VAR:?}` 保险丝直接报错。这是故意的——宁可响亮地失败，也别拿空密码去建库。

容器名形如 `dotpub-web-1`（compose 项目名 = compose 文件所在目录的 basename）。

---

## 七、排错对照表

| 症状 | 先查什么 |
|---|---|
| **Actions 绿了但代码没生效** | 镜像名对比（第三节）。多半是浏览器缓存，用无痕窗口再确认一次 |
| Actions 报 `denied: unknown manifest class` | 构建步骤少了 `provenance: false` / `sbom: false`，ACR 个人版不收 BuildKit 的证明附件 |
| 部署报 `manifest unknown` | 那个 sha 在 ACR 里没有镜像 |
| 浏览器一直转圈超时 | 安全组 80 端口没开 |
| 502 Bad Gateway | backend 容器挂了 → `docker compose ps` + `logs backend` |
| 刷新内页 404 | `frontend/nginx.conf` 里的 `try_files $uri $uri/ /index.html`（SPA 回退） |
| 接口全部 404 | `frontend/nginx.conf` 里 `proxy_pass` 结尾多了斜杠——**绝对不能加**，加了会剥掉 `/api` |
| 页面空白 | F12 → Console / Network，看 JS 有没有 404 |
| MySQL `Access denied` | 密码只在数据目录为空时读一次。已建库的话改 `.env` 不生效，得进容器 `ALTER USER` |

---

## 八、详细文档（都在仓库 `docs/` 里）

| 文档 | 内容 |
|---|---|
| `docs/cicd.md` | CI/CD 完整链路、五个关键决策、踩坑汇总 |
| `docs/docker-deploy.md` | 容器化迁移的完整过程与踩坑 |
| `docs/ai-chat-v1/v2/v3.md` | AI 助手功能的设计与迭代 |

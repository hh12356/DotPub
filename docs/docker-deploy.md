# DotPub 容器化部署

## Context

站点原本跑在阿里云服务器上，用的是 systemd + 宿主机 Nginx + 宿主机 MySQL。

改 Docker **不是技术上的必需**——那台机器只有 1.7G 内存，容器化反而多花了一点开销。真正的原因是下一步要做 CI/CD，而 CI/CD 需要一个可交付的产物，**镜像就是这个产物**。systemd 那套的交付物是"一堆散落在服务器上的文件"，没法自动化。

顺序上先做 Docker、再做 CI/CD，是因为 CI/CD 的每一环都建立在"镜像能跑起来"之上。

---

## 最终架构

`docker-compose.yml` 在仓库根目录，三个 service：

| service | 镜像 | 端口 | 数据 |
|---|---|---|---|
| `db` | `mysql:8.4` | **不发布**（仅 compose 内网可达） | named volume `db_data` → `/var/lib/mysql` |
| `backend` | `dotpub-backend:v1` | 内部 8010 | 无状态 |
| `web` | `dotpub-frontend:v1` | **宿主机 80** | 无状态 |

- `backend` 的 CMD 是 `aerich upgrade && exec uvicorn main:app --host 0.0.0.0 --port 8010 --workers 2`——`&&` 保证不会带着过期表结构对外服务，`exec` 让 uvicorn 成为 PID 1 以便正确接收 SIGTERM。
- `web` 是两阶段构建：node 编译 → nginx 托管 dist。请求 `/api/` 时反代到 `http://backend:8010`（**末尾没有斜杠**，有斜杠会把 `/api` 前缀吃掉）。
- 三者都 `restart: unless-stopped`，顶替了原来 systemd 的开机自启角色。

`web` 与 `backend` 之间靠 compose 的服务名做 DNS——这是容器化白拿的好处，不需要再配 IP。

---

## 三个约束，推出来的设计

**① 服务器连不上 Docker Hub（无外网、无加速器）。**

这一条决定了整个流程的形状：**镜像只能在本地构建，再传上去**。

```bash
# 本地
docker save dotpub-backend:v1 dotpub-frontend:v1 mysql:8.4 -o dotpub-images.tar
scp dotpub-images.tar dotpub:/opt/dotpub/

# 服务器
docker load -i dotpub-images.tar
```

推论：**compose 文件里只能写 `image:`，绝不能写 `build:`**。写了 `build:`，服务器上就会尝试拉基础镜像然后超时。这一条同样适用于 CI/CD 阶段——到时候 `mysql:8.4` 也得推一份到阿里云 ACR，否则 `compose pull` 会卡在 `db` 那一行。

**② 必须写 `.dockerignore`。**

`COPY . .` 会把 `backend/.env` 打进镜像层。镜像层是永久的——**即使后续提交里删掉了，它仍然留在那一层的 tar 里可以挖出来**。这不是洁癖问题，是密钥泄漏。

`frontend/.dockerignore` 里的 `node_modules/` 同样必须——否则宿主机的 Windows 版本会覆盖容器里的 Linux 版本，报 `You installed esbuild for another platform`。

**③ MySQL 一起来进容器。**

服务器上原本的 MySQL 数据靠 `mysqldump` 导出、再在容器里 `mysql` 恢复。验证字符集时用的是 `CHAR_LENGTH()` 和 `LENGTH()` 的比值（≈3 就是正确的 utf8mb4），而不是把中文标题打出来看——后者依赖终端编码，换个终端可能误判。

---

## 环境变量的两条通道（最容易搞混的地方）

同一份 `backend/.env` 被读了两次，用途完全不同：

| 写法 | 作用时机 | 作用对象 |
|---|---|---|
| 命令行 `--env-file ./backend/.env` | **解析阶段** | 替换 compose 文件里的 `${...}` |
| service 里的 `env_file: ./backend/.env` | **运行阶段** | 注入容器的环境变量 |

所以**每条 `docker compose` 命令都必须带 `--env-file`**，漏了会触发 `${VAR:?}` 保险丝。这是故意设计的：宁可响亮地失败，也不要拿空密码去建库。

`DB_HOST` / `DB_USER` 放在 compose 的 `environment:` 里，**不写进 `.env`**——它们的正确取值取决于"跑在容器里还是宿主机上"，属于编排层的事。

`backend/core/setting.py` 里 `DB_HOST` 的默认值原本硬编码为 `127.0.0.1`，改成读环境变量。**在容器里 `127.0.0.1` 指的是容器自己，不是宿主机**——这是整个迁移里唯一需要动的业务代码。

---

## 踩过的坑

| 症状 | 真实原因 |
|---|---|
| `docker build` 拉基础镜像超时，但 `docker pull` 同一镜像正常 | Docker Desktop 的代理管不到 **BuildKit**。解法是先手动 `docker pull` 基础镜像，构建里 `RUN pip/npm` 换国内源 |
| 容器 `Up` 但 80 端口没人监听，外面 `curl` 报 `Connection reset by peer` | `nginx:*-alpine` 的 entrypoint 脚本调 `apk manifest nginx`，`apk` 在无外网时挂死，永远走不到 `exec nginx`。**诊断靠 `docker exec <容器> ps aux` 看 PID 1 是谁** |
| 改了 `.env` 里的数据库密码，当下没事 | MySQL 镜像**只在数据目录为空时**读一次 `MYSQL_ROOT_PASSWORD`。之后改只让文件撒谎，等做备份时才报 `Access denied` |
| `KeyError: 'DEEPSEEK_API_KEY'` | 服务器上的 `.env` 早于 chat 功能存在，只是缺这一行。**跨环境只补"缺的"变量，绝不覆盖"已有的"** |

最后一条的判断方法是比对变量名而不是抄值：

```bash
cut -d= -f1 backend/.env | sort
docker inspect <容器> --format '{{range .Config.Env}}{{println .}}{{end}}' | cut -d= -f1 | sort
```

---

## 切换与清理

切换当天：停宿主机 systemd 服务 → 起容器 → 确认无误后把 `web` 的端口从 `127.0.0.1:8080` 改成 `80`。

之后的清理清单：

1. **补数据库备份**（服务器上原本**一份都没有**——root 无 crontab、`/var/spool/cron/crontabs/` 是空的）。新增 `backup.sh`，crontab 每天 3:30 执行，保留 14 天。
2. 停用并禁用宿主机 `mysqld`
3. 停用并禁用旧的 `dotpub` systemd 服务
4. 删除 `/opt/dotpub/frontend/dist`（已无人读取的过期静态文件）

`backup.sh` 有个不显眼但重要的细节：**先写 `.tmp`，成功了才 `mv` 成正式文件名**。不这么做的话，mysqldump 中途失败时 `>` 已经建好了文件、里面是半截内容——你会得到一个看起来完全正常、实际不能用的备份，而且要到真需要恢复的那天才发现。

**最后重启了一次服务器验证整栈自启。** 这一步不能省：开机自启的职责已经从 `systemctl enable` 转交给 `restart: unless-stopped` + Docker 守护进程，不实测就只是"以为"它能自己回来。

注意 `unless-stopped` 的语义是"**除非你手动停过**"——如果调试时敲了 `docker compose stop web`，之后重启服务器 web 也不会自己回来。

---

## 现状与待办

`http://47.122.126.63` 跑在容器上，重启验证通过。

**下一步 CI/CD：**

1. `/opt/dotpub` 改成 git 克隆（现在是 `git archive` 的产物，有 `.gitignore` 没有 `.git/`）。改之前先把 `backend/.env` 备份到克隆目录之外——它是服务器上唯一不可再生的文件。
2. 建阿里云 ACR 实例，`mysql:8.4` 一并重打标推入。
3. 把 `entrypoint: ["nginx", "-g", "daemon off;"]` 从 compose 挪进 `frontend/Dockerfile`，顺手换 `nginx:stable`（Debian 版不调 `apk`，那个卡死问题从根上消失）。
4. GitHub Secrets + `.github/workflows/deploy.yml`。

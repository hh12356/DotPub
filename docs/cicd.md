# DotPub CI/CD：GitHub Actions → 阿里云 ACR → 服务器

## Context

容器化部署完成后，发布流程是"本地 build → `docker save` → scp → 服务器 `docker load`"。它能用，但**必须在我在场时才能发布**：镜像得从我的电脑上打包传过去。

CI/CD 换掉的就是这一环：**`git push` 就是部署。**

---

## 完整链路

```
    git push (master)
        │
        ▼
   GitHub Actions runner（临时租的机器，有完整外网）
        ├─ docker build ×2      ← 构建跑在这里，不占服务器资源
        ├─ docker push      ──┐
        └─ scp docker-compose.yml ──┐
                                    │
        ┌───────────────────────────┘
        ▼
   阿里云 ACR（镜像仓库）
        │
        │  docker compose pull（服务器主动拉）
        ▼
   服务器：docker compose up -d
```

## 三个角色的分工

| 角色 | 干什么 | 不干什么 |
|---|---|---|
| GitHub runner | 构建镜像、推 registry、把 compose 文件 scp 过去 | 不碰线上容器 |
| 阿里云 ACR | 存镜像 | 不构建（**没关联代码源**） |
| 服务器 | 拉镜像、跑容器 | **不构建、不访问 GitHub、不拉 Docker Hub** |

服务器的约束是这套设计的出发点：**它只做"拉"和"跑"**。任何需要它主动出网的动作都被移走了。

---

## 五个关键决策

**① 构建必须离开服务器。**

服务器只有 1.7G 内存，构建会把它挤死。更重要的是它连不上 Docker Hub，`FROM python:3.14-slim` 第一步就超时。构建放在 runner 上，顺带把本地 Docker Desktop 跟代理搏斗的那套（手动预拉基础镜像、`--build-arg` 换国内源）全都消掉了。

**② 服务器不访问 GitHub。**

原本的设计是让服务器 `git pull`，实测不行：

```
fatal: unable to access 'https://github.com/hh12356/DotPub.git/':
GnuTLS recv error (-110): The TLS connection was non-properly terminated.
```

手动操作时这不算事——重试就行。**但自动化里一次抖动就是一次红色部署**，而且它不挑时间。

改法：compose 文件由 runner 用 scp 送过去（runner 在 GitHub 机房里，取代码稳如泰山）。代价只是 workflow 里多一个步骤，换来服务器**一个字节都不需要从 GitHub 取**。

**③ Registry 必须是国内服务。**

试过 GitHub Container Registry，失败了：

```
failed to do request: Get "https://pkg-containers.githubusercontent.com/ghcrblobs08/blobs/sha256:..."
net/http: TLS handshake timeout
```

**这个失败暴露了一个容易搞错的点**：ghcr 的 registry API（`ghcr.io`）和真实的镜像层数据（`pkg-containers.githubusercontent.com`，走 Azure blob）**是两个不同的域名**。只探测 `ghcr.io/v2/` 返回 401，只证明了 API 通，完全没证明数据下得下来。

教训：**要验证"能不能用某服务"，就做那个真实操作（拉一个镜像），别做代理指标的探测。**

最终用阿里云 ACR 个人版。注意它现在的域名格式是**每个实例专属**的：

```
crpi-<实例ID>.<地域>.personal.cr.aliyuncs.com
```

不是老教程里的 `registry.cn-hangzhou.aliyuncs.com`。

另外 ACR 个人版**不是所有地域都有**——服务器所在的武汉（`cn-wuhan-l`）就没有，所以实例建在杭州，跨地域拉取走公网（**入方向流量不计费**）。

**④ 镜像 tag 用 git commit 的 sha。**

不用 `latest` 单独作为版本标识——`latest` 会被覆盖，覆盖之后就**没有东西可以回滚**。每个 commit 一个不可变的 tag，回滚就是"把 tag 指回上一个"。

顺带解决了一个更基本的问题：**线上跑的到底是哪份代码**，`docker inspect` 一看就知道。用 `latest` 的话这个问题永远没有答案。

`latest` 仍然会推一份，但只给手动命令兜底（compose 里写的是 `${IMAGE_TAG:-latest}`），部署永远用 sha。

**⑤ 健康检查要比对镜像，不能只 curl 首页。**

第一版写的是：

```bash
curl -fsS -o /dev/null http://127.0.0.1/ && echo "deployed, homepage OK"
```

**这个检查是空转的。** 旧的三个容器一直在正常服务，curl 当然返回 200——它只能证明"有个网站在跑"，**测不出"这次部署什么都没发生"**。

结果就是：workflow 绿着，容器还是 17 小时前那一批。真正的检查是比对运行的镜像名：

```bash
WEB=$(docker compose ps -q web)
RUNNING=$(docker inspect "$WEB" --format '{{.Config.Image}}')
[ "$RUNNING" = "$EXPECTED" ] || exit 1
```

---

## 踩过的坑汇总

| 症状 | 真实原因 |
|---|---|
| `GnuTLS recv error (-110)` | 服务器到 GitHub 的 TLS 被中途掐断——国内链路的常态，**不能让自动化依赖它** |
| `ghcr.io/v2/` 返回 401，但拉镜像 `TLS handshake timeout` | API 域名和 blob 数据域名是两回事，前者通不代表后者通 |
| Actions 绿了但容器没更新 | 健康检查只 curl 首页，测不出"什么都没发生" |
| `repository name must be lowercase` | ghcr 强制小写，`DotPub` 这种混写会被拒 |
| ACR 在服务器所在地域找不到 | 个人版只开放部分地域，换杭州/上海即可 |
| 部署卡在 `Mirror mysql` 十几分钟 | **不一定是卡死**——`docker push` 在非 TTY 下缓冲输出，跨境传 500MB 期间日志就是空白的 |

---

## 日常操作

**部署** —— 提交并推送，去 Actions 看结果：

```bash
git add -A && git commit -m "..." && git push
```

**查线上跑的是哪一版**：

```bash
docker inspect dotpub-web-1 --format '{{.Config.Image}}'
```

**回滚** —— 把 `IMAGE_TAG` 指向上一个 commit 的 sha：

```bash
cd /opt/dotpub
export IMAGE_TAG=<上一个 sha>
docker compose --env-file ./backend/.env pull
docker compose --env-file ./backend/.env up -d
```

（`IMAGE_TAG` 只认 shell 变量，不能写进 `backend/.env`——那个文件是手工维护的密钥，机器写入的部署状态不该混进去。）

回滚有三个必须知道的边界：

1. **它不写进 git。** `IMAGE_TAG` 只活在这次 shell 里，服务器上一份"当前跑哪个 sha"的记录都没有。**下次 `git push` 会直接把它冲掉**，回到最新版。所以回滚是"临时救火"，不是"改回去"——真要长期停在旧版，得 revert 那个 commit 再推。
2. **验证方式只有一种：比对镜像名**（`docker inspect`）。页面看起来和回滚前一模一样是正常的，**别靠眼睛判断回滚成没成**。这正是第 ⑤ 条决策的同一个道理。
3. **数据库不回滚。** 容器启动时 backend 会跑 `aerich upgrade`，它只会往前迁。用旧镜像配新表结构，只要新版本没加过 migration 就没事；加过就可能炸。

---

## 不在 CI/CD 覆盖范围内的

这三个是**手工维护**的，改了要自己同步：

- **`backend/.env`** —— 密钥，永远不进仓库。**服务器上唯一不可再生的文件**，改之前先备份。
- **`backup.sh` + crontab** —— 备份脚本。它没做进 scp 同步，因为 scp 不保留可执行位，覆盖一次就可能让 cron 静默失效。改了就手动传一次并 `chmod +x`。
- **`mysql:8.4` 推到 ACR** —— 服务器拉不动 Docker Hub，所以这个基础镜像必须有一份在国内 registry 上。**推一次就永远在，所以是一次性操作，手工做**：

  ```bash
  docker pull --platform linux/amd64 mysql:8.4
  docker tag mysql:8.4 crpi-.../dotpub/mysql:8.4
  docker push crpi-.../dotpub/mysql:8.4
  ```

  它一度被写在 workflow 里，用 `docker manifest inspect` 判断"推过没"。**那一步是错的**：一次性操作放进流水线，等于每次部署都付一遍它的成本，而守卫本身对私有 ACR 又不可靠。判断标准不是"能不能自动化"，是"**这件事会发生几次**"——一次的事就该手工做。

另一件不属于 CI/CD、但容易被忘的事：**数据库备份和数据库在同一块盘上**。只防误删误改，不防磁盘故障。

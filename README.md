# DotPub

一个技术文章社区,我们称其为小黑书

🔗 在线体验：http://47.122.126.63/ (已下线)

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | FastAPI 0.141 · Tortoise ORM 1.1 · MySQL 8（utf8mb4）· Aerich 迁移 |
| 认证 | JWT（PyJWT / HS256）· argon2id 密码哈希 |
| 安全 | nh3（入库清洗）· DOMPurify（渲染清洗） |
| 前端 | React 19 · Vite 8 · antd 6 · Redux Toolkit · react-router-dom 7 |
| 其他 | react-quill-new（富文本编辑器）· ECharts 6（管理看板）· axios |

## 功能

**访客**：浏览首页 / 搜索文章 / 查看文章与评论 / 看作者主页

**注册用户**
- 富文本发布与编辑文章（Quill），删除/编辑自己的文章与评论
- 点赞、收藏、评论
- 「我的文章 / 我的点赞 / 我的收藏」三个个人列表
- 修改个人简介，个人主页展示发文数、获赞数、被收藏数

**管理员**
- 置顶任意文章；删除任意文章与评论（和作者本人共用同一套权限判定）
- 封号 / 禁言任意用户（封号后无法登录，禁言后无法发帖评论但可浏览）
- `/admin` 数据看板：总量统计、近 14 天新增文章与用户趋势、点赞/收藏/评论人气榜、发文最多的用户

**列表能力**：首页三路排序（最新 / 最热 / 最高分）、分页 + `has_more`、搜索、404 与 403 的错误态

<img width="420" height="280" alt="image" src="https://github.com/user-attachments/assets/031918cc-5177-4979-97ca-6904e3523782" />
<img width="420" height="280" alt="image" src="https://github.com/user-attachments/assets/9a12d60c-8037-4234-b3ee-9142398cbc17" />

## 项目结构

```
DotPub/
├── backend/
│   ├── main.py            # FastAPI 入口，挂载 6 个路由 + 注册 Tortoise
│   ├── apis/              # login · sign_up · article · user · admin · chat
│   ├── core/
│   │   ├── security.py    # JWT、argon2、verify_token / verify_admin / can_manage
│   │   └── setting.py     # .env 载入 + TORTOISE_ORM 配置
│   ├── models/            # UserAccount · Article · Comment · ArticleLike · ArticleStar
│   ├── migrations/        # Aerich 迁移 0–11
│   ├── seeds/             # 12 篇种子文章正文（网络前端 / 后端数据库 / 安全运维）
│   ├── tests/             # test_sanitize.py · test_stats.py · test_chat.py（裸 assert，无框架）
│   └── seed_articles.py   # 种子数据导入脚本（--clean 可重跑）
└── frontend/
    └── src/
        ├── router/        # 路由表 + RequireAdmin（管理页守卫）
        ├── apis/          # 按模块封装的接口
        ├── pages/         # Home · Article · Write · Search · Login · Signup · Layout · Admin · User/*
        ├── components/    # ArticleCard · ChatFloat（AI 助手悬浮窗）
        ├── hooks/         # useArticles：分页累积 + 丢弃过期响应
        ├── store/         # Redux user 切片（sessionStorage 的镜像）
        └── utils/         # request（axios 封装 + 401 拦截跳登录）· token · userName / userRole
```

## 部署与 CI/CD

三个容器（`web` nginx + `backend` uvicorn + `db` mysql）由根目录 `docker-compose.yml` 编排，宿主机只暴露 80。**`git push` 即部署**：GitHub Actions 构建两个镜像推阿里云 ACR，服务器只做 `pull && up -d`，不构建、不访问 GitHub；镜像 tag 用 git commit sha，线上跑的是哪一版 `docker inspect` 一看就知道，回滚就是把 tag 指回上一个 commit。

细节见 [`docs/docker-deploy.md`](docs/docker-deploy.md) · [`docs/cicd.md`](docs/cicd.md)。

## 值得一提的几处

### 1. 存储型 XSS：把清洗放在写入口

正文是富文本，前端必须用 `dangerouslySetInnerHTML` 渲染——这意味着**只要有人绕过前端直接 `POST /api/article`，脚本就会存进库，之后每个打开这篇文章的人都执行它**。

- 前端那些 `required`、`isEmptyHtml` 校验都跑在攻击者自己的浏览器里，不算信任边界，所以清洗放在**后端入库前**：`apis/article.py` 的 `clean_html()` 用 nh3 白名单过滤，只放行 Quill 真正产出的标签与属性。
- 没有用正则自己实现——`<IMG SRC=x ONERROR=...>`、`<scr<script>ipt>`、实体编码都能绕过正则；nh3 底层是真正的 HTML 解析器 + 白名单，和浏览器同一套规则。
- 前端渲染时再过一次 DOMPurify 作纵深防御（后端失守时仍有兜底）。
- 代价与取舍：`class` / `data-list` 必须放行，否则正文里的列表和对齐会整段丢格式。

覆盖用例在 `backend/tests/test_sanitize.py`（含大小写变形、`javascript:` 伪协议等攻击样本）。

### 2. 点赞收藏的幂等：把约束交给数据库

「先查有没有点过，再写」两步之间有竞态窗口，双击或重放请求就会写进两条。

做法是 `ArticleLike` 上建 `unique_together(user, art)`，写入时直接捕获 `IntegrityError` 并返回「已经赞过了」。并发下只有一条能成功，其余走异常分支——这也是唯一不会漏的地方。

### 3. 热榜排序：加权 + 时间衰减

按点赞数硬排会让老文章永久霸榜，新内容没有曝光。排序键改成：

```
0.25 × 点赞 + 0.35 × 评论 + 0.4 × 收藏
  → LOG10 压缩 → - 发布至今小时数 / 90天窗口
  → + 由 art_id 派生的确定性抖动（打散同分）
```

`LOG10` 是为了让「100 赞 vs 10 赞」的差距不被「1 赞 vs 0 赞」淹没；抖动项让同分文章不会永远固定在同一顺序。

两个实现上的坑：排序必须在 SQL 里算（Tortoise 的 `Count` 没实现算术运算，`Count(...) * 0.4` 会直接 `TypeError`，所以用 `RawSQL` 关联子查询）；`ORDER BY` 末尾一定要带 `-art_id` 兜底，并列分数时 MySQL 不保证顺序，翻页会重复或漏项。

### 4. 权限：一个纯函数 + 服务端下发「我能做什么」

- `can_manage(owner_id, viewer_id, is_admin)` 是纯函数，编辑文章、删除文章、删除评论三处共用同一个判定，不存在某条路径漏判。
- 封禁与禁言统一在 `verify_token` 依赖里拦截，一处生效于**所有**需要登录的接口，而不是在每个路由里各写一遍。
- 列表与详情接口直接返回 `can_delete` / `can_pin` / `can_ban` / `self`，前端不自己算权限——按钮显示与否和后端判定同源，不会出现「按钮在但点了一直 403」。

### 5. 密钥与密码

- `JWT_SECRET_KEY`、`DB_PASSWORD` 只存在于 `backend/.env`（已被 gitignore），仓库里只有 `backend/.env.example` 说明怎么生成。
- `core/setting.py` 用 `setdefault` 载入 `.env`，所以线上平台注入的环境变量优先；签名密钥**不给默认值**，缺失时进程启动瞬间就崩，而不是静默用一个公开值跑起来。
- 密码用 argon2id（time_cost 3 / 内存 64MB / 并行 4）。`backend/pwd_migrate.py` 是把存量明文密码一次性哈希的脚本，以 `$argon2id$` 前缀作幂等 guard，中途挂了可以直接重跑。

### 6. 列表接口的 payload

列表接口不返回正文 HTML，而是用 `first_line()` 把富文本转成纯文本摘要（卡片本来就是按纯文本渲染的，直接给 HTML 会把标签和 `&nbsp;` 一起显示出来）。首页、搜索、个人文章、点赞、收藏五个列表共用这一个函数。

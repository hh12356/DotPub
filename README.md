# DotPub

一个多角色的技术文章社区：任何人都能注册发文、评论、点赞收藏；管理员可以处置任意内容与用户，并在数据看板上看到全站趋势。

> 🔗 在线体验：`（待填线上地址）`
> 数据库里已有 12 篇技术文章和一批互动记录作演示数据。

<!-- 截图（建议放 3 张，横排）：
     1. 首页文章流  2. 文章详情 + 富文本正文  3. /admin 数据看板
-->

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

## 项目结构

```
DotPub/
├── backend/
│   ├── main.py            # FastAPI 入口，挂载 5 个路由 + 注册 Tortoise
│   ├── apis/              # login · sign_up · article · user · admin
│   ├── core/
│   │   ├── security.py    # JWT、argon2、verify_token / verify_admin / can_manage
│   │   └── setting.py     # .env 载入 + TORTOISE_ORM 配置
│   ├── models/            # UserAccount · Article · Comment · ArticleLike · ArticleStar
│   ├── migrations/        # Aerich 迁移 0–11
│   ├── seeds/             # 12 篇种子文章正文（网络前端 / 后端数据库 / 安全运维）
│   ├── tests/             # test_sanitize.py · test_stats.py（裸 assert，无框架）
│   └── seed_articles.py   # 种子数据导入脚本（--clean 可重跑）
└── frontend/
    └── src/
        ├── apis/          # 按模块封装的接口
        ├── pages/         # Home · Article · Write · Search · Login · Signup · Layout · Admin · User/*
        ├── hooks/         # useArticles：分页累积 + 丢弃过期响应
        ├── store/         # Redux user 切片（sessionStorage 的镜像）
        └── utils/         # request（axios 封装 + 401 拦截跳登录）· token
```

## 本地跑起来

**1. 建库**

```sql
CREATE DATABASE DotPub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**2. 起后端**（需要 Python 3.11+）

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                                 # 然后把两个值填上
python -c "import secrets; print(secrets.token_hex(32))"   # 生成 JWT_SECRET_KEY

python -m aerich upgrade                             # 建表
python main.py                                       # http://127.0.0.1:8010
```

**3. 灌演示数据**（可选，需要库里已有至少 3 个账号）

```bash
python seed_articles.py            # 写入 12 篇文章 + 点赞收藏记录
python seed_articles.py --clean    # 先删同名旧文章再写，可重复跑
```

**4. 起前端**

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173，/api 已代理到 8010
```

**5. 造一个管理员**

注册接口不开放管理员角色，直接在库里改：

```sql
UPDATE useraccount SET user_role = 'admin' WHERE user_name = '你的用户名';
```

重新登录后 Layout 的菜单里会出现「Admin」，访问 `/admin` 即是数据看板。

## 接口一览

所有接口以 `/api` 为前缀。成功统一返回 `{code: 200, msg, data}`（列表额外带 `has_more`）；失败走 HTTP 状态码 + `detail: {code, msg}`。

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/signup` | 公开 | 注册（用户名/手机号唯一，密码 ≥8 位） |
| POST | `/login` | 公开 | 登录取 JWT；被封禁的账号拒绝登录 |
| GET | `/article` | 公开 | 文章列表，`page` / `size` / `sort=latest\|hot\|greatest` |
| GET | `/article/{id}` | 公开 | 文章详情，含 `can_delete` / `can_pin` |
| POST | `/article` | 登录 | 发布文章（正文入库前清洗） |
| PUT | `/article/{id}` | 本人或管理员 | 编辑文章 |
| DELETE | `/article/{id}` | 本人或管理员 | 删除文章 |
| GET | `/search/{关键词}` | 公开 | 按标题模糊搜索 |
| PUT | `/pin/{id}` | 管理员 | 置顶 / 取消置顶 |
| GET / DELETE | `/like/{id}` | 登录 | 点赞 / 取消点赞（幂等） |
| GET / DELETE | `/star/{id}` | 登录 | 收藏 / 取消收藏（幂等） |
| GET | `/comment/{art_id}` | 公开 | 评论列表 |
| PUT | `/comment/{art_id}` | 登录 | 发表评论 |
| DELETE | `/comment/{cmt_id}` | 本人或管理员 | 删除评论 |
| GET | `/userart` | 登录 | 我发布的文章 |
| GET | `/likes` · `/stars` | 登录 | 我点赞 / 收藏的文章 |
| GET | `/profile/{user_id}` | 公开 | 用户主页（发文数、获赞、被收藏） |
| PUT | `/profile/bio` | 登录 | 修改个人简介 |
| PUT | `/ban/{user_id}` · `/mute/{user_id}` | 管理员 | 封号 / 禁言及解除 |
| GET | `/admin/stats` | 管理员 | 看板数据（总量、14 天趋势、三个榜单、活跃作者） |

## 部署

仓库本身不依赖任何绝对地址，线上按同域部署即可：

- 前端 `baseURL` 是相对路径 `/api`，Nginx 把 `/api` 反代到 uvicorn（开发环境由 Vite 代理到 8010，行为一致）。
- `.env` 不进仓库，`JWT_SECRET_KEY` / `DB_PASSWORD` 由部署平台注入环境变量。
- 建表用 `python -m aerich upgrade`，服务由 systemd 或平台进程管理拉起 `uvicorn`。

`（待填：实际的域名 / 服务器与部署命令）`

## 已知问题与后续

**已确认的缺陷**
- 退出登录不彻底：`clearUserInfo` 定义了但从未 dispatch，401 拦截器也只清 token 和用户名、不清 `user_role` —— 退出后 Redux 里的登录态会残留到刷新页面为止。
- `@ant-design/icons` 全站大量使用，但没写进 `package.json`（靠 antd 的传递依赖解析）。全新环境 `npm install` 后有装不上的风险。
- 前端没有 404 catch-all 路由，访问未知路径会落到 react-router 的默认英文错误页。
- `pages/User/` 下的 Likes、Stars、UserArt 三个页面几乎是逐字复制的，只差调用的接口名，应当抽成一个列表组件。
- 首页 `useArticles` 没有 `catch`，接口失败时只有空列表和一个 unhandled rejection；两处 `console.log` 未清理。

**有意为之的取舍**
- `/admin` 没有前端路由守卫，菜单项按角色隐藏，但直接敲 URL 仍能进入页面——真正的拦截在后端（非管理员拿到 403，页面渲染「无权访问」）。前端守卫只是 UI，不是安全边界。
- 点赞用 `GET /like/{id}` 表示创建、评论发布用 `PUT /comment/{art_id}`，语义上不 RESTful；保持现状是因为前端调用点已经铺开，改动收益低于回归风险。
- 列表接口的 `has_more` 按「返回条数恰好等于 size」判断，最后一批正好满页时会多出一次空请求。

**还没做的**
- 发帖 / 评论的频率限制与反垃圾
- 图片上传（现在正文插图只能填外链 URL）
- 搜索、评论、个人页列表的分页
- 单元测试框架（目前只有 `tests/` 下两个裸 assert 自检脚本），前端无 lint 脚本（`oxlint` 已装但没配 script）

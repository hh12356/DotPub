dotpub/
├── backend/                    # 后端根目录（FastAPI + Tortoise）
│   ├── app/                    # 核心代码（所有业务逻辑）
│   │   ├── core/               # 核心配置与工具
│   │   │   ├── config.py       # 读取 .env，管理数据库连接串、JWT密钥
│   │   │   ├── security.py     # 密码加密、JWT签发与验证函数
│   │   │   └── dependencies.py # 全局依赖项（如：获取当前登录用户、验证管理员身份）
│   │   ├── models/             # TortoiseORM 实体类（对应 MySQL 表）
│   │   │   ├── user.py         # User 表（id, username, password_hash, role...）
│   │   │   ├── article.py      # Article 表（title, content_md, content_html...）
│   │   │   ├── comment.py      # Comment 表
│   │   │   └── like.py         # Like 表（联合唯一索引在这里定义）
│   │   ├── schemas/            # Pydantic 模型（接口请求/响应的数据结构）
│   │   │   ├── user.py         # RegisterSchema, LoginSchema, UserInfoResponse
│   │   │   ├── article.py      # CreateArticleSchema, UpdateArticleSchema, ArticleListResponse
│   │   │   └── common.py       # 统一分页、统一返回格式（如 {"code":0, "data":{}}
│   │   ├── routers/            # 路由层（接口地址定义，只负责调 Service 或直接调 Model）
│   │   │   ├── auth.py         # /api/auth/register, /api/auth/login
│   │   │   ├── articles.py     # /api/articles (GET/POST), /api/articles/{id} (GET/PUT/DELETE)
│   │   │   ├── comments.py     # /api/comments (POST/GET)
│   │   │   ├── likes.py        # /api/likes (POST/DELETE)
│   │   │   └── admin.py        # /api/admin/... (所有管理员专用接口)
│   │   ├── services/           # 【可选】业务逻辑层（处理复杂的数据库事务）
│   │   │   └── article_service.py # 处理点赞时“同时更新文章计数”的事务
│   │   └── main.py             # FastAPI 启动入口（注册路由、注册数据库、配置 CORS）
│   ├── migrations/             # Aerich 自动生成的数据库版本迁移文件（千万别手动改）
│   ├── .env                    # 环境变量（DB_URL, JWT_SECRET_KEY）
│   ├── requirements.txt        # Python 依赖清单
│   └── pyproject.toml          #（可选）如果使用 Poetry 管理包
│
├── frontend/                   # 前端根目录（React + Vite）
│   ├── public/                 # 静态资源（favicon, 图片等）
│   ├── src/
│   │   ├── api/                # 网络请求层（统一管理后端接口调用）
│   │   │   ├── client.js       # axios 实例（配置 baseURL，请求/响应拦截器塞 Token）
│   │   │   ├── auth.js         # 封装 login(), register() 请求
│   │   │   ├── articles.js     # 封装 getArticles(), createArticle() 等
│   │   │   └── admin.js        # 封装管理员专用接口（删除用户、置顶）
│   │   ├── assets/             # 样式文件（CSS / Tailwind 配置）、字体
│   │   ├── components/         # 可复用 UI 组件（无状态或纯展示）
│   │   │   ├── common/         # 通用组件（Button, Input, Modal, Toast）
│   │   │   ├── layout/         # 布局组件（Header, Footer, Sidebar, AdminLayout）
│   │   │   └── articles/       # 业务组件（ArticleCard, MarkdownEditor, CommentList）
│   │   ├── hooks/              # 自定义 React Hooks（抽离复用逻辑）
│   │   │   ├── useAuth.js      # 管理登录状态、Token 过期跳转
│   │   │   └── usePagination.js# 封装分页加载逻辑
│   │   ├── pages/              # 路由页面（每个文件对应一个独立页面）
│   │   │   ├── Home/           # 首页 Feed 流（文章列表）
│   │   │   ├── Login/          # 登录页
│   │   │   ├── Register/       # 注册页
│   │   │   ├── ArticleDetail/  # 文章详情（包含评论和点赞按钮）
│   │   │   ├── WriteArticle/   # 写文章/编辑文章（包含 Markdown 编辑器）
│   │   │   └── Admin/          # 管理员后台（包含 Dashboard 数据看板、用户管理、内容审查）
│   │   ├── store/              # 全局状态管理（Context / Zustand / Redux）
│   │   │   └── authStore.js    # 存储当前用户信息、角色、Token
│   │   ├── utils/              # 工具函数（时间格式化、字符串截取、Markdown 辅助）
│   │   ├── App.jsx             # 根组件（定义路由映射）
│   │   ├── main.jsx            # 入口文件
│   │   └── routes.js           # 路由配置表（区分哪些页面需要登录，哪些需要 Admin 权限）
│   ├── .env                    # 前端环境变量（VITE_API_BASE_URL=后端地址）
│   ├── vite.config.js          # Vite 配置（代理设置，解决开发环境跨域）
│   └── package.json            # Node 依赖清单
│
├── docker-compose.yml          # 【后期部署使用】一键启动 MySQL + 后端 + Nginx
└── README.md                   # 项目介绍、启动命令、架构图
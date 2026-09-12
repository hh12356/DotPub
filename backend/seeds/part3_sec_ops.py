# 由 seed_articles.py 载入，字段名和 Article 模型对齐
ARTICLES = [
    {
        "title": "JWT 原理与常见安全坑",
        "content": """<p>JWT 是前后端分离项目里最常见的登录凭证，但很多人只把它当成一串加密字符串塞进 Authorization 头，并不知道 payload 其实是明文。这篇文章讲清 JWT 的三段结构、签名到底保证了什么，以及 alg 绕过、无法主动失效、存储位置这几个真实会踩的坑。</p>
<h2>三段结构：header、payload、signature</h2>
<p>JWT 是三个 Base64URL 编码的片段用点号拼起来的：header 描述算法和类型，payload 放声明 claim，第三段是签名。Base64URL 就是把 Base64 里的加号和斜杠换成减号和下划线，再去掉尾部填充等号，好让它能安全地放进 URL 和请求头。解码不需要任何密钥。</p>
<p><strong>最常见的误解就是把 payload 当成加密数据。</strong>任何人拿到 token，把中间那段复制出来做一次 Base64URL 解码，就能看到 userId、role、过期时间。所以绝对不能往 payload 里放手机号、身份证号这类敏感信息。</p>
<h2>签名校验与 alg 绕过</h2>
<p>签名不是对整串 token 做哈希，而是把 header 和 payload 的原始字符串用点号拼起来，用密钥和 header 里声明的算法算一个摘要，再和第三段比对。</p>
<p>它保证的是<strong>完整性和来源</strong>：内容被改过一个字符签名就对不上，没有密钥就伪造不出合法签名。它<strong>不保证保密性</strong>，payload 依旧是明文。这是两件完全不同的事，混在一起想就会写出错的代码。</p>
<p>更糟的是，校验时用什么算法这件事本身不该由请求方决定。早期不少库会读 header 里的 alg 字段来决定用什么算法校验。攻击者把 alg 改成 none、签名段留空，如果服务端照做就等于完全不校验，可以伪造任意身份。另一种玩法是算法混用：服务端本该用公钥验 RS256，攻击者改成 HS256，然后拿那个公开的公钥当 HMAC 密钥重算签名，同样能通过。</p>
<p>防御原则只有一条：<strong>服务端固定算法，绝不信任 header 里的 alg</strong>。用 PyJWT 时把 algorithms 写死成一个列表，不要放 None。HS256 是对称算法，签发和校验用同一个密钥，密钥泄露等于谁都能签发；RS256 是非对称，私钥签发、公钥校验，适合多个服务共享校验能力的场景，但私钥必须管好，绝不能进 git。</p>
<h2>无法主动失效：短过期加 refresh token</h2>
<p>JWT 是无状态的，服务端不存会话，所以用户登出、改密码、被封号之后，手里那张 token 在过期前依然有效。这是设计上的取舍，不是 bug。标准做法是三件事叠加：</p>
<ul><li data-list="bullet"><span class="ql-ui"></span>access token 过期时间压短，让它自己快速失效；</li><li data-list="bullet"><span class="ql-ui"></span>用长期但可撤销的 refresh token 换新 access token，refresh 存在服务端；</li><li data-list="bullet"><span class="ql-ui"></span>改密码、封号这类必须立刻生效的场景，维护一个黑名单或版本号，校验时比对。</li></ul>
<p>黑名单会破坏无状态的好处，所以别给每个 token 都记，只记真正需要立刻失效的。</p>
<h2>前端存哪里</h2>
<p>放 localStorage 最省事，但任何 XSS 都能把它读走；放 Cookie 能配 HttpOnly 挡住 JS 读取，代价是要防 CSRF。一般结论是用 HttpOnly、Secure、SameSite 三件套的 Cookie，SameSite 至少 Lax，跨站场景配 Strict 并带上 CSRF token。不存在又方便又安全的存储位置，只能选一种攻击面。无论选哪种，都要给 token 设一个合理的过期时间，永久有效的凭证一旦泄露就是永久的。</p>
<h2>PyJWT 签发与校验</h2>
<pre><code>import jwt
from datetime import datetime, timedelta, timezone

SECRET = "从环境变量读，不要写死在代码里"
ALGO = "HS256"

def issue(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def verify(token: str) -> dict:
    # algorithms 写死，绝不读 header 里的 alg
    return jwt.decode(
        token,
        SECRET,
        algorithms=[ALGO],
        options={"require": ["exp", "sub"]},
    )
</code></pre>
<p>注意 sub 用字符串、exp 用 UTC 时间戳，这是规范要求，部分库不认 int 类型的 sub。校验失败就统一抛异常，不要在业务代码里自己解析 payload 当身份用。</p>
""",
    },
    {
        "title": "Docker 镜像分层与构建缓存",
        "content": """<p>很多人写 Dockerfile 的顺序是拍脑袋定的，结果改一行业务代码，构建时就要重装一遍依赖。根因在于不理解镜像的分层和缓存命中规则。这篇讲清层的叠加方式、缓存什么时候失效，并给出依赖先装、代码后拷的正确写法。</p>
<h2>镜像是一层层叠出来的</h2>
<p>镜像不是一个大文件，而是一组只读层的叠加，每一层记录的是相对上一层的文件系统差异。容器启动时，Docker 在所有只读层之上再加一个可写层，容器里所有写操作都发生在这层，删掉容器这层就没了，镜像本身不动。这也是容器里的数据不持久化的原因。</p>
<p>Dockerfile 里几乎每条指令都会生成一层。COPY、RUN、ADD 这类产生文件系统改动的必然成层，ENV、WORKDIR、CMD 这类只改元数据的层很轻，但不代表不存在。</p>
<h2>缓存规则：一层变了，后面全废</h2>
<p>构建时 Docker 从第一层开始逐层比对。只有当前面所有层都<strong>完全没变</strong>时，这一层才能命中缓存；<strong>任意一层变了，它之后的所有层全部失效，必须重建</strong>。这里的变既包括指令文本改了，也包括被 COPY 进来的文件内容变了，Docker 会对文件算校验和。</p>
<p>还有个常被忽略的点：RUN 指令的缓存不只看命令本身，还看它前面所有层的指纹。所以哪怕 pip 命令一个字没改，只要前面的 COPY 内容变了，它照样要重跑。</p>
<h2>错误顺序与正确顺序</h2>
<p>先看常见的错误写法：</p>
<pre><code>FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
</code></pre>
<p>COPY 整份代码在前，只要改了一个 py 文件，这层的校验和就变了，后面的 pip install 缓存全部失效，每次构建都要重新下载安装全部依赖，项目越大越疼。正确写法是把依赖声明单独先拷、先装：</p>
<pre><code>FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
</code></pre>
<p>这样改业务代码只会让最后的 COPY 失效，依赖层稳稳命中缓存。原则就是：<strong>变动频率低的放前面，变动频率高的放后面</strong>。</p>
<h2>dockerignore 与多阶段构建</h2>
<p>COPY 会把构建上下文目录里的所有东西都送进去，包括 .git、缓存目录、node_modules、虚拟环境。这些既拖慢构建、又污染镜像，还会让缓存莫名其妙地失效，比如 .git 里每次提交都在变。用 .dockerignore 排除掉，写法和 .gitignore 一样。另外构建上下文越大，Docker 要扫描和发送给 daemon 的数据就越多，哪怕这些文件最后不参与构建，这部分开销也省不掉。</p>
<p>多阶段构建解决的是另一件事：编译期需要编译器，运行期不需要。第一个阶段装全套工具把东西编出来，第二个阶段只从一个干净的基础镜像开始，把产物 COPY 过来。镜像里不留编译工具链，体积和攻击面都小一圈。</p>
<pre><code>FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
</code></pre>
<h2>关于层数越少越好</h2>
<p>这是被说烂又容易用错的一句话。合并 RUN 确实有意义：一是减少层数带来的元数据开销，二是像更新索引和安装软件必须写在同一层，否则缓存分开后可能装到过期的索引。但为了减层把一堆不相关的命令用连接符串成一坨，出问题根本没法定位是哪一步挂的，可读性会崩。合并的原则是<strong>语义上相关的操作放一起</strong>，不是数字上越少越好。真正该关心的是构建速度和最终体积，而不是 FROM 到 CMD 之间有几行。</p>
""",
    },
    {
        "title": "Nginx 反向代理与负载均衡",
        "content": """<p>反向代理是 Nginx 最常用的用途，但配置里几个不起眼的字符就决定了请求能不能到后端、后端看到的客户端 IP 对不对。这篇讲清正反向代理的区别、proxy_pass 的路径拼接规则、必须转发的请求头，以及 upstream 几种策略怎么选。</p>
<h2>正向代理和反向代理</h2>
<p>区别就一句话：<strong>代理谁、对谁透明</strong>。正向代理站在客户端这边，代表客户端去访问外网，服务端只知道代理的地址，不知道真实客户端是谁。反向代理站在服务端这边，代表一组后端服务器接收请求，客户端以为自己在跟一台服务器说话，完全不知道背后有几台、是哪台。Nginx 做的是后者。还有一点，反向代理顺手就能做 TLS 终止、静态文件托管和压缩，后端只管业务逻辑，这也是它几乎无处不在的原因。</p>
<p>最小可用的配置只有几行，一个 server 块加一条 proxy_pass 就够跑起来：</p>
<pre><code>server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
</code></pre>
<p>这就够跑起来了，但只转发请求不转发头，后端看到的信息还是不全。这类路径和头的问题在本地开发时很难复现，因为本地往往不经过 Nginx，上线才暴露，所以配置改完一定要在真实链路上实际请求一次。</p>
<h2>proxy_pass 结尾那个斜杠</h2>
<p>这是最容易翻车的地方，规则是：<strong>带斜杠等于把匹配到的 location 前缀替换掉，不带斜杠等于原样拼接</strong>。</p>
<ul><li data-list="bullet"><span class="ql-ui"></span>location /api/ 配 proxy_pass http://backend/，请求 /api/user 到后端变成 /user；</li><li data-list="bullet"><span class="ql-ui"></span>location /api/ 配 proxy_pass http://backend，请求 /api/user 到后端还是 /api/user。</li></ul>
<p>后端路由挂在 /api 下而你写成了带斜杠的版本，就会稳定 404。别猜，改完用 nginx -T 看最终配置，再实际请求一次确认路径。</p>
<h2>必须转发的请求头</h2>
<p>反向代理之后，后端拿到的 remote_addr 是 <strong>Nginx 自己的 IP</strong>，不是真实客户端。所有基于 IP 的限流、审计、地域判断都会失效。所以必须显式转发：</p>
<pre><code>location / {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
</code></pre>
<p>Host 不转发的话，后端生成的绝对 URL 和跳转地址会指向错误的主机；X-Forwarded-For 是逗号分隔的链条，每过一层代理追加一个 IP，取第一个才是原始客户端；X-Forwarded-Proto 告诉后端原始请求是 http 还是 https，否则框架会把 https 请求当成 http 处理，重定向成明文地址。还要注意，应用框架通常要显式配置才会信任这些头，比如 Django 的 SECURE_PROXY_SSL_HEADER、USE_X_FORWARDED_HOST，或者 Uvicorn 的 proxy headers 开关，光在 Nginx 里转发、应用不认，一样拿不到真实 IP。</p>
<p>WebSocket 还要额外两行。Upgrade 和 Connection 头<strong>不会被默认转发</strong>，缺了它们握手永远不成功，连接会停在 400 或者被降级成普通请求：</p>
<pre><code>    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
</code></pre>
<h2>upstream 策略怎么选</h2>
<ul><li data-list="bullet"><span class="ql-ui"></span>默认轮询：请求依次分给每台后端，适合后端配置一致、无状态的场景；</li><li data-list="bullet"><span class="ql-ui"></span>weight：给配置不同的节点加权，机器好的多分一点；</li><li data-list="bullet"><span class="ql-ui"></span>ip_hash：按客户端 IP 哈希固定到某台后端，适合还在用本地会话、缓存没共享的过渡期，但机器增减时映射会重新洗牌；</li><li data-list="bullet"><span class="ql-ui"></span>least_conn：把请求给当前连接数最少的那台，适合长连接、请求耗时差异大的场景。</li></ul>
<p>配合 max_fails 和 fail_timeout 决定连续失败几次、多久内把节点摘掉，backup 标记的机器平时不接流量，主节点全挂才顶上。</p>
<pre><code>upstream backend {
    least_conn;
    server 10.0.0.1:8000 weight=3 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8000;
    server 10.0.0.3:8000 backup;
}
</code></pre>
<h2>默认 60 秒超时的坑</h2>
<p>Nginx 的 proxy_read_timeout 默认 60 秒。大文件上传、长时间导出这类请求超过 60 秒，Nginx 就断开连接返回 504，而后端其实还在干活。解决方法是按 location 单独放宽超时，别全局调大，全局调大会让真正卡死的连接一直占着 worker 不放。</p>
<pre><code>location /api/upload/ {
    proxy_pass http://backend;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    client_max_body_size 100m;
}
</code></pre>
<p>另外 client_max_body_size 默认只有 1m，超出会直接返回 413，这跟超时是两回事，别混着排查。</p>
""",
    },
    {
        "title": "Git rebase 与 merge 的区别",
        "content": """<p>merge 和 rebase 都能把分支合到一起，但历史长什么样完全不同，出事的代价也不同。这篇文章讲清两者的机制差异、rebase 的黄金法则、交互式 rebase 的常用操作，以及冲突处理和强推时的注意事项。</p>
<h2>机制差异</h2>
<p>merge 把两个分支的末端和它们的共同祖先做一次三方合并，生成一个<strong>合并提交</strong>，这个提交有两个父节点。原来分支的分叉结构和每个提交的上下文都完整保留，历史是真实发生过的样子，代价是图形会变得很乱。</p>
<p>rebase 则是把当前分支上的提交逐个摘下来，重新应用到新基底上，每个提交都重新生成一遍。<strong>结果是 commit hash 全变了</strong>，因为 hash 由内容、父节点和提交信息算出，父节点变了 hash 必然变。换句话说 rebase 等于重写了历史，不是移动指针，是造了一批新提交。一个直观的判断方法是：如果这段历史要给同事看、要用来追溯问题，就保留真实结构；如果只是你本地还没人看过的整理，怎么干净怎么来。</p>
<h2>黄金法则</h2>
<p>只 rebase <strong>你自己还没 push 的提交</strong>。公共分支上 rebase，别人手里的提交还是旧的 hash，再拉取就会把被删掉的旧提交又合并回来，历史里出现两份内容相同、hash 不同的提交，非常难收拾。</p>
<p>已经 push 过的个人分支要 rebase 也行，但推的时候必须用 <code>git push --force-with-lease</code>。<strong>不要用 --force</strong>：前者会在远端被别人更新过时拒绝推送，相当于加了一道保险；后者是无条件覆盖，会把别人的提交直接抹掉。如果分支有别人在协作，动手前最好打个招呼。</p>
<h2>交互式 rebase</h2>
<p><code>git rebase -i HEAD~3</code> 会列出最近三个提交，操作方式是把每行开头的单词改掉：</p>
<ul><li data-list="bullet"><span class="ql-ui"></span>pick 保持不动；</li><li data-list="bullet"><span class="ql-ui"></span>reword 只改提交信息，内容不动；</li><li data-list="bullet"><span class="ql-ui"></span>squash 把这个提交并进上一个，两段信息会拼在一起让你编辑；</li><li data-list="bullet"><span class="ql-ui"></span>fixup 同样合并，但扔掉这条提交信息；</li><li data-list="bullet"><span class="ql-ui"></span>drop 直接删掉这个提交；</li><li data-list="bullet"><span class="ql-ui"></span>edit 停下来让你改内容，改完 add 之后再继续。</li></ul>
<p>把改错别字、再改一次这类提交压成一个再提 PR，是它最实用的场景。中途乱了用 git rebase --abort 回到起点，不会丢东西。</p>
<h2>--ff 和 --no-ff</h2>
<p>分支基底没变时，Git 默认做 fast-forward：不生成合并提交，直接移动指针，历史是一条直线，看不出这里曾经有过分支。加 --no-ff 则强制生成合并提交，好处是历史上能清楚看到一个功能分支的整体边界，回滚整个功能只要 revert 那一个合并提交。团队协作的主干分支通常用 --no-ff，个人临时分支用默认快进就够了。</p>
<h2>冲突处理的差别</h2>
<p>merge 只在最后合并那一次解冲突，<strong>解一次就完事</strong>。rebase 是把提交一个个重放，如果多个提交都改了同一处，<strong>可能每个提交都要解一次冲突</strong>，而且解的时候面对的是中间状态，容易解出能通过编译但语义错误的代码。提交越多、跨度越长，rebase 的冲突成本越高。</p>
<pre><code># 用远端主干更新本地功能分支
git fetch origin
git rebase origin/main

# 冲突时：改文件 -&gt; git add -&gt; 继续
git add conflicted.py
git rebase --continue

# 发现不对，整个撤掉
git rebase --abort

# 整理最近 3 个提交
git rebase -i HEAD~3

# 覆盖远端，只在个人分支上用
git push --force-with-lease

# 合并时显式保留合并提交
git merge --no-ff feature/login
</code></pre>
<p>总结一句：想要真实历史用 merge，想要干净直线用 rebase，但 rebase 只碰自己还没推的提交。</p>
""",
    },
]

第二步:上 Redis
a. 依赖
requirements.txt 加 redis(redis-py)。别去装 aioredis——那个库已经废弃,异步支持早合并回 redis-py 本身了(redis.asyncio)。版本照你文件的风格钉死,自己 pip install redis 看装到哪个。

b. 配置
setting.py 加 REDIS_HOST,和 DB_HOST 完全同一个模式(环境变量 + 默认值)。

c. 连接
全局建一次 client(redis.asyncio.from_url),放 main.py 的 lifespan 里,别每请求新建。它自带连接池——每个 worker 一个池是正常的,因为状态在服务端,不在池里。

d. compose
第四个 service redis,backend 加一行 REDIS_HOST: redis(和现在 DB_HOST: db 一模一样)。

⚠️ 镜像:你 mysql 那次的教训——镜像是转存到 ACR 的,Docker Hub 在服务器上多半拉不动。redis 镜像也得照做,否则你本地跑得好好的,线上一 up -d 就卡在 pull。

e. 算法
命令	代价
固定窗口	INCR + EXPIRE	边界会漏(59 分和 61 分各发 30 条 = 两分钟 60 条)
滑动窗口	ZSET + Lua	保持你现在 deque 的严格语义,多点代码
建议先做固定窗口,能跑、够用,想升级再说。

f. ⚠️ 一个真坑:INCR 和 EXPIRE 之间有条缝
两条命令不是原子的。如果 INCR 成功、EXPIRE 没执行(进程刚好在这一瞬间挂了),那个 key 就永远不过期 → 这个用户被永久锁死。你的窗口从一小时变成一辈子,比原来的 bug 还糟。

所以不能直白地写"先 INCR 再 EXPIRE"。最干净的是把两条包进一个 Lua 脚本,服务端一口气跑完:


local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return n
(残留隐患:如果 key 存在但没有 TTL——比如你以后改了写法留下的——n 永远不等于 1,TTL 就永远设不上。知道就行。)

g. allow 必须变异步——这里我要纠正我自己
我之前说"调用点一行不用动",那句是错的。函数体里要 await redis,所以 allow 得变成 async def,chat.py:240 的 if not allow(user_id) 就得加 await。

改动还是很小(一行),但"一行不用动"不准确,跟你说清楚。

h. ⚠️ 你的测试会被打破
test_chat.py:96-100:


assert all(allow(uid) for _ in range(LIMIT))
assert allow(uid) is False
allow 一变异步,这两行就在拿协程对象做断言:

all(allow(uid) ...) —— 协程是真值,这行会假通过,什么都没验。
allow(uid) is False —— 这行会失败(顺带一堆 "coroutine was never awaited" 警告)。
假通过比失败更危险,和你文件开头那句"allow 写错则限流形同虚设"是同一类毛病。改法是套 asyncio.run(文件里已经有用例)。

而且注意后果:这个自检文件从此需要一个真的 Redis 在跑。它之前把 OpenAI 客户端都 stub 掉了,是零外部依赖的。要么本机起个 redis,要么把 allow 设计成能注入 client(测试传假的进去),要么把这段挪走。这是个真选择,你得挑一个。

i. 失败策略(要你拍板)
Redis 挂了,是 fail-open(放行)还是 fail-closed(全 429)?

你自己的 docs/ai-chat-v1.md:168 写了:这个项目护的稀缺资源是"公网端点别被人打满",不是 token 钱(我上一轮拿余额说事,跟你文档里的结论不一致,以你的为准)。那就好办了——Redis 挂了不代表端点坏了,限流器不该拖垮聊天功能,我倾向 fail-open + logger.warning。但你得显式选,并且写进文档。

j. 别漏文档
ai-chat-v1/v2/v3 里一堆地方写了 allow 和 _hits:v1 的 194-198、v2 的 95、v3 的 150 和 353。尤其 v3:353 那句"allow 还在外面,不受影响"——改完它就是错的了。

k. 怎么证明改对了
除了修好 test_chat.py 那两行,再加一条能真正抓到原 bug 的:让两个独立进程共享同一份计数,断言合计不超过 LIMIT。

这条测试改之前必然失败(就是今天线上的样子),改完必然通过。这才是"我修好了"的证据,而不是"我看着像对了"。
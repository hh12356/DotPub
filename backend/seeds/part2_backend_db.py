# 由 seed_articles.py 载入，字段名和 Article 模型对齐
ARTICLES = [
    {
        "title": "缓存穿透、击穿与雪崩",
        "content": """<p>缓存能挡住绝大部分读请求，但它失效的方式不止一种。穿透、击穿、雪崩经常被混为一谈，实际上三者的触发条件和解法完全不同。本文先讲清区别，再给出一段 Python 伪代码，用缓存空值加互斥锁重建来同时应对前两种。</p>
<h2>先分清三者的区别</h2>
<p>三个词都指向同一个后果：请求绕过缓存，直接打到数据库。但原因完全不一样。</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>穿透</strong>：要查的数据<em>根本不存在</em>，缓存里永远不会有，每次请求都落到 DB。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>击穿</strong>：数据存在，但某个<em>热点 key 恰好在高并发时刻过期</em>，一瞬间大量请求同时去 DB 重建。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>雪崩</strong>：<em>大量 key 同时过期</em>，或者缓存服务整体不可用，流量整体压向 DB。</li>
</ul>
<p>一句话总结：穿透是「数据不存在」，击穿是「一个热点 key 失效」，雪崩是「一批 key 失效或整层缓存没了」。三者的解法也不通用，拿防穿透的办法去防雪崩，基本没用。</p>
<h2>穿透：布隆过滤器与空值缓存</h2>
<p>典型场景是有人用不存在的 id 刷接口。因为查不到，代码通常不会写缓存，于是每次请求都要查库。两种解法：</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>布隆过滤器</strong>：把存在的 key 预先放进过滤器，请求先过一遍。它判断「不存在」时一定准确，判断「存在」有小概率误判，所以只适合做前置拦截。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>缓存空值</strong>：查不到也写入一个特殊标记，过期时间设短，避免大量空 key 长期占用内存。</li>
</ul>
<p>常见误解是只用其中一种。布隆过滤器会随数据新增产生误判，空值缓存挡不住每次都换一个新 id 的请求，实际项目往往两个一起用。</p>
<h2>击穿与雪崩：锁、抖动与熔断</h2>
<p>击穿的前提是数据确实存在，只是缓存刚好不在。如果放任所有请求去查库，DB 会在极短时间内收到同一个查询的成百上千份副本。</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>互斥锁重建</strong>：只允许一个请求拿到锁去查库并回填缓存，其余请求短暂等待后重试。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>逻辑过期</strong>：key 不设 TTL，把过期时间写在 value 里；发现逻辑过期时异步起一个线程去刷新，其他请求继续返回旧值。用一致性换可用性。</li>
</ul>
<p>如果说击穿是单个 key 的问题，雪崩就是整层缓存同时失效。它的破坏力最大，常见做法：</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span>过期时间加<strong>随机抖动</strong>，比如基础 300 秒再加一段随机值，避免批量写入的 key 同时失效。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>多级缓存</strong>：本地缓存扛一层，Redis 扛一层，DB 前面再留一层保护。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>熔断和限流</strong>：缓存挂掉时直接拒绝部分流量，保住 DB 不被打穿。DB 一旦被压死，恢复时间远长于拒绝请求的代价。</li>
</ul>
<h2>代码：空值缓存加互斥锁</h2>
<p>下面这段伪代码同时处理穿透和击穿，关键点是空值标记和锁的粒度。</p>
<pre><code>import json
import time
import random

EMPTY = "__EMPTY__"

def get_user(user_id):
    key = "user:" + str(user_id)
    cached = redis.get(key)
    if cached is not None:
        return None if cached == EMPTY else json.loads(cached)

    lock_key = "lock:" + key
    # nx=True 表示只有第一个请求能设置成功，也就是抢到了锁
    if redis.set(lock_key, "1", nx=True, ex=3):
        try:
            row = db.query("select * from user where id = %s", user_id)
            if row is None:
                # 空值也缓存，过期时间短，防止被无效 id 刷穿
                redis.set(key, EMPTY, ex=60)
                return None
            ttl = 300 + random.randint(0, 60)
            redis.set(key, json.dumps(row), ex=ttl)
            return row
        finally:
            redis.delete(lock_key)

    # 没抢到锁，等一会儿再看缓存
    time.sleep(0.05)
    return get_user(user_id)
</code></pre>
<p>几个容易踩的点：锁必须带过期时间，否则持锁线程崩溃会导致死锁；递归重试要加次数上限，否则等待的请求可能堆成新的雪崩；空值的过期时间要明显短于正常数据，否则被大量无效 id 刷一遍就要吃满内存。</p>
<h2>小结</h2>
<p>判断问题类型比背解法更重要：查不存在的数据是穿透，热点 key 失效是击穿，批量失效或缓存整体不可用是雪崩。抖动能缓解雪崩但不能解决缓存挂掉，熔断限流才是最后一道防线。</p>
""",
    },
    {
        "title": "Python GIL 到底是什么",
        "content": """<p>很多人把 GIL 说成「Python 不能多线程」，这句话既对又不对。GIL 是 CPython 解释器内部的一把全局互斥锁，不是 Python 语言规范的一部分。理解它到底锁住了什么，才能判断什么时候该用多线程、什么时候必须换多进程。</p>
<h2>GIL 是什么，为什么存在</h2>
<p>GIL（Global Interpreter Lock）是 CPython 用来保护解释器内部状态的全局锁。任意时刻，一个进程里只有一个线程能持有 GIL 并执行 Python 字节码。三个要点：</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span>它是 <strong>CPython 的实现选择</strong>，不是语言标准。Jython 没有 GIL，PyPy 有自己的实现，行为不一定相同。</li>
<li data-list="bullet"><span class="ql-ui"></span>它锁的是<strong>解释器状态</strong>，不是你的数据。指望 GIL 保证线程安全是错的，共享变量的竞态依旧存在。</li>
<li data-list="bullet"><span class="ql-ui"></span>它<strong>不保证原子性</strong>。像 <code>counter += 1</code> 这种语句在字节码层面是读、加、写三步，线程切换照样会丢更新。</li>
</ul>
<p>核心原因是 CPython 的内存管理方式。对象靠<strong>引用计数</strong>回收，每个对象头里有一个计数器，赋值、传参、出作用域都要加减它。如果多个线程同时改同一个对象的计数，不加锁就会算错，导致对象被提前释放或永远不释放。给每个对象配一把锁开销太大，还会引入死锁风险，于是 CPython 选了最简单粗暴的方案：一把全局锁，一次只让一个线程跑字节码。</p>
<p>顺带的收益是 C 扩展好写。扩展作者默认只有一个线程在执行，不用操心解释器状态的竞争。这也是 GIL 一直没被拿掉的重要原因——生态里大量 C 扩展依赖这个假设。</p>
<p>引用计数之外还有<strong>分代 GC</strong>，它负责回收循环引用。两者是互补的：引用计数处理绝大多数对象，分代 GC 定期扫描容器对象找环。GIL 和 GC 是两回事，不要混为一谈。</p>
<h2>实际影响</h2>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>CPU 密集型多线程不提速</strong>。线程之间抢 GIL，还会带来切换开销，跑满多核未必比单线程快。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>IO 密集型有收益</strong>。阻塞式 IO 会主动<strong>释放 GIL</strong>，其他线程可以继续执行，所以网络请求、文件读写用线程池是有效的。</li>
</ul>
<p>常见误解是「IO 密集一定加速」。收益取决于等待时间和线程数，线程开太多反而全是切换开销，通常十几到几十个就够了。</p>
<p>还有一个细节：GIL 的释放有两种触发方式，一是执行到会阻塞的调用时主动释放，二是执行字节码的线程超过切换间隔后被强制让出，间隔长度由 <code>sys.setswitchinterval</code> 控制。所以纯计算的线程也不是一直霸占着锁，只是让出之后大家还得排队，整体仍然只有一个线程在跑。</p>
<h2>绕开 GIL 的方式</h2>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>multiprocessing</strong>：每个进程有独立的解释器和 GIL，能真正并行。代价是进程启动开销、内存不共享、数据要序列化。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>C 扩展主动释放 GIL</strong>：numpy 这类库在做大规模数值计算时会释放 GIL，让多个线程真正并行。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>asyncio</strong>：处理 IO 密集，单线程事件循环，没有线程切换和加锁的开销。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>free-threaded 构建</strong>：CPython 已经在推进去掉 GIL 的版本，但生态兼容和单线程性能还在打磨，别急着把生产代码押上去。</li>
</ul>
<h2>代码：线程与进程对比</h2>
<p>同一段 CPU 密集任务，分别用 4 个线程和 4 个进程跑，耗时差别很明显。</p>
<pre><code>import threading
import multiprocessing
import time

def burn(n):
    total = 0
    for i in range(n):
        total += i * i
    return total

N = 5_000_000

def run_threads():
    workers = [threading.Thread(target=burn, args=(N,)) for _ in range(4)]
    start = time.perf_counter()
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return time.perf_counter() - start

def run_processes():
    with multiprocessing.Pool(4) as pool:
        start = time.perf_counter()
        pool.map(burn, [N] * 4)
        return time.perf_counter() - start

if __name__ == "__main__":
    print("threads:", run_threads())
    print("processes:", run_processes())
</code></pre>
<p>把 <code>burn</code> 换成 <code>time.sleep</code> 或网络请求，结论就会反过来：线程和协程都会明显优于多进程，因为等待期间 GIL 是放开的。</p>
<h2>小结</h2>
<p>GIL 是 CPython 为简化内存管理和 C 扩展编写而做出的取舍。CPU 密集用多进程或 C 扩展，IO 密集用线程或 asyncio，这是最实用的判断标准。同时记住：GIL 保护的是解释器，不是你的数据，该加锁的地方一个都不能省。</p>
""",
    },
    {
        "title": "数据库事务隔离级别与幻读",
        "content": """<p>隔离级别定义了并发事务之间能看到什么、看不到什么。很多人只背下了「RR 能防幻读」，却说不清 InnoDB 到底是靠什么防住的。本文以 MySQL InnoDB 为准，把四种级别、MVCC、快照读与当前读、next-key lock 串起来讲清楚。</p>
<h2>四种级别各防住哪些现象</h2>
<p>先统一三个现象的定义：</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>脏读</strong>：读到了别的事务还没提交的数据。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>不可重复读</strong>：同一事务内两次读同一行，结果不一样，因为别人改了并提交。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>幻读</strong>：同一事务内两次执行同样的范围查询，第二次多出了几行，因为别人插入并提交。</li>
</ul>
<p>标准定义的隔离级别与现象的对应关系：</p>
<ol>
<li data-list="ordered"><span class="ql-ui"></span><strong>READ UNCOMMITTED</strong>：三个都防不住。</li>
<li data-list="ordered"><span class="ql-ui"></span><strong>READ COMMITTED</strong>：防住脏读，防不住不可重复读和幻读。</li>
<li data-list="ordered"><span class="ql-ui"></span><strong>REPEATABLE READ</strong>：防住脏读和不可重复读，标准认为防不住幻读。</li>
<li data-list="ordered"><span class="ql-ui"></span><strong>SERIALIZABLE</strong>：三个都能防住，代价是并发度极低。</li>
</ol>
<p>注意「标准认为」这四个字。InnoDB 的 RR 通过间隙锁把大部分幻读也防住了，这是实现强于标准的地方，也是理解上的第一个坑。</p>
<h2>默认 RR 靠 MVCC 挡住不可重复读</h2>
<p>InnoDB 默认的隔离级别是 REPEATABLE READ。它防不可重复读靠的是 MVCC（多版本并发控制）：每行记录有隐藏的事务 id 和回滚指针，通过 undo log 串成版本链。事务第一次读时生成一个 ReadView，记录当前活跃事务列表，之后所有普通查询都沿着版本链找到可见的那个版本。</p>
<p>关键在于 ReadView 的生成时机：RR 下，ReadView 在事务第一次快照读时生成，之后一直复用，所以整个事务看到的是同一个快照；RC 下，每次快照读都重新生成 ReadView，所以能读到别人刚提交的数据。这一个差别就决定了整个事务的可见性语义。</p>
<h2>快照读、当前读与 next-key lock</h2>
<p>说清 MVCC 的前提是区分两种读：</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>快照读</strong>：普通的 <code>select</code>，走 MVCC，读的是历史版本，不加锁。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>当前读</strong>：<code>select ... for update</code>、<code>select ... lock in share mode</code>、<code>update</code>、<code>delete</code>、<code>insert</code>，读的是最新已提交版本，并且要加锁。</li>
</ul>
<p>这是最容易被忽略的地方：MVCC 只解决快照读的重复读问题，对当前读无效。如果你在事务里用 for update 去查，拿到的一定是最新数据，而不是事务开始时的快照。</p>
<p>幻读发生在范围查询上，光靠行锁锁不住「还不存在的行」。InnoDB 的解法是 next-key lock，即记录锁加上该记录前面的间隙锁，锁住一个左开右闭的区间。这样别的事务往这个区间插入就会被阻塞，范围查询自然不会多出行来。</p>
<p>两个实践中要注意的点：</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span>查询条件命中唯一索引等值查询且记录存在时，next-key lock 会退化成记录锁，只锁那一行。</li>
<li data-list="bullet"><span class="ql-ui"></span>条件没走到索引时，InnoDB 会锁住扫描过的所有记录和间隙，影响范围远超预期。所以范围查询的字段一定要有合适的索引。</li>
</ul>
<h2>为什么很多公司把默认改成 RC</h2>
<p>RC 的缺点是防不住不可重复读，但它有几个很现实的优势：间隙锁在 RC 下基本不生效，锁的范围更小，死锁概率和锁等待明显降低；另外主从复制用 RC 配合 row 格式的 binlog 也更不容易出问题。所以不少互联网公司会把默认隔离级别改成 RC，由业务自己保证必要的读一致性。这是权衡，不是 RC 更「先进」。</p>
<h2>两个 session 的例子</h2>
<p>下面按时间线交替执行，可以看到 RR 下快照读与当前读的差异。假设表 t 主键为 id，已经存在一行 id=10。</p>
<pre><code>-- 会话 A
begin;                                        -- T1
select name from t where id = 10;             -- T2 返回 old

-- 会话 B
begin;                                        -- T3
update t set name = 'new' where id = 10;      -- T4
commit;                                       -- T5

-- 回到会话 A
select name from t where id = 10;             -- T6 快照读，仍返回 old
select name from t where id = 10 for update;  -- T7 当前读，返回 new
update t set name = 'x' where id = 10;        -- T8 更新的是 new
commit;                                       -- T9
</code></pre>
<p>T6 返回旧值不是 bug，是 RR 的快照语义；T7 返回新值说明当前读绕开了快照。如果把 T4 改成往区间里 <code>insert</code> 一行，RR 下 T6 那样的范围查询不会看到新行，而 T7 那样的当前读会看到——这正是间隙锁在起作用的直接体现。</p>
<p>脏读、不可重复读、幻读分别对应不同级别的防护能力；InnoDB 的 RR 用 MVCC 解决快照读的一致性，用 next-key lock 在当前读下防住幻读。记住快照读和当前读的区别，大部分「为什么读到的数据不对」的困惑都能自己解释。</p>
""",
    },
    {
        "title": "SQL 注入原理与防御",
        "content": """<p>SQL 注入常年排在各类安全漏洞榜单前列，但很多人的理解停留在「过滤特殊字符」。这个方向从根上就是错的：注入成立的原因是数据被当成了代码，改变了 SQL 的语法结构。本文从原理讲到防御，重点说清参数化查询为什么是根本解法，以及 ORM 为什么不能自动保平安。</p>
<h2>根本原因：数据变成了代码</h2>
<p>SQL 语句在数据库端要经过解析、生成执行计划、执行三个阶段。问题出在解析这一步：如果用户输入参与了语句拼接，数据库看到的是一整条拼好的 SQL，它无法分辨哪部分是开发者写的结构、哪部分是用户传的值。用户输入里的引号一旦闭合了字符串，后面写的内容就变成了 SQL 语法本身。</p>
<p>所以判断一个写法安不安全，看的不是「有没有过滤特殊字符」，而是「输入有没有机会参与语法解析」。这是本文最重要的一句话。</p>
<p>假设后端这样拼 SQL：</p>
<pre><code>sql = "select * from account where name = '%s' and pwd = '%s'" % (name, pwd)
</code></pre>
<p>正常输入 name=alice、pwd=123456 时，拼出的语句符合预期。但如果 pwd 被填成 <code>' OR '1'='1</code>，拼出来就变成了：</p>
<pre><code>select * from account where name = 'alice' and pwd = '' OR '1'='1'
</code></pre>
<p>原本属于「值」的那段内容，闭合了 pwd 的字符串，插进了一个 OR 和一个恒真条件。WHERE 的布尔结构被改写，条件永远成立，查询返回表里的行，登录判断被绕过。</p>
<p>注意这里没有用到任何高深技巧，只是利用了「值的位置可以被语法结构占据」这一点。这也说明为什么黑名单过滤不可靠：SQL 语法太灵活，等价写法太多，堵不完。</p>
<h2>根本防御：参数化查询</h2>
<p>参数化查询（预编译）的做法是把 SQL 骨架和值分开发送：</p>
<pre><code>import sqlite3

conn = sqlite3.connect("app.db")
cur = conn.cursor()

# 正确：占位符的值由驱动单独发送，不参与 SQL 解析
cur.execute(
    "select * from account where name = ? and pwd = ?",
    (name, pwd),
)
row = cur.fetchone()
</code></pre>
<p>关键在于顺序：数据库先收到并解析带占位符的语句模板，确定了语法结构和参数类型；值是在之后单独传进去的，只会被当作数据填充，不参与解析。哪怕值里全是引号，它也只是一个字符串。</p>
<p>Python 的 DB-API 常见写法用 <code>%s</code> 占位，必须把参数作为 execute 的第二个参数传入，不要自己用 <code>%</code> 或 f-string 拼进去——那样等于没做参数化，只是把拼接换了个地方。SQLAlchemy 的写法类似：</p>
<pre><code>from sqlalchemy import text

stmt = text("select * from account where name = :name and pwd = :pwd")
conn.execute(stmt, {"name": name, "pwd": pwd})
</code></pre>
<h2>补充防御：权限、错误信息和标识符</h2>
<ul>
<li data-list="bullet"><span class="ql-ui"></span><strong>最小权限账号</strong>：应用连库的账号只给必要的 DML 权限，不要给 drop、grant 这类能力。参数化防不住逻辑漏洞，权限能兜底。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>错误信息不外泄</strong>：把数据库原始报错直接返回给前端，等于把表名字段名送给对方。统一包装成通用错误，细节只写进服务端日志。</li>
<li data-list="bullet"><span class="ql-ui"></span><strong>标识符要用白名单</strong>：表名、列名、排序方向没法用占位符——占位符只能填值，不能填语法结构。这类输入必须用固定白名单比对。</li>
</ul>
<pre><code>ALLOWED_SORT = {"created_at", "score", "id"}

if sort_field not in ALLOWED_SORT:
    raise ValueError("invalid sort field")

# 通过白名单校验后，标识符才允许拼接
sql = "select * from article order by " + sort_field + " desc"
</code></pre>
<h2>用了 ORM 也可能中招</h2>
<p>这是最容易被误解的一点。ORM 生成的查询默认是参数化的，但只要你绕开它，风险立刻回来：</p>
<ul>
<li data-list="bullet"><span class="ql-ui"></span>用 <code>raw()</code>、<code>execute()</code> 直接跑拼接出来的 SQL。</li>
<li data-list="bullet"><span class="ql-ui"></span>把用户输入直接拼进 where 条件的字符串，或者拼进 order by、limit。</li>
<li data-list="bullet"><span class="ql-ui"></span>用 ORM 提供的「原生条件」接口去拼字段名。</li>
</ul>
<p>结论很简单：ORM 保护的是它自己生成的那部分语句，不保护你手写的字符串。凡是把用户输入拼进 SQL 的地方，都要按没有 ORM 的情况来审查一遍。</p>
<h2>小结</h2>
<p>注入的本质是数据混进了代码，所以解法也必须作用在「分离」上：值用参数化绑定，标识符用白名单，剩下的交给最小权限和错误处理兜底。另外别忘了密码本身要做加盐哈希存储，这是另一条独立的防线。</p>
""",
    },
]

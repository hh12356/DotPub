# 由 seed_articles.py 载入，字段名和 Article 模型对齐
ARTICLES = [
    {
        "title": "TCP 三次握手为什么不是两次",
        "content": """<p>TCP 建立连接为什么必须是三次握手？很多人背得出 SYN、SYN+ACK、ACK，却说不清第二次握手为什么能合并。本文从「双方各自确认收发能力」这一本质出发，讲清序列号同步、滞留旧报文与 SYN 洪泛的防御思路。</p>
<h2>握手的本质是四次能力确认</h2>
<p>一条 TCP 连接是双向的，两个方向的收发能力都要被确认。站在客户端角度，它要确认自己「发得出去」并且「收得回来」；服务端同理。每一次单向确认需要一个报文，两边加起来正好是四次。</p>
<p>关键在于：一个报文能携带的信息是叠加的。第二次握手时，服务端本来就要回复客户端的 SYN，而「能回这个包」这件事本身就证明了服务端的接收能力和发送能力都正常。于是服务端把自己那两次确认合并进同一个报文，四次确认压缩成三个报文，这就是三次握手的由来。</p>
<pre><code>客户端                                        服务端
  |                                             |
  |  ── SYN (seq=x) ─────────────────────────→  |   客户端: 我发得出去
  |                                             |   服务端: 我收得到
  |  ←── SYN+ACK (seq=y, ack=x+1) ────────────  |   服务端: 我发得出去
  |                                             |   客户端: 我收得到
  |  ── ACK (ack=y+1) ───────────────────────→  |   服务端: 对方确认了
  |                                             |</code></pre>
<h2>为什么要同步 ISN</h2>
<p>TCP 用序列号标记每一个字节，接收方靠它去重、排序、拼装。连接刚建立时双方的序列号都是随机的，叫 ISN（Initial Sequence Number）。之所以随机而不是固定从 0 开始，是为了避免上一次连接的迟到报文被误当成新连接的数据。</p>
<p>三次握手的过程，本质就是双方交换并确认彼此的 ISN：客户端发 SYN 带上自己的 seq；服务端回 SYN+ACK 时既确认对方的 seq，也带上自己的 seq；客户端最后用 ACK 确认回去。两边都拿到了「对方期望我下一次发送的序列号」，连接才真正可用。</p>
<h2>为什么两次握手不够</h2>
<p>假设只有两次握手：客户端发 SYN，服务端回 SYN+ACK 就认为连接建立完毕。问题出在网络中滞留的旧 SYN。</p>
<p>一个早该被丢弃的重复 SYN 报文在链路里晃荡了很久才到达服务端。服务端收到后误以为客户端要新建连接，立刻分配资源、回 SYN+ACK，并进入 ESTABLISHED 状态开始等数据。而客户端根本没打算连接，收到这个莫名其妙的 SYN+ACK 只会回一个 RST 或者直接忽略。结果服务端这边留下一个永远不会被使用、也永远不会被正常释放的连接，白白占用内存和端口资源。</p>
<p>三次握手能挡住这个问题：客户端没有发出过对应的 SYN，自然不会回第三次 ACK，服务端超时后就会回收资源。也就是说，第三次握手的价值在于让客户端有机会否决一次「它从未发起过的连接」。</p>
<h2>半连接队列与 SYN 洪泛</h2>
<p>服务端收到 SYN、回了 SYN+ACK、但还没收到最终 ACK 的连接，存放在半连接队列（SYN queue）里；走完三次握手的连接才进入全连接队列（accept queue）。这两个队列都有长度上限。</p>
<p>攻击者可以伪造大量源 IP 发送 SYN，把半连接队列塞满，正常用户就再也连不进来，这就是 SYN 洪泛。注意它并不需要真的完成握手，成本极低，防御起来却很麻烦。</p>
<p>常见的缓解手段是 SYN Cookie：服务端收到 SYN 时不立即分配资源、不把连接放进半连接队列，而是把「客户端 IP、端口、时间戳」等信息配合自己的密钥算成一个哈希，当作序列号写进 SYN+ACK 发出去。等客户端回 ACK 时，服务端用同样的密钥再算一遍，能对上才认为这次握手有效。这样服务端在握手完成前几乎不保存状态，半连接队列被撑爆的问题就绕开了。</p>
<h2>结尾：TIME_WAIT 与四次挥手</h2>
<p>连接建立是三次，连接关闭却是四次，因为 TCP 是全双工的：一方发出 FIN 只代表「我没有数据要发了」，另一方可能还有数据没发完，所以 ACK 和 FIN 不能合并。主动关闭的一方最后会进入 TIME_WAIT 状态等上 2MSL，目的是保证最后那个 ACK 有机会重传，并让本次连接的迟到报文彻底消失，不至于污染下一次复用同一四元组的新连接。这部分内容足够再写一篇，本文就不再展开了。</p>
""",
    },
    {
        "title": "HTTP 缓存：强缓存与协商缓存",
        "content": """<p>代码明明发版了，用户看到的为什么还是旧页面？本文把强缓存与协商缓存拆开讲清楚：Cache-Control 各指令的含义、ETag 为什么比 Last-Modified 更准、304 省下了什么，并附可直接抄的响应头配置。</p>
<h2>缓存分成两个层次</h2>
<p>浏览器取一个资源，会先看本地有没有可用副本。这个过程分两步：先判断本地副本能不能直接用，这一步叫强缓存；不能直接用，再去问服务器「我手上这份还能用吗」，这一步叫协商缓存。两者的分界线就是到底要不要发请求。</p>
<h2>强缓存：命中就完全不发请求</h2>
<p>强缓存由 Cache-Control 控制，最常用的是 max-age，单位是秒，表示资源在本地可以保持新鲜多久。在有效期内浏览器直接从内存或磁盘缓存里取，DevTools 网络面板里根本看不到这条请求，Size 一栏会显示 from disk cache 或 from memory cache。</p>
<p>常用指令的含义：</p>
<ul><li data-list="bullet"><span class="ql-ui"></span>max-age：相对当前时间的秒数，优先级高于 Expires</li><li data-list="bullet"><span class="ql-ui"></span>public / private：能不能被 CDN 这类共享缓存保存</li><li data-list="bullet"><span class="ql-ui"></span>no-cache：可以存，但每次使用前都要先去服务器确认</li><li data-list="bullet"><span class="ql-ui"></span>no-store：完全不许存，连写进磁盘都不行</li></ul>
<p>Expires 是一个绝对时间点，问题在于它拿服务器的时间去和客户端的时间比较。用户机器时间不准或者跨时区，这个判断直接就错了。max-age 是相对时间，不受时钟偏差影响，所以现在配置里基本只写 Cache-Control，Expires 只当老客户端的兜底。</p>
<h2>协商缓存：发请求，但可能只回 304</h2>
<p>强缓存过期之后进入协商缓存。浏览器把上次拿到的校验信息放进请求头，服务端比对后决定是回 304（你用本地那份）还是 200 加新内容。304 没有响应体，省下的是传输体积，往返时间一点没省。</p>
<ul><li data-list="bullet"><span class="ql-ui"></span>Last-Modified 响应头，对应请求头 If-Modified-Since</li><li data-list="bullet"><span class="ql-ui"></span>ETag 响应头，对应请求头 If-None-Match</li><li data-list="bullet"><span class="ql-ui"></span>两个都存在时，服务端优先看 ETag</li></ul>
<p>ETag 比 Last-Modified 准，原因有三个：一是 Last-Modified 只有秒级精度，一秒内改两次就漏掉了；二是内容没变但文件被重新部署导致修改时间变化，会白白让缓存失效；三是有些响应是动态生成的，压根没有合理的修改时间。ETag 是对内容本身算出的指纹，内容不变指纹就不变。</p>
<h2>no-cache 不等于 no-store</h2>
<p>这是最常见的误解。字面上 no-cache 像是「不缓存」，实际含义是「可以缓存，但每次用之前都要跟服务器确认」——它其实是协商缓存的一种表达方式。真正禁止保存的是 no-store，用在支付页、带隐私数据的接口这类绝对不能落盘的响应上。</p>
<p>一句话记法：no-cache 管的是「用之前要不要问」，no-store 管的是「能不能存」。用错了，会把本该零请求的静态资源变成每次都往返一趟。</p>
<h2>典型踩坑与配置</h2>
<p>最经典的坑是给 index.html 和打包产物都设了很长的强缓存。发版之后文件名没变，浏览器在有效期内死活不发请求，用户拿着旧代码跑新接口，报错还找不到原因。</p>
<p>解法是文件名加 hash：构建工具为每个产物生成内容相关的文件名，内容一变文件名就变，文件名不变就永远不用重新下载。再把入口 HTML 设成 no-cache，它负责引用新的 hash 文件名，每次进来先确认一次即可。</p>
<pre><code># 带 hash 的静态产物：强缓存一年，基本等于永不过期
location ~* \\.(js|css|png|jpg|svg|woff2)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
}

# 入口 HTML：可缓存但要每次校验，保证能拿到新的 hash 文件名
location = /index.html {
    add_header Cache-Control "no-cache";
}

# 接口响应：不许缓存
location /api/ {
    add_header Cache-Control "no-store";
}</code></pre>
<p>最后提醒一句：CDN 上残留的旧缓存是另一个层面的问题，发版时记得刷新 CDN 缓存，或者用带版本号的目录路径来绕开。</p>
""",
    },
    {
        "title": "JavaScript 事件循环与微任务",
        "content": """<p>setTimeout(fn, 0) 为什么总是排在 Promise.then 后面？本文从调用栈和任务队列讲起，说清宏任务与微任务的调度规则，拿一段十行的输出题逐步推演，并解释为什么在微任务里递归会直接卡死页面而不会报错。</p>
<h2>调用栈、任务队列与事件循环</h2>
<p>JavaScript 是单线程的，同一时刻只有一段代码在跑。正在执行的东西放在调用栈里，函数进栈、返回、出栈，栈空了才轮到下一件事。而异步任务的回调不会自己跳回栈里，它们被放进任务队列排队，由事件循环负责在栈空的时候把队首的回调压进栈。</p>
<p>所以事件循环可以粗略概括成一句话：栈空了，就去队列里取一个回调来执行，执行完再看栈空不空。它的本质是一个永不停止的循环。</p>
<h2>宏任务与微任务</h2>
<p>任务队列其实分两种，优先级完全不同：</p>
<ul><li data-list="bullet"><span class="ql-ui"></span>宏任务：setTimeout、setInterval、I/O 回调、用户交互事件、MessageChannel</li><li data-list="bullet"><span class="ql-ui"></span>微任务：Promise.then/catch/finally、queueMicrotask、MutationObserver</li></ul>
<p>最关键的一条规则是：每执行完一个宏任务，就把整条微任务队列清空，清空期间新产生的微任务也一并执行掉，直到队列真的空了，才去取下一个宏任务。也正因为如此，微任务的优先级永远高于下一个宏任务。</p>
<p>async/await 本质上就是 Promise 的语法糖：await 后面的代码相当于被塞进了 then 的回调里，所以它同样是微任务，同样享有插队到下一个宏任务之前的待遇。另外要记住浏览器渲染的位置——一次宏任务执行完、微任务也清空之后，浏览器才有机会做样式计算、布局和绘制，这个顺序正是下面「微任务卡死页面」问题的根源。</p>
<h2>一道输出顺序题</h2>
<pre><code>console.log('script start')

setTimeout(() =&gt; {
  console.log('setTimeout')
}, 0)

Promise.resolve()
  .then(() =&gt; console.log('promise1'))
  .then(() =&gt; console.log('promise2'))

console.log('script end')</code></pre>
<p>输出是：script start、script end、promise1、promise2、setTimeout。逐步推演：</p>
<ol><li data-list="ordered"><span class="ql-ui"></span>整段脚本本身就是一个宏任务，开始执行，先打印 script start</li><li data-list="ordered"><span class="ql-ui"></span>遇到 setTimeout，把回调注册进定时器，0 毫秒后把回调丢进宏任务队列，此时脚本还远没跑完</li><li data-list="ordered"><span class="ql-ui"></span>Promise.resolve() 已经是完成状态，第一个 then 的回调被丢进微任务队列</li><li data-list="ordered"><span class="ql-ui"></span>打印 script end，这个宏任务的同步代码执行完毕</li><li data-list="ordered"><span class="ql-ui"></span>清空微任务队列：先跑第一个 then 打印 promise1，它返回后第二个 then 被追加进队列，接着打印 promise2</li><li data-list="ordered"><span class="ql-ui"></span>微任务队列空了，事件循环去取下一个宏任务，也就是 setTimeout 的回调，最后打印 setTimeout</li></ol>
<h2>setTimeout(fn, 0) 不是立刻执行</h2>
<p>以为写 0 就等于马上跑，是另一个常见误解。这个 0 只表示「至少等 0 毫秒」，回调仍然要走完「进宏任务队列、排队等前面所有任务和微任务结束」的完整流程。而且浏览器对嵌套的定时器有最小延迟钳制，实际间隔往往比写的数字大。想在当前任务结束后尽快执行，用 queueMicrotask 或者 Promise.resolve().then，它们会插到微任务队列里，比任何定时器都早。</p>
<h2>微任务里递归为什么会卡死页面</h2>
<p>渲染也是一个任务，它同样要排队等调用栈空出来。如果在微任务里一直产生新的微任务，清空微任务队列这一步就永远不会结束，事件循环根本没机会走到渲染那一步，页面自然完全没反应，连点击事件都排不上队。</p>
<p>更麻烦的是这种卡死通常是静默的：没有报错，没有栈溢出提示，CPU 跑满，DevTools 的 Performance 面板上看到的就是一条一直不结束的任务。所以写「不断自我调度的微任务」时一定要有终止条件，或者改成 setTimeout、requestAnimationFrame 这类会让出控制权的宏任务。</p>
""",
    },
    {
        "title": "React useEffect 依赖数组的陷阱",
        "content": """<p>useEffect 的依赖数组是 React 里最容易写错的地方：漏写依赖会读到旧值，多写又会陷入无限循环。本文讲清闭包捕获、对象依赖与空数组的真正含义，并解释清理函数与 StrictMode 的行为。</p>
<h2>effect 捕获的是那一次渲染的值</h2>
<p>函数组件的每一次渲染，都是重新调用一次函数。这次调用里产生的 props、state、局部变量，被这一次的 effect 闭包捕获下来，就固定住了，之后再也不会变。不是 React 故意为难人，而是 JavaScript 闭包本来的行为。</p>
<p>理解了这一点，后面所有坑都能自己推出来：effect 里读到的永远不是「当前最新的值」，而是「定义这个 effect 的那次渲染的值」。</p>
<h2>漏依赖：setInterval 里永远是 0</h2>
<pre><code>function Counter() {
  const [count, setCount] = useState(0)

  useEffect(() =&gt; {
    const id = setInterval(() =&gt; {
      console.log(count)      // 永远是 0
      setCount(count + 1)     // 也永远把它设成 1
    }, 1000)
    return () =&gt; clearInterval(id)
  }, [])                      // 漏了 count
}</code></pre>
<p>空数组意味着这个 effect 只在挂载时跑一次，它捕获的 count 就是首次渲染的 0。定时器每秒打印 0，每秒把 count 设成 1，界面永远停在 1。这就是漏依赖最典型的后果：读到旧值，而且症状看起来完全莫名其妙。</p>
<p>把 count 加进依赖数组能修好，但定时器会被反复销毁重建，不是最优解。更好的写法是用函数式更新 setCount(c =&gt; c + 1)，这样 effect 不再依赖 count，数组保持为空也不会读到旧值。</p>
<h2>对象和函数依赖导致的无限循环</h2>
<p>React 用 Object.is 逐项比较依赖。对象、数组、函数的比较是引用比较，哪怕内容一模一样，每次渲染都是新的一份引用，比较结果永远是不相等，effect 就会每次都重新执行。如果 effect 里还调用了 setState，就会渲染、跑 effect、再渲染，直接死循环，控制台刷满请求，页面卡住。</p>
<p>三种解法，按推荐程度排：把依赖拆成原始值，比如依赖 user.id 而不是整个 user；用 useCallback / useMemo 稳定引用；把真正需要的逻辑挪进 effect 内部，减少外部依赖。第一种最省事也最难写错。</p>
<h2>空数组不等于「只跑一次还能看到最新值」</h2>
<p>很多人把依赖数组当开关：空数组等于只跑一次。这句话本身没错，但这只是「只跑一次」，并不附带「永远能看到最新值」的效果。两者在闭包里是矛盾的：只看一次，就必然只能看到那一次的值。</p>
<p>想在只跑一次的前提下读到最新值，需要用 ref 存一份。每次渲染把最新的值写进 ref.current，effect 里读 ref.current，因为它是一个可变盒子，读到的是写进去的最新内容。这个模式在定时器、事件订阅里非常常用。</p>
<h2>清理函数的时机与 StrictMode</h2>
<p>effect 返回的函数叫清理函数，它在两个时刻执行：组件卸载前，以及下一次 effect 重新执行之前。注意顺序是「先清理上一次，再执行这一次」，所以依赖数组变化时，你会看到清理和重建交替出现。</p>
<p>拿定时器举例就很直观：依赖变化时先 clearInterval 掉旧的，再开一个新的，日志里呈现「清理、启动、清理、启动」的交替。如果清理函数里漏了 clearInterval，定时器就会越堆越多，组件卸载后回调还在跑，页面越用越卡，而且非常难排查。凡是订阅、定时器、监听器，都必须在清理函数里释放。</p>
<p>React 18 的 StrictMode 在开发环境下会把每个 effect 跑两次：挂载、执行、清理、再执行，目的是提前暴露清理函数写得不对的问题。所以开发时看到请求发了两次、日志打了两遍，先别急着删 StrictMode，检查一下清理函数是否真的把副作用收干净了。生产构建里不会重复执行。</p>
""",
    },
]

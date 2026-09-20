# DeepSeek 聊天悬浮窗 v2：SSE 流式

## Context

v1 已经跑通：点悬浮球 → 抽屉 → 提问 → 三到十秒后整段回答砸下来。

v2 只改一件事：**把回答从"憋完再吐"改成"边生成边吐"**。首字延迟从 3–10 秒降到 0.5 秒左右，观感差别很大。

好消息是改动面很小：**请求体一个字都不用改**。`ChatData`、`build_messages`、`allow`、`plain_text` 全部原样保留——流式改的是**响应**，不是请求。历史照样由前端整包带过来。

改 4 个文件：后端 2 个（`chat.py`、`test_chat.py`），前端 2 个（`apis/chat.jsx`、`ChatFloat/index.jsx`）。Nginx 大概率不用动，理由在步骤 5。

---

## 全局设计：流式唯一真正难的地方

**HTTP 只有一个状态码，而它在你吐出第一个字的那一刻就已经发出去了。**

这是 v2 全部设计的源头。v1 里 `try/except` 圈住整个调用，任何错都能翻成 503/504 再 `raise HTTPException` 返回。v2 一旦开始吐字，响应头已经躺在网线上了——**此后无论发生什么，你都改不了状态码**，只能在流里表达。

三条推论，后面每一步都围着它们转：

1. **所有"失败时你希望用户看到 4xx/5xx"的事，必须在返回 `StreamingResponse` 之前做完。** 鉴权、限流、查文章、拼 messages、以及**发起上游请求**——全在前半段。
2. **上游 402/429 能不能在前半段抓到，取决于 openai SDK 什么时候真正发 HTTP。** 这个必须实测（步骤 0 的 curl A），不能猜。
3. **流开始之后才炸的**（网络断、上游超时），只能发一个错误帧，或者直接断流。**前端必须能区分"正常结束"和"断了"**，否则用户会对着一个永远转圈的空气泡发呆。

还有个小坑：**SSE 是按行解析的**。模型回答里的换行符如果直接写进 `data:` 后面，会变成帧内换行，前端解析直接错位。所以载荷一律 JSON 编码（JSON 会把 `\n` 转义成 `\\n`），顺带也保住了首尾空格。

---

## 文件地图

| 步骤 | 文件 | 新建/修改 |
|---|---|---|
| 1 | `backend/apis/chat.py` | 改（1a 路由拆两半、1b 生成器、1c usage） |
| 2 | `backend/tests/test_chat.py` | 改（加一个流式自检） |
| 3 | `frontend/src/apis/chat.jsx` | **重写**：axios → 原生 fetch |
| 4 | `frontend/src/components/ChatFloat/index.jsx` | 改（`onSend` 换成流式） |
| 5 | 线上 Nginx | 大概率不改，见步骤 5 |

---

## 后端

### 步骤 0：先跑两条 curl，别信文档

> **实测结论（2026-09-19，两条都跑过了）**
>
> - **curl A → 400。** 非 2xx 是作为 **HTTP 状态码**回来的，不是流里的一帧 → `await create(stream=True)` 当场就抛 → **v1 的 `except APIStatusError` 原地不动，不用挪。**
> - **curl B → 有 `"choices":[]` + `"usage":{...}` 的那一帧。** `stream_options` 参数名正确，`STREAM_OPTS` 保留。
>
> 顺带两个推论：① 生成器里 `if not chunk.choices: continue` 是**承重的，不是死代码**，删了就是 IndexError；② 上游的 400 会落到 v1 那句兜底 `503 "AI 服务出错"`——这是对的，400 意味着你自己的代码写错了（模型名/参数名），那是给日志看的，不该翻译成人话给用户。
>
> 下面两段保留原始推理过程，不用再跑一遍。

v1 已经教过一次：**文档和搜索对 DeepSeek 的参数写法毫无可信度。** 下面两件事我都不敢替你写死，你有 key，你是唯一能拿到权威答案的人。

**curl A —— 上游的 402/429 到底在哪一刻抛？**

这条决定了 v1 那个 `except APIStatusError` 能不能原封不动留着。故意用一个不存在的模型名，看报错是在"调用返回时"就炸，还是"读流读到一半"才炸：

```bash
curl -N -s -o /dev/null -w '%{http_code}\n' https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-nonexistent","messages":[{"role":"user","content":"hi"}],"stream":true}'
```

- 立刻返回 422/404（**没开始吐字节**）→ SDK 是先发请求拿响应头、再交给你流，`except APIStatusError` 保持原位就够，**这是预期结果**。
- 返回 200 然后流里冒出个错误帧 → 那你得在生成器里也做一遍错误翻译，代码要多一层。

**curl B —— usage 怎么拿？**

`stream=True` 之后 `resp.usage` 就不存在了，usage 要么不发，要么挂在**最后一帧**。要拿它得显式请求：

```bash
curl -N -s https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-flash","messages":[{"role":"user","content":"1+1=?"}],"stream":true,"stream_options":{"include_usage":true}}' \
  | tail -5
```

看最后几帧：

- 出现一帧 `"choices":[]`、带 `"usage":{...}` → 参数名对了，步骤 1c 照抄。
- 没有 → 去掉 `stream_options` 再试一次，还是没有就接受现实：**流式模式下拿不到 usage，缓存命中率就没法在生产上看了**。那就本地用非流式（v1 的代码）复验缓存，生产只认功能。

> 注意 `stream_options` 是 OpenAI 的字段，DeepSeek 认不认是另一回事。不认的话放在 `extra_body` 里可能被忽略也可能报 422——所以是 curl 说的算，不是我说的算。

---

### 步骤 1：`backend/apis/chat.py`

改动集中在文件末尾。前面那些（`client`、`SYSTEM_PROMPT`、`plain_text`、`build_messages`、`allow`、`ChatData`）**一行都不用动**，只在 import 区补两个：

```python
import json
from fastapi.responses import StreamingResponse
```

**1a. 路由拆成"准备"和"流"两半**

现在的路由是一条直线：校验 → 查文章 → 调用 → return。改成在"调用"之后返回一个生成器，而不是等它写完：

```python
@chat_api.post("/chat")
async def chat(data: ChatData, token_data: Annotated[dict, Depends(verify_token)]):
    # ↓↓↓ 这一段全部在返回之前跑完，这里的异常还能变成状态码 ↓↓↓
    user_id = token_data["user_id"]
    if not allow(user_id):
        raise HTTPException(status_code=429, detail={"code": 429, "msg": "聊得太快了，休息一下"})

    title = ""
    text = ""
    if data.art_id:
        article = await Article.get_or_none(art_id=data.art_id)
        if article:
            title, text = article.art_title, plain_text(article.art_content)

    try:
        stream = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=build_messages(title, text, data.history, data.question),
            extra_body={**THINKING_OFF, **STREAM_OPTS},
            stream=True,
        )
    except APIStatusError as e:
        ...                              # ← v1 这段原样保留，只把 resp 换成 stream
    except (APITimeoutError, APIConnectionError):
        ...
    # ↑↑↑ 到这里为止，出错仍然是干净的 4xx/5xx ↑↑↑

    return StreamingResponse(
        sse(stream),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**关键在 `await create(stream=True)` 上面那个 `await`。** 它已经把 HTTP 请求发出去了、响应头也收回来了，只是正文还没读完——所以 402/429 在这一刻就抛出来了，v1 的错误处理一行都不用挪。**这正是 curl A 要证实的事**，实测不是这样的话回来找我。

顺带：`THINKING_OFF` 和 `STREAM_OPTS` 都是模块级常量，**别在调用处内联**——它们是前缀缓存区之外的参数，但保持常量写法读起来和 v1 一致。

```python
STREAM_OPTS = {"stream_options": {"include_usage": True}}   # curl B 说不支持就删掉这个常量
```

**1b. 生成器 + 帧打包**

两个纯函数/生成器，放在 `build_messages` 旁边（纯函数区）：

```python
def sse_pack(payload: dict) -> str:
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"


async def sse(stream):
    usage = None
    try:
        async for chunk in stream:
            # usage 挂在最后一帧，而那一帧的 choices 是空的——先取 usage 再过滤
            if chunk.usage:
                usage = chunk.usage
            if not chunk.choices:
                continue
            piece = chunk.choices[0].delta.content
            if piece:
                yield sse_pack({"t": piece})
    except Exception:
        logger.warning("stream broke", exc_info=True)
        yield sse_pack({"e": "回答中断了，再问一次试试"})
    if usage:
        logger.info("chat usage: %s", usage)
    yield "data: [DONE]\n\n"
```

四个点，每个都有代价：

- **`ensure_ascii=False`**。默认 `True` 会把每个汉字转成 `中` 这样的六字符转义——能跑，但帧体积大好几倍，浏览器 Network 面板里也没法看。全中文的产品，这一行必须加。
- **顺序不能反**。`if not chunk.choices: continue` 必须在取 usage **之后**。反过来的话 usage 那一帧会被直接跳过，你永远拿不到缓存命中数字。这个 bug 不报错，只是让你瞎。
- **`except Exception` 不是为了吞异常，是为了让流"有尊严地结束"**。上游从中间断了，你没法改状态码；发一帧 `{"e": ...}` 再发 `[DONE]`，前端就能弹个红字而不是转圈到天荒地老。注意 `asyncio.CancelledError` 继承自 `BaseException`，**不会被这里捕获**——用户关掉抽屉时生成器被取消是正常路径，不该走这个 except。
- **`[DONE]` 是"我正常讲完了"的标记，不是废话**。没有它，前端无法区分"讲完了"和"网线被拔了"，因为两者都是 reader 结束。

**1c. usage**

就是 1b 里那三行。**这行日志现在是验证前缀缓存有没有生效的唯一手段**，别省。流式下它出现在最后，所以要看完整的一次对话日志才能看到——本地开着终端，或者线上 `journalctl -u dotpub -f`。

---

### 步骤 2：`backend/tests/test_chat.py` 加自检

v1 那个文件继续用，追加两项（照旧裸 `assert`，不加 pytest）：

**一是 `sse_pack` 的形状**：以 `\n\n` 结尾；正文里的换行被转义成了 `\\n` 而不是真的换行；中文没被转成 `\uXXXX`：

```python
raw = sse_pack({"t": "第一行\n第二行"})
assert raw.endswith("\n\n")
assert raw.count("\n") == 2          # 只有收尾那俩，正文里的换行被 JSON 吃掉了
assert "第一行" in raw                # 没被 escape 成 \uXXXX
```

**二是把生成器跑一遍**——这个比 1 值钱，因为 `chunk.choices` 为空导致 `IndexError` 是 v2 上线后最常见的崩法，而它只在真实响应里出现：

用 `types.SimpleNamespace` 造几个假 chunk（记得包含那一帧 `choices=[]` 但带 usage 的），`asyncio.run` 收一遍输出：

```python
import asyncio
from types import SimpleNamespace

def _chunk(piece=None, usage=None):
    choices = [SimpleNamespace(delta=SimpleNamespace(content=piece))] if piece is not None else []
    return SimpleNamespace(choices=choices, usage=usage)
```

断言：输出拼起来等于「你好」；`[DONE]` 在最后；带 usage 的那一帧没让程序崩。

---

## 前端

### 步骤 3：`frontend/src/apis/chat.jsx` 重写

**为什么必须换掉 axios**：浏览器里的 axios 走 XHR，**响应体是一次性给你的**，没有 `response.body.getReader()` 这种"读一点给一点"的口子。所以不是"axios 慢"，是它拿不到流。

换了之后有个连带损失：`utils/request.jsx` 的两个拦截器都不再作用于此请求——**JWT 头要手动带，401 要手动处理**。

```jsx
import { getToken, removeToken } from "@/utils/token"
import { removeUserName } from "@/utils/userName"
import router from "@/router"

export async function ChatStream({ question, art_id, history }, onText) {
    const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ question, art_id, history }),
    })

    if (!res.ok) {
        if (res.status === 401) {          //拦截器没了，这里补上
            removeToken(); removeUserName(); router.navigate('/login')
        }
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail?.msg || '请求失败，请稍后重试')
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const frames = buf.split('\n\n')
        buf = frames.pop()                 //最后一段可能是半截帧，留着
        for (const frame of frames) {
            if (!frame.startsWith('data: ')) continue
            const payload = frame.slice(6)
            if (payload === '[DONE]') return
            const msg = JSON.parse(payload)
            if (msg.e) throw new Error(msg.e)
            if (msg.t) onText(msg.t)
        }
    }
}
```

**三个必踩的坑，一个都别省：**

1. **`decoder.decode(value, { stream: true })`** —— 不加 `{stream:true}`，一个 3 字节的汉字被 TCP 恰好切在两段中间时，前半段会解成 `�`，而且**这会真的发生**，因为你的回答全是中文。TextDecoder 内部要留着那半个字符等下一段。
2. **`buf` + `split('\n\n')` + `pop()`** —— 网络给的分片和 SSE 的帧**没有任何对齐关系**。一个 `data: {...}` 完全可能被劈成两次 `read()`。必须自己攒缓冲区，只处理完整的帧，把最后那截不完整的留到下一轮。这是 SSE 最经典的 bug，症状是"偶尔少几个字"。
3. **`frame.slice(6)`** —— `'data: '` 正好 6 个字符。写死数字不好看，但这是 SSE 规范定的前缀，行业惯例。

注意错误分两种来源，都从 `ChatStream` 里 `throw` 出来，调用方一个 `catch` 兜住：HTTP 层（`!res.ok`）和流内错误帧（`msg.e`）。

### 步骤 4：`ChatFloat/index.jsx` 的 `onSend`

v1 的流程是"发出去 → 等一整段 → push 一条"。v2 要变成"先 push 一个空气泡，然后一个字一个字往里填"。

```jsx
const onSend = async () => {
    const question = input.trim()
    if (!question || loading) return

    const history = msgs
    //先占位：用户这句 + 一个空的 Dot 气泡
    setMsgs([...history, { role: 'user', content: question }, { role: 'assistant', content: '' }])
    setInput('')
    setLoading(true)

    let got = ''
    try {
        await ChatStream({ question, art_id: artId, history }, t => {
            got += t
            setMsgs(prev => {
                const last = prev[prev.length - 1]
                return [...prev.slice(0, -1), { ...last, content: last.content + t }]
            })
        })
    }
    catch (e) {
        message.error(e.message)
        //一个字都没吐出来才整轮撤回、问题还回输入框；吐了一半就留着，别让答案凭空消失
        if (!got) {
            setMsgs(prev => prev.slice(0, -2))
            setInput(question)
        }
    }
    finally {
        setLoading(false)
    }
}
```

要点：

- **`history` 必须在 push 之前抓**（v1 就是这个写法，别改）。
- **`got` 用局部变量记，不是 ref**。`onText` 是同步回调，全程在同一个 async 函数里，闭包直接读得到。
- **占位气泡是新的**。v1 失败时 `slice(0,-1)` 撤一条，现在要 `slice(0,-2)` 撤两条。
- **别在 `setMsgs` 的更新函数里调 `setInput`**——那是个 reducer，StrictMode 下会跑两遍。所以判断放在外面用 `got`。

**渲染那行跟着改一处**：v1 是 `{loading && <div ...>思考中…</div>}` 单独一个气泡，现在空气泡已经在了，直接拿它显示占位文字：

```jsx
{msgs.map((m, i) => (
    <div key={i} className={`chat-msg chat-msg-${m.role}`}>
        {m.content || '思考中…'}
    </div>
))}
```

（`loading` 那三行删掉。`useEffect` 的滚动依赖照旧 `[msgs, loading]`，`msgs` 每个字都在变，正好一直贴着底。）

> 没做"停止生成"按钮。要做的话是在 `ChatStream` 里接一个 `AbortController` 传给 `fetch`，再把 `signal` 暴露出来——需要就说。

### 步骤 5：线上 Nginx —— 先别改

**v1 的计划里写的是"必须给 `/api/chat` 加 `proxy_buffering off;`"。v2 有更省事的办法：响应头里那个 `X-Accel-Buffering: no`（步骤 1a 已经加了）。** Nginx 认这个头，会为这一个响应关掉攒包，**配置文件一行都不用动**。

所以上线顺序是：

1. 后端和前端照常传上去，**先什么都不改**，直接点一次悬浮球。
2. 逐字往外蹦 → 完事，Nginx 保持原样。
3. 还是先卡几秒再一坨出来 → 按顺序查：
   - 浏览器 Network 面板看 `/api/chat` 的**响应头**里有没有 `x-accel-buffering: no`。没有 = 中间有东西把它吃了（比如某层代理），先解决这个。
   - 有但还是攒包 → 那才去改 Nginx，在 `/api/chat` 的 location 里加 `proxy_buffering off;`。
   - 还看 `gzip`：`gzip_types` 默认只有 `text/html`，不含 `text/event-stream`，所以一般没事；万一被加过，gzip 也会攒包。

验证命令（`-N` 是关掉 curl 自己的缓冲，不加的话你看到的是 curl 在攒）：

```bash
curl -N -X POST https://你的域名/api/chat \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"question":"这篇在讲什么","art_id":1}'
```

本地如果就不流式，先怀疑 Vite 的 dev proxy（`vite.config.js` 那段 `server.proxy`），它默认是透传的，一般没问题。

---

## 验证

**后端**
1. `python tests/test_chat.py` —— 老的 + 新的流式自检都过
2. 起本地后端，用浏览器 sessionStorage 里的 token 打上面那条 `curl -N`：字应该**一段一段**冒出来，最后有 `data: [DONE]`
3. **同文章连问两次**，看终端里第二次的 `chat usage:` 的 `prompt_cache_hit_tokens` 是不是明显不为 0 —— 消息顺序排对了的唯一证据（curl B 不支持 `stream_options` 的话，这条只能在 v1 的非流式代码上验）

**前端**
4. `npm run dev`，进一篇文章提问，**肉眼确认是逐字出**，不是卡三秒猛地弹一坨
5. 问一个长问题（"把这篇总结成十点"），中途点关闭抽屉再打开——不该白屏，不该报错
6. 把后端停掉再发一句：红字是中文、空气泡被撤掉、问题回到输入框
7. 吐到一半断网（拔网线或 devtools 切 offline）：应该出现"回答中断了"，**已吐出的半截保留**，不是整个消失

**上线**
8. 传后端 + 传前端 dist → 点一次看是否逐字。Nginx 大概率不用动（步骤 5）
9. `journalctl -u dotpub -f` 看一次完整对话的行尾日志

---

## 这次明确不做的

- **停止生成按钮**（`AbortController`）—— 不是必须的，用户关抽屉就等价于停
- **断线重连 / `Last-Event-ID` 重放** —— SSE 有这个能力，但对话流不需要：让用户重问一句比补播中间那几个字简单得多
- 会话落库、v1 的其它"不做"项，照旧
- **v3（Function Calling / 让模型自己检索文章）** —— 那是下一步

---

## 参考

- v1 的完整决策与坑：`docs/ai-chat-v1.md`
- 前缀缓存规则（**流式不影响它，v1 的消息顺序照旧**）：https://api-docs.deepseek.com/zh-cn/guides/kv_cache/
- SSE 规范（帧格式、`data:` 前缀、为什么按 `\n\n` 切）：https://html.spec.whatwg.org/multipage/server-sent-events.html

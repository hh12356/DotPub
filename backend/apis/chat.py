import logging
import re
import uuid
from html import unescape
from typing import Annotated

import nh3
from fastapi import APIRouter, Depends, HTTPException
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, Field

from core.security import verify_token
from core.setting import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, REDIS_HOST, REDIS_PORT
from models.article import Article

import json
from fastapi.responses import StreamingResponse

import redis
from redis.exceptions import RedisError

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=30.0,
)

#异步redis
r = redis.asyncio.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    #redis-py 8 默认发 RESP3 的 HELLO 握手，5.0 的服务器不认，必须退回 RESP2
    protocol=2,
    decode_responses=True,
    #池子满了不会排队，直接抛 MaxConnectionsError。所以这个数要盖过"同时有多少个
    #allow() 在飞"，而不是"平时有多少流量"。2 个 worker 各有一份，互不影响
    max_connections=50
)

SYSTEM_PROMPT = (
    "你是 Dot，DotPub（一个技术文章社区）的站内助手。"
    "用简体中文回答，直接给结论，不要客套。"
    "如果用户正在阅读某篇文章，文章正文会一并提供给你，请优先依据它回答；"
    "正文里没有写的内容不要编，直接说明文章里没有提到。"
    "站里其它文章的内容你不知道，需要时用 search_articles 查，查到标题后用 read_article 读全文。"
    "搜不到就说站里没有，不要凭记忆编造站内的文章。"
    "返回文章时不要暴露文章id"
)

#工具定义，内容会跟着请求发上去，属于提示词的一部分，必须是模块级常量
TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_articles",
        "description": "按关键词搜索 DotPub 站内的文章标题，返回匹配文章的 art_id 和标题。",
        "parameters": {
            "type": "object",
            "properties": {"keyword": {"type": "string", "description": "搜索关键词，比如 Redis"}},
            "required": ["keyword"],
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "read_article",
        "description": "读取站内某篇文章的全文。art_id 必须来自 search_articles 的返回。",
        "parameters": {
            "type": "object",
            "properties": {"art_id": {"type": "integer", "description": "文章 id"}},
            "required": ["art_id"],
        },
    },
}]

#最多几轮。查一次(search) + 读一次(read) + 出答案 = 3
MAX_ROUNDS = 3

#关闭DS思考模式，打开即enabled
THINKING_OFF = {"thinking": {"type": "disabled"}}

#流式模式下 usage 只挂在最后一帧，要显式索要
STREAM_OPTS = {"stream_options": {"include_usage": True}}

MAX_HISTORY = 20
WINDOW = 3600
LIMIT = 30

#拿到报错日志
logger = logging.getLogger("uvicorn.error")


#剥掉html标签
def plain_text(raw: str) -> str:
    with_breaks = re.sub(r"</(?:p|div|li|h[1-6])>|<br\s*/?>", "\n", raw or "", flags=re.I)
    return unescape(nh3.clean(with_breaks, tags=set()))


#刻意不 await：路由里 await 它，第一轮的报错就还是 503/504
def new_stream(messages, last=False):
    return client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        tools=TOOLS,
        #最后一轮 tool_choice 设 none，逼它出文字；tools 照传，前缀才不破
        tool_choice="none" if last else "auto",
        #关闭思考模式并提供流式相关参数
        extra_body={**THINKING_OFF, **STREAM_OPTS},
        stream=True,
    )

#把字典包装成 SSE 协议字符串
def sse_pack(payload: dict) -> str:
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"

#模型调用工具的入口函数
async def run_tool(name: str, args_json: str) -> str:
    #模型给的是字符串，可能会拼出不合法 JSON
    try:
        args = json.loads(args_json or "{}")
    except ValueError:
        return "参数不是合法 JSON"

    #搜索文章功能
    if name == "search_articles":
        keyword = str(args.get("keyword") or "").strip()
        if not keyword:
            return "关键词为空"
        #和 apis/article.py 的 /search 同一个查询
        rows = await Article.filter(art_title__icontains=keyword).limit(5).values("art_id", "art_title")
        if not rows:
            return "站里没有标题含这个词的文章"
        #把python对象转成json，ensure_ascii=False保留原始中文
        return json.dumps(rows, ensure_ascii=False)

    #阅读文章功能
    if name == "read_article":
        #模型输出喂进数据库查询，是信任边界，类型必须自己收
        art_id = args.get("art_id")
        if not isinstance(art_id, int):
            return "art_id 必须是整数"
        article = await Article.get_or_none(art_id=art_id)
        if not article:
            return "没有这个 art_id 的文章"
        return f"《{article.art_title}》：\n\n{plain_text(article.art_content)}"

    #模型自己编出来的工具名（它会），别把 KeyError 漏出去
    return f"没有名为 {name} 的工具"

 #一次工具调用在流里被切成几十片，将他拼为合法json
def merge_tool_calls(calls: dict, deltas) -> None:
    for tc in deltas or []:
        #setdefault 而不是取值判断，不存在就新建
        slot = calls.setdefault(tc.index, {"id": "", "name": "", "args": ""})
        if tc.id:
            slot["id"] = tc.id
        #name 用 += ：分片是"search_" + "articles"，直接赋值会丢掉前半截
        if tc.function.name:
            slot["name"] += tc.function.name
        if tc.function.arguments:
            slot["args"] += tc.function.arguments


#v3 相对 v2 的改动：外面套了 MAX_ROUNDS 层循环，多收一个 messages（工具往返要往里接消息，
#所以列表得是可变的、从路由传进来）。轮内清空 calls；取整个 delta 而不只是 .content，好顺带收 tool_calls；
#轮末把 assistant(tool_calls) 和 tool 结果接回 messages，再开下一轮的流。
#取 usage、过滤空 choices、if d.content、except、收尾 [DONE] 这五处一行没动。
async def sse(stream, messages):
    try:
        for i in range(MAX_ROUNDS):
            calls = {}
            async for chunk in stream:
                #记录token消耗及退出
                if chunk.usage:
                    logger.info("chat usage: %s", chunk.usage)
                # .choices是候选回答 
                if not chunk.choices:
                    continue

                # .delta是本轮增加部分
                d = chunk.choices[0].delta
                merge_tool_calls(calls, d.tool_calls)
                if d.content:
                    yield sse_pack({"t": d.content})
            #本轮生成完成，进入工具调用

            #模型没要工具，这一轮就是最终答案
            if not calls or i == MAX_ROUNDS - 1:
                break

            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": c["id"], "type": "function",
                     "function": {"name": c["name"], "arguments": c["args"]}}
                    for c in calls.values()
                ],
            })
            for c in calls.values():
                messages.append({
                    "role": "tool",
                    "tool_call_id": c["id"],
                    "content": await run_tool(c["name"], c["args"]),
                })

            #i == MAX_ROUNDS-2 说明下一轮就是最后一轮了
            stream = await new_stream(messages, last=(i == MAX_ROUNDS - 2))
    except Exception:
        logger.warning("stream broke", exc_info=True)
        yield sse_pack({"e": "回答中断了，再问一次试试"})
    yield "data: [DONE]\n\n"


#搭建初始提示词(json格式)
def build_messages(title: str, text: str, history: list, question: str) -> list:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if text:
        messages.append({"role": "system", "content": f"用户正在阅读《{title}》：\n\n{text}"})
    #MAX_HISTORY限制上下文长度，读取历史对话
    for m in (history or [])[-MAX_HISTORY:]:
        #进行一次过滤再append
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            messages.append({"role": m["role"], "content": m["content"]})
    #本轮对话
    messages.append({"role": "user", "content": question})
    return messages

#包含过期清除
#KEYS[1]=chat:rate:<uid>  ARGV[1]=member  ARGV[2]=窗口秒数  ARGV[3]=上限
RATE_LIMIT_LUA = """
local now = tonumber(redis.call('TIME')[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, now - tonumber(ARGV[2]))
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[3]) then
    return 0
end
redis.call('ZADD', KEYS[1], now, ARGV[1])
redis.call('EXPIRE', KEYS[1], ARGV[2])
return 1
"""


async def allow(user_id: int) -> bool:
    key = f"chat:rate:{user_id}"
    try:
        allowed = await r.eval(RATE_LIMIT_LUA, 1, key, uuid.uuid4().hex, WINDOW, LIMIT)
    except RedisError:
        #Redis 连不上、或同时飞的请求超过连接池上限都落到这里。宁可拒掉，
        #也不放行——否则 Redis 一挂，限流就等于没有，公网端点直接裸奔
        logger.warning("rate limit unavailable", exc_info=True)
        return False
    return allowed == 1


class ChatData(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    art_id: int | None = None
    #对话记录由前端上传
    history: list[dict] = []


chat_api = APIRouter(prefix="/api")

@chat_api.post("/chat")
async def chat(data: ChatData, token_data: Annotated[dict, Depends(verify_token)]):
    user_id = token_data["user_id"]
    #对话是否超过限额
    if not await allow(user_id):
        raise HTTPException(status_code=429, detail={"code": 429, "msg": "聊得太快了，休息一下"})

    title = ""
    text = ""
    if data.art_id:
        article = await Article.get_or_none(art_id=data.art_id)
        if article:
            title, text = article.art_title, plain_text(article.art_content)

    messages = build_messages(title, text, data.history, data.question)
    try:
        #刻意 await：第一轮还在响应头之前，402/429 仍能翻成 503
        stream = await new_stream(messages)
    #DSapi报错处理
    except APIStatusError as e:
        logger.warning("deepseek status %s: %s", e.status_code, e)
        if e.status_code == 402:
            raise HTTPException(status_code=503, detail={"code": 503, "msg": "AI 服务暂时不可用"})
        if e.status_code == 429:
            raise HTTPException(status_code=503, detail={"code": 503, "msg": "AI 服务繁忙，请稍后再试"})
        raise HTTPException(status_code=503, detail={"code": 503, "msg": "AI 服务出错，请稍后再试"})
    except (APITimeoutError, APIConnectionError):
        logger.warning("deepseek unreachable", exc_info=True)
        raise HTTPException(status_code=504, detail={"code": 504, "msg": "AI 响应超时，请重试"})

    return StreamingResponse(
        sse(stream, messages),
        #前端识别此类型后持续监听服务端推送数据
        media_type="text/event-stream",
        #"Cache-Control": "no-cache" 告诉前端不缓存，否则会拿到旧消息
        #"X-Accel-Buffering": "no" 关闭Nginx响应缓冲，流式输出
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
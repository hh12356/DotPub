import logging
import re
import time
from collections import deque
from html import unescape
from typing import Annotated

import nh3
from fastapi import APIRouter, Depends, HTTPException
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, Field

from core.security import verify_token
from core.setting import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
from models.article import Article

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=30.0,
)

SYSTEM_PROMPT = (
    "你是 Dot，DotPub（一个技术文章社区）的站内助手。"
    "用简体中文回答，直接给结论，不要客套。"
    "如果用户正在阅读某篇文章，文章正文会一并提供给你，请优先依据它回答；"
    "正文里没有写的内容不要编，直接说明文章里没有提到。"
)

#关闭DS思考模式，打开即enabled
THINKING_OFF = {"thinking": {"type": "disabled"}}

MAX_HISTORY = 20
WINDOW = 3600
LIMIT = 30

#拿到报错日志
logger = logging.getLogger("uvicorn.error")


#剥掉html标签
def plain_text(raw: str) -> str:
    with_breaks = re.sub(r"</(?:p|div|li|h[1-6])>|<br\s*/?>", "\n", raw or "", flags=re.I)
    return unescape(nh3.clean(with_breaks, tags=set()))


#搭建提示词(json格式)
def build_messages(title: str, text: str, history: list, question: str) -> list:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if text:
        messages.append({"role": "system", "content": f"用户正在阅读《{title}》：\n\n{text}"})
    #MAX_HISTORY限制上下文长度，读取历史对话
    for m in (history or [])[-MAX_HISTORY:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            messages.append({"role": m["role"], "content": m["content"]})
    #本轮对话
    messages.append({"role": "user", "content": question})
    return messages


_hits: dict[int, deque] = {}


def allow(user_id: int) -> bool:
    #单调时钟的时间，仅用于计算时间差
    now = time.monotonic()
    q = _hits.setdefault(user_id, deque())
    #删掉超过1小时的记录
    while q and now - q[0] > WINDOW:
        q.popleft()
    #限制对话次数
    if len(q) >= LIMIT:
        return False
    #记录当前时间
    q.append(now)
    return True


class ChatData(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    art_id: int | None = None
    #对话记录由前端上传
    history: list[dict] = []


chat_api = APIRouter(prefix="/api")

@chat_api.post("/chat")
async def chat(data: ChatData, token_data: Annotated[dict, Depends(verify_token)]):
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
        resp = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=build_messages(title, text, data.history, data.question),
            extra_body=THINKING_OFF,
        )
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

    #本次对话消耗token
    logger.info("chat usage: %s", resp.usage)

    return {"code": 200, "msg": "成功", "data": {"answer": resp.choices[0].message.content}}

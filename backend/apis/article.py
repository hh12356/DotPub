from typing import Annotated
from core.security import verify_token

import nh3
from fastapi import APIRouter,HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from models.article import *
from models.interaction import *

article_api = APIRouter()

# ---------- 正文 HTML 清洗 ----------
# 接口是唯一的信任边界：前端那些校验（isEmptyHtml、required）都跑在
# 攻击者自己的浏览器里，绕过 Write 页面直接 POST /article 就能把任意
# HTML 存进库，之后每个打开这篇文章的人都会执行它（存储型 XSS）。
# 所以清洗必须放在【入库前】——把危险标签在写进数据库之前就剥掉，
# 而不是等到渲染时再想办法。

# 只放行编辑器和阅读页真正用得到的标签，其余一律剥除（保留文字内容）
ALLOWED_TAGS = {
    "p", "br", "strong", "em", "u", "s", "span",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "pre", "code", "a", "img",
}

# class 和 data-list 是 Quill 渲染对齐、字号、列表序号用的，
# 不放行的话正文格式会整个丢掉（列表变成没圆点的纯文本）
ALLOWED_ATTRS = {
    "a": {"href", "target"},
    "img": {"src", "alt"},
    "*": {"class", "data-list"},
}


def clean_html(html: str) -> str:
    """剥掉正文里除白名单外的所有标签和属性。

    注意不要用正则自己实现——`<img src=x onerror=>`、大小写变形、
    `<scr<script>ipt>`、实体编码都能绕过去。nh3 底层是真正的 HTML
    解析器 + 白名单，和浏览器同一套规则。
    """
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)


class SubmitData(BaseModel):
    art_title:str
    art_content:str

#上传文章
@article_api.post("/article")
async def submit_article(article_data:SubmitData,token_data:Annotated[dict,Depends(verify_token)]):
    print(token_data)
    user_id=token_data["user_id"]
    article = await Article.create(
        # art_title 不用清洗：前端是当纯文本渲染的（React 自动转义），
        # 而 art_content 会走 dangerouslySetInnerHTML，所以必须清
        art_title=article_data.art_title,
        art_content=clean_html(article_data.art_content),
        art_author_id=user_id
    )
    return {
        "code": 200,
        "msg": "发布成功",
        "data": article
    }



#获取所有文章
@article_api.get("/article")
async def get_all_article():
    articles = await Article.all().select_related("art_author")
    #Queryset : [Student(),Student(),Student(),...]

    return {
        "code": 200,
        "msg": "获取成功",
        "data": [
            {**dict(a), "art_author": a.art_author.user_name}
            for a in articles
        ]
    }

#获取对应id文章
@article_api.get("/article/{art_id}")
async def get_article(art_id):
    article = await Article.get(art_id=art_id).select_related("art_author")

    return {
        "code": 200,
        "msg": "获取成功",
        "data": {**dict(article), "art_author": article.art_author.user_name}
    }

#点赞
@article_api.get("/like/{art_id}")
async def like(art_id,token_data:Annotated[dict,Depends(verify_token)]):
    user_id=token_data["user_id"]
    try:
        await ArticleLike(user_id=user_id,art_id=art_id)
        return {"code": 200, "msg": "点赞成功"}
    except IntegrityError:
    # 已经赞过了（或者并发撞上了）→ 幂等返回成功，不是错误
        return {"code": 200, "msg": "已经赞过了"}

#取消点赞
@article_api.delete("/like/{art_id}")
async def cancel_like(art_id,token_data:Annotated[dict,Depends(verify_token)]):
    user_id=token_data["user_id"]
    await ArticleLike(user_id=user_id,art_id=art_id).delete()
    return {"code": 200, "msg": "取消点赞成功","like":False}




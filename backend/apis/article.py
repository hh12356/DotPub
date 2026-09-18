from tortoise.functions import Count

from core.security import verify_token, optional_user, is_admin, can_manage

import nh3
from fastapi.params import Depends
from pydantic import BaseModel, Field
from tortoise.exceptions import IntegrityError

from models.article import *
from models.interaction import *
from models.comment import *

from typing import Annotated, Literal
from fastapi import APIRouter, HTTPException, Query
from tortoise.expressions import RawSQL
import re
from html import unescape

article_api = APIRouter(prefix="/api")

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
    art_title:str=Field(min_length=1,max_length=100)
    art_content:str

#上传文章
@article_api.post("/article")
async def submit_article(article_data:SubmitData,token_data:Annotated[dict,Depends(verify_token)]):
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

#修改文章
@article_api.put("/article/{art_id}")
async def edit_article(art_id,article_data:SubmitData,token_data:Annotated[dict,Depends(verify_token)]):
    user_id=token_data["user_id"]
    article = await Article.get_or_none(art_id=art_id)

    #身份检验
    if not article or not can_manage(article.art_author_id, user_id, await is_admin(user_id)):
        raise HTTPException(status_code=404,detail={"msg":"只能修改自己的文章"})

    article.art_title=article_data.art_title
    article.art_content=clean_html(article_data.art_content)
    await article.save()

    return {
        "code": 200,
        "msg": "修改成功",
        "data": article
    }

#删除文章
@article_api.delete("/article/{art_id}")
async def delete_article(art_id,token_data:Annotated[dict,Depends(verify_token)]):
    user_id = token_data["user_id"]
    article = await Article.get_or_none(art_id=art_id)
    if not article or not can_manage(article.art_author_id, user_id, await is_admin(user_id)):
        raise HTTPException(
            status_code=403,
            detail={"code": 403, "msg": "只能删除自己的文章"}
        )

    await article.delete()
    return {"code": 200, "msg": "删除成功"}

#获取所有文章
def first_line(raw: str) -> str:
    with_breaks = re.sub(r"</(?:p|div|li|h[1-6])>|<br\s*/?>", "\n", raw or "", flags=re.I)
    # nh3 负责剥标签（防 XSS），但它序列化时会把 NBSP 写回 &nbsp; 实体，
    # 得再 unescape 一次才是真正的纯文本。strip() 会顺手去掉还原出来的 NBSP
    text = unescape(nh3.clean(with_breaks, tags=set()))
    return next((s.strip() for s in text.split("\n") if s.strip()), "")

FRESH_WINDOW = 90 * 24 * 3600
@article_api.get("/article")
async def get_all_article(
        user:Annotated[dict | None , Depends(optional_user)],
        page:int=Query(1,ge=1),
        size:int=Query(8,ge=1,le=100),
        sort:Literal["latest", "hot", "greatest"] = "latest"
):
    #准备数据
    like = Count("like_records", distinct=True)
    star = Count("star_records", distinct=True)
    cmt = Count("comments", distinct=True)

    qs = Article.annotate(
        like_count=like,
        star_count=star,
        comment_count=cmt,
    ).select_related("art_author")

    if sort == "greatest":
        qs = qs.annotate(score=like * 0.4 + star * 0.6)
        order = "-score"
    elif sort == "hot":
        qs = qs.annotate(score=RawSQL(
            "LOG10(GREATEST("
            "0.25 * (SELECT COUNT(*) FROM `articlelike`"
            "        WHERE `articlelike`.`art_id` = `article`.`art_id`)"
            " + 0.35 * (SELECT COUNT(*) FROM `comment`"
            "        WHERE `comment`.`cmt_art_id` = `article`.`art_id`)"
            " + 0.4 * (SELECT COUNT(*) FROM `articlestar`"
            "        WHERE `articlestar`.`art_id` = `article`.`art_id`)"
            f", 1)) - TIMESTAMPDIFF(SECOND, `article`.`art_pub_datetime`, NOW()) / {FRESH_WINDOW}"
            " + (MOD(`article`.`art_id` * 2654435761, 1000) / 1000.0 - 0.5) * 0.6"
        ))
        order = "-score"
    else:
        order = "-art_pub_datetime"

    articles = await qs.order_by("-is_pinned", order).offset((page - 1) * size).limit(size)

    #获取当前用户点赞收藏信息
    liked_ids, starred_ids = set(), set()
    if user and articles:
        art_ids = [a.art_id for a in articles]
        liked_ids = set(await ArticleLike.filter(
            user_id=user["user_id"], art_id__in=art_ids
        ).values_list("art_id", flat=True))
        starred_ids = set(await ArticleStar.filter(
            user_id=user["user_id"], art_id__in=art_ids
        ).values_list("art_id", flat=True))

    return {
        "code": 200,
        "msg": "获取成功",
        "has_more": len(articles) == size,  # 新增：前端靠它判断要不要继续加载
        "data": [
            {
                **dict(a),
                "art_content":first_line(a.art_content),
                "art_author": a.art_author.user_name,
                "like_count": a.like_count,
                "star_count": a.star_count,
                "comment_count": a.comment_count,
                "is_liked": a.art_id in liked_ids,
                "is_starred": a.art_id in starred_ids,
            }
            for a in articles
        ]
    }

#获取对应id文章
@article_api.get("/article/{art_id}")
async def get_article(art_id:int,user:Annotated[dict | None , Depends(optional_user)]):
    article = await Article.get_or_none(art_id=art_id).select_related("art_author")
    #文章存在校验
    if not article:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": "文章不存在"})

    like_count = await ArticleLike.filter(art_id=art_id).count()
    star_count = await ArticleStar.filter(art_id=art_id).count()
    comment_count = await Comment.filter(cmt_art_id=art_id).count()

    is_liked = is_starred = False
    if user:
        is_liked = await ArticleLike.filter(user_id=user["user_id"], art_id=art_id).exists()
        is_starred = await ArticleStar.filter(user_id=user["user_id"], art_id=art_id).exists()

    can_delete = bool(user) and can_manage(
        article.art_author_id, user["user_id"], await is_admin(user["user_id"])
    )
    can_pin = bool(user) and await is_admin(user["user_id"])

    return {
        "code": 200,
        "msg": "获取成功",
        "data": {
            **dict(article),
            "art_author": article.art_author.user_name,
            "art_author_id":article.art_author.user_id,
            "like_count":like_count,
            "star_count":star_count,
            "comment_count":comment_count,
            "is_liked":is_liked,
            "is_starred":is_starred,
            "can_delete":can_delete,
            "can_pin":can_pin
        }
    }

#搜索文章
@article_api.get("/search/{value}")
async def search_article(value:str,user:Annotated[dict | None , Depends(optional_user)]):
    articles = await (Article.filter(
        art_title__icontains=value
    ).annotate(
        like_count=Count("like_records",distinct=True),
        star_count=Count("star_records",distinct=True),
        comment_count=Count("comments",distinct=True)
    ).select_related("art_author"))
    #Queryset : [Student(),Student(),Student(),...]

    #获取当前用户点赞收藏信息
    liked_ids, starred_ids = set(), set()
    if user and articles:
        art_ids = [a.art_id for a in articles]
        liked_ids = set(await ArticleLike.filter(
            user_id=user["user_id"], art_id__in=art_ids
        ).values_list("art_id", flat=True))
        starred_ids = set(await ArticleStar.filter(
            user_id=user["user_id"], art_id__in=art_ids
        ).values_list("art_id", flat=True))

    return {
        "code": 200,
        "msg": "搜索成功",
        "data": [
            {
                **dict(a),
                # 和 /article 一样只给摘要：搜索页也是列表，也用 ArticleCard
                "art_content": first_line(a.art_content),
                "art_author": a.art_author.user_name,
                "like_count": a.like_count,
                "star_count": a.star_count,
                "comment_count": a.comment_count,
                "is_liked": a.art_id in liked_ids,
                "is_starred": a.art_id in starred_ids,
            }
            for a in articles
        ]
    }



#点赞
@article_api.get("/like/{art_id}")
async def like(art_id,token_data:Annotated[dict,Depends(verify_token)]):
    user_id=token_data["user_id"]
    if not await Article.exists(art_id=art_id):
        raise HTTPException(status_code=404, detail={"msg": "文章不存在"})

    try:
        await ArticleLike.create(user_id=user_id,art_id=art_id)
        return {"code": 200, "msg": "点赞成功"}
    except IntegrityError:
    # 已经赞过了（或者并发撞上了）→ 幂等返回成功，不是错误
        return {"code": 200, "msg": "已经赞过了"}

#取消点赞
@article_api.delete("/like/{art_id}")
async def cancel_like(art_id,token_data:Annotated[dict,Depends(verify_token)]):
    user_id=token_data["user_id"]
    await ArticleLike.filter(user_id=user_id,art_id=art_id).delete()
    return {"code": 200, "msg": "取消点赞成功"}


#收藏
@article_api.get("/star/{art_id}")
async def like(art_id,token_data:Annotated[dict,Depends(verify_token)]):
    user_id=token_data["user_id"]
    if not await Article.exists(art_id=art_id):
        raise HTTPException(status_code=404, detail={"msg": "文章不存在"})

    try:
        await ArticleStar.create(user_id=user_id,art_id=art_id)
        return {"code": 200, "msg": "收藏成功"}
    except IntegrityError:
        return {"code": 200, "msg": "已经收藏过了"}

#取消收藏
@article_api.delete("/star/{art_id}")
async def cancel_like(art_id,token_data:Annotated[dict,Depends(verify_token)]):
    user_id=token_data["user_id"]
    await ArticleStar.filter(user_id=user_id,art_id=art_id).delete()
    return {"code": 200, "msg": "取消收藏成功","like":False}

class CommentIn(BaseModel):
    cmt_content:str=Field(max_length=500)

#发布评论
@article_api.put('/comment/{art_id}')
async def add_comment(art_id,cmt_data:CommentIn,token_data:Annotated[dict,Depends(verify_token)]):
    await Comment.create(cmt_content=cmt_data.cmt_content,cmt_art_id=art_id,cmt_user_id=token_data["user_id"])
    return {"code":200,"msg":"发布成功"}

#获取评论
@article_api.get('/comment/{art_id}')
async def get_comment(art_id,user:Annotated[dict | None , Depends(optional_user)]):
    comments = await Comment.filter(cmt_art_id=art_id).select_related("cmt_user").order_by("-cmt_pub_datetime")
    viewer_is_admin = bool(user) and await is_admin(user["user_id"])
    return {
        "code":200,
        "msg":"发布成功",
        "data":[
            {
                "cmt_id":c.cmt_id,
                "user_name":c.cmt_user.user_name,
                "cmt_user_id":c.cmt_user_id,
                "cmt_content":c.cmt_content,
                "cmt_pub_datetime":c.cmt_pub_datetime,
                "can_delete": bool(user) and can_manage(
                    c.cmt_user_id, user["user_id"], viewer_is_admin
                ),
            }
            for c in comments
        ]
    }

#删除评论
@article_api.delete('/comment/{cmt_id}')
async def delete_comment(cmt_id:int,token_data:Annotated[dict,Depends(verify_token)]):
    user_id = token_data["user_id"]
    comment = await Comment.get_or_none(cmt_id=cmt_id)
    if not comment or not can_manage(comment.cmt_user_id, user_id, await is_admin(user_id)):
        raise HTTPException(
            status_code=403,
            detail={"code": 403, "msg": "只能删除自己的评论"}
        )
    await comment.delete()
    return {"code": 200, "msg": "删除成功"}

class PinIn(BaseModel):
    status:bool

@article_api.put('/pin/{art_id}')
async def change_pin(art_id:int, pin_data:PinIn, token_data:Annotated[dict,Depends(verify_token)]):
    if await is_admin(token_data["user_id"]):
        await Article.filter(art_id=art_id).update(is_pinned=pin_data.status)
        return {
            "code":200,
            "msg":"修改置顶成功"
        }
    raise HTTPException(
        status_code=403,
        detail={
            'msg':"权限不足"
        }
    )




















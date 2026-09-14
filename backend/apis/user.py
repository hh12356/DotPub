from typing import Annotated

from tortoise.functions import Count

from core.security import verify_token,optional_user

from fastapi import APIRouter,HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from models.article import *
from models.interaction import *


user_api = APIRouter()

#获取喜欢列表
@user_api.get('/likes')
async def get_likes(token_data:Annotated[dict,Depends(verify_token)]):
    user_id = token_data["user_id"]

    ids = list(await ArticleLike.filter(user_id=user_id)
               .order_by("-created_at")
               .values_list("art_id", flat=True))

    articles = await Article.filter(art_id__in=ids).annotate(
        like_count=Count("like_records", distinct=True),
        star_count=Count("star_records", distinct=True)
    ).select_related("art_author")

    starred_ids = set(await ArticleStar.filter(
        user_id=user_id, art_id__in=[a.art_id for a in articles]
    ).values_list("art_id", flat=True))

    by_id = {a.art_id: a for a in articles}
    articles = [by_id[i] for i in ids]

    return {
            "code": 200,
            "msg": "获取成功",
            "data": [
                {
                    **dict(a),
                    "art_author": a.art_author.user_name,
                    "like_count": a.like_count,
                    "star_count": a.star_count,
                    "is_liked": True,
                    "is_starred": a.art_id in starred_ids,
                }
                for a in articles
            ]
        }


#获取收藏列表
@user_api.get('/stars')
async def get_stars(token_data:Annotated[dict,Depends(verify_token)]):
    user_id = token_data["user_id"]

    ids = list(await ArticleStar.filter(user_id=user_id)
               .order_by("-created_at")
               .values_list("art_id", flat=True))#flat=True返回一维数组

    articles = await Article.filter(art_id__in=ids).annotate(
        like_count=Count("like_records", distinct=True),
        star_count=Count("star_records", distinct=True)
    ).select_related("art_author")

    liked_ids = set(await ArticleLike.filter(
        user_id=user_id, art_id__in=[a.art_id for a in articles]
    ).values_list("art_id", flat=True))

    #重新排序
    by_id = {a.art_id: a for a in articles}
    articles = [by_id[i] for i in ids]

    return {
            "code": 200,
            "msg": "获取成功",
            "data": [
                {
                    **dict(a),
                    "art_author": a.art_author.user_name,
                    "like_count": a.like_count,
                    "star_count": a.star_count,
                    "is_liked": a.art_id in liked_ids,
                    "is_starred": True,
                }
                for a in articles
            ]
        }






















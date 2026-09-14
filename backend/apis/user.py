from typing import Annotated

from tortoise.functions import Count

from core.security import verify_token,optional_user

from fastapi import APIRouter,HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from models.article import *
from models.interaction import *
from models.user import UserAccount

user_api = APIRouter()

#获取用户文章
@user_api.get('/userart')
async def get_user_art(token_data:Annotated[dict,Depends(verify_token)]):
    user_id = token_data["user_id"]

    articles = await Article.filter(art_author_id=user_id).annotate(
        like_count=Count("like_records", distinct=True),
        star_count=Count("star_records", distinct=True)
    ).select_related("art_author").order_by('-art_pub_datetime')

    starred_ids = set(await ArticleStar.filter(
        user_id=user_id, art_id__in=[a.art_id for a in articles]
    ).values_list("art_id", flat=True))
    liked_ids = set(await ArticleLike.filter(
        user_id=user_id, art_id__in=[a.art_id for a in articles]
    ).values_list("art_id", flat=True))

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
                    "is_starred": a.art_id in starred_ids,
                }
                for a in articles
            ]
        }


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


#获取用户profile
#用户名 简介  发表文章数 被赞总数 被收藏总数  代表作
@user_api.get('/profile/{tar_id}')
async def get_user_profile(tar_id:int,user:Annotated[dict | None , Depends(optional_user)]):
    user_id = user["user_id"] if user else None

    tar_user = await UserAccount.filter(user_id=tar_id).first()
    if not tar_user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": 404,
                "msg": "用户不存在"
            }
        )
    articles = await Article.filter(art_author_id=tar_id).annotate(
        like_count=Count("like_records",distinct=True),
        star_count=Count("star_records",distinct=True)
    ).select_related("art_author")

    liked_ids, starred_ids = set(), set()
    if user and articles:
        art_ids = [a.art_id for a in articles]
        liked_ids = set(await ArticleLike.filter(
            user_id=user["user_id"], art_id__in=art_ids
        ).values_list("art_id", flat=True))
        starred_ids = set(await ArticleStar.filter(
            user_id=user["user_id"], art_id__in=art_ids
        ).values_list("art_id", flat=True))

    art_ids = list(await Article.filter(art_author_id=tar_id).values_list("art_id",flat=True))
    return {
            "code": 200,
            "msg": "获取成功",
            "data": {
                "user_name":tar_user.user_name,
                "user_bio":tar_user.user_bio,
                "user_join_date":tar_user.user_join_date,
                "art_count":len(art_ids),
                "likes_received":await ArticleLike.filter(art_id__in=art_ids).count(),
                "stars_received":await ArticleStar.filter(art_id__in=art_ids).count(),
                "self":(user_id==tar_id),
                "art":[
                    {
                        **dict(a),
                        "art_author": a.art_author.user_name,
                        "like_count": a.like_count,
                        "star_count": a.star_count,
                        "is_liked": a.art_id in liked_ids,
                        "is_starred": a.art_id in starred_ids,
                    }
                    for a in articles
                ]
            }
        }




















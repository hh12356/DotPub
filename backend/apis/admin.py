from tortoise.functions import Count

from core.security import verify_token, optional_user, is_admin, can_manage, verify_admin

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

from models.user import UserAccount

from collections import Counter
from datetime import date, datetime, time, timedelta

admin_api = APIRouter(prefix="/api")

TREND_DAYS = 14
TOP_N = 10


def _trend_axis(today: date, days: int = TREND_DAYS) -> list[date]:
    """趋势图横轴，最早的在前——折线要从左往右读。"""
    return [today - timedelta(days=i) for i in range(days - 1, -1, -1)]


def _series(axis: list[date], counter: Counter) -> list[int]:
    """把按天计数对齐到横轴上，没有数据的天补 0（缺了折线会断）。"""
    return [counter[d] for d in axis]


def _art_row(art, **counts):
    """榜单里每篇只要标题和作者，正文不返回。"""
    return {
        "art_id": art.art_id,
        "art_title": art.art_title,
        "art_author": art.art_author.user_name,
        **counts,
    }


@admin_api.get('/admin/stats')
async def get_stats(token_data:Annotated[dict,Depends(verify_admin)]):
    #统计总数
    totals = {
        "user": await UserAccount.all().count(),
        "article": await Article.all().count(),
        "comment": await Comment.all().count(),
        "like": await ArticleLike.all().count(),
        "star": await ArticleStar.all().count(),
    }

    #近14天趋势：把时间列取回内存用 Counter 按天分组。
    #千级数据这样最省事；涨到几十万行再换成 GROUP BY DATE(...) 一次查出。
    axis = _trend_axis(date.today())
    start = datetime.combine(axis[0], time.min)
    art_per_day = Counter(
        d.date() for d in await Article.filter(
            art_pub_datetime__gte=start).values_list("art_pub_datetime", flat=True))
    user_per_day = Counter(
        d.date() for d in await UserAccount.filter(
            user_join_date__gte=start).values_list("user_join_date", flat=True))

    #人气top
    top_liked = await Article.annotate(
        like_count=Count("like_records")).select_related("art_author").order_by(
        "-like_count", "-art_id").limit(TOP_N)
    top_starred = await Article.annotate(
        star_count=Count("star_records")).select_related("art_author").order_by(
        "-star_count", "-art_id").limit(TOP_N)
    top_commented = await Article.annotate(
        comment_count=Count("comments")).select_related("art_author").order_by(
        "-comment_count", "-art_id").limit(TOP_N)

    #发文最多的人，0 篇的（纯浏览用户）不往榜上放
    active_users = await UserAccount.annotate(
        art_count=Count("articles")).order_by("-art_count", "-user_id").limit(TOP_N)

    return {
        "code": 200,
        "msg": "获取成功",
        "data": {
            "totals": totals,
            "trend": {
                "dates": [d.strftime("%m-%d") for d in axis],
                "articles": _series(axis, art_per_day),
                "users": _series(axis, user_per_day),
            },
            "top_liked": [_art_row(a, like_count=a.like_count) for a in top_liked],
            "top_starred": [_art_row(a, star_count=a.star_count) for a in top_starred],
            "top_commented": [
                _art_row(a, comment_count=a.comment_count) for a in top_commented],
            "active_users": [
                {"user_id": u.user_id, "user_name": u.user_name, "art_count": u.art_count}
                for u in active_users if u.art_count
            ],
        },
    }




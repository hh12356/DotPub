from typing import Annotated
from core.security import verify_token

from fastapi import APIRouter,HTTPException
from fastapi.params import Depends
from pydantic import BaseModel

from models.article import *

article_api = APIRouter()

class SubmitData(BaseModel):
    art_title:str
    art_content:str

#上传文章
@article_api.post("/article")
async def submit_article(article_data:SubmitData,token_data:Annotated[dict,Depends(verify_token)]):
    print(token_data)
    user_id=token_data["user_id"]
    article = await Article.create(
        art_title=article_data.art_title,
        art_content=article_data.art_content,
        art_author_id=user_id
    )
    return {
        "code": 200,
        "msg": "发布成功",
        "data": article
    }

#按时间顺序获取文章
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






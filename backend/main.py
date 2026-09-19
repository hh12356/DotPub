from fastapi import FastAPI
import uvicorn

from tortoise.contrib.fastapi import register_tortoise

from apis.admin import admin_api
from apis.user import user_api
from core.setting import TORTOISE_ORM

from apis.login import login_api
from apis.sign_up import sign_up_api
from apis.article import article_api
from apis.chat import chat_api

app = FastAPI()

app.include_router(login_api,tags=["登录模块"])
app.include_router(sign_up_api,tags=["注册模块"])
app.include_router(article_api,tags=["文章模块"])
app.include_router(user_api,tags=["用户模块"])
app.include_router(admin_api,tags=["管理员板块"])
app.include_router(chat_api,tags=["AI 助手"])

register_tortoise(
    app=app,
    config=TORTOISE_ORM
)

if __name__ == '__main__':
    uvicorn.run(app,port=8010,log_level="debug",workers=1)
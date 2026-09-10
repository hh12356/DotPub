from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from tortoise.contrib.fastapi import register_tortoise
from core.setting import TORTOISE_ORM

from apis.login import login_api
from apis.sign_up import sign_up_api

app = FastAPI()

app.include_router(login_api,tags=["登录模块"])
app.include_router(sign_up_api,tags=["注册模块"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)

register_tortoise(
    app=app,
    config=TORTOISE_ORM
)

if __name__ == '__main__':
    uvicorn.run(app,port=8010,log_level="debug",workers=1)
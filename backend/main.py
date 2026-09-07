from fastapi import FastAPI
import uvicorn

from tortoise.contrib.fastapi import register_tortoise
from setting import TORTOISE_ORM

from apis.login import login_api

app = FastAPI()

app.include_router(login_api,tags=["登录模块"])

register_tortoise(
    app=app,
    config=TORTOISE_ORM
)

if __name__ == '__main__':
    uvicorn.run(app,port=8010,log_level="debug",workers=1)
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from tortoise.exceptions import IntegrityError

from core.security import get_token, hash_pwd
from models.user import *

sign_up_api = APIRouter(prefix="/api")

class SignUpData(BaseModel):
    #手机号由前端校验
    user_phone:str
    user_name:str
    user_pwd:str = Field(min_length=8)

@sign_up_api.post("/signup")
async def verify_user_info(sign_up_data:SignUpData):
    try:
        #有unique关键字，有重复项会直接catch
        user = await UserAccount.create(
            user_name=sign_up_data.user_name,
            user_pwd=hash_pwd(sign_up_data.user_pwd),
            user_phone=sign_up_data.user_phone
        )
    except IntegrityError:
        raise HTTPException(status_code=400, detail={"code": 400, "msg": "用户名或手机号已被占用"})
    return {
        "code": 200,
        "msg": "注册成功",
        "data": {
            "user_id": user.user_id,
            "user_name": user.user_name,
            "token": get_token({"user_id": user.user_id})
        }
    }
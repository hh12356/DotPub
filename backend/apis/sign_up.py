from fastapi import APIRouter
from pydantic import BaseModel,Field
from models.user import *

sign_up_api = APIRouter()

class SignUpData(BaseModel):
    #手机号由前端校验
    user_phone:str
    user_name:str
    user_pwd:str

@sign_up_api.post("/signup")
async def verify_user_info(sign_up_data:SignUpData):
    exist_phone=await UserAccount.filter(user_phone=sign_up_data.user_phone)
    if not exist_phone:
        exist_name = await UserAccount.filter(user_name=sign_up_data.user_name)
        if not exist_name:
            user = await UserAccount.create(
                user_name=sign_up_data.user_name,
                user_pwd=sign_up_data.user_pwd,
                user_phone=sign_up_data.user_phone
            )
            return {
                "code": 200,
                "msg": "注册成功",
                "data": {
                    "user_id": user.user_id,
                    "user_name": user.user_name
                }
            }
        return {
            "code": 400,
            "msg": "该用户名已被占用",
            "data": None
        }
    return {
        "code":400,
        "msg":"该手机号已注册",
        "data":None
    }
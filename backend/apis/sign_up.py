from fastapi import APIRouter
from pydantic import BaseModel,Field
from models.user import *

sign_up_api = APIRouter()

class SignUpData(BaseModel):
    #手机号由前端校验
    user_phone:str
    user_name:str
    user_pwd:str

@sign_up_api.post("/login")
async def verify_user_info(sign_up_data:SignUpData):
    exist_user=UserAccount.filter(user_phone=sign_up_data.user_phone)
    if not exist_user:
        #未添加用户名校验和id自增，数据库未更新
        user = await UserAccount.create(
            user_name = sign_up_data.user_name,
            user_pwd = sign_up_data.user_pwd,
            user_phone = sign_up_data.user_phone
        )

        return{
            "code":200,
            "msg":"注册成功",
            "data":{
                "user_id":user[0].user_id,
                "user_name":user[0].user_name
            }
        }

    return {
        "code":400,
        "msg":"该手机号已注册",
        "data":None
    }
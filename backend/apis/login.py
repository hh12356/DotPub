from fastapi import APIRouter
from pydantic import BaseModel
from models.user import *

login_api = APIRouter()

class LoginData(BaseModel):
    user_name:str
    user_pwd:str


@login_api.post("/login")
async def verify_user_info(login_data:LoginData):
    user = await UserAccount.filter(user_name=login_data.user_name,user_pwd=login_data.user_pwd)
    if not user :
        return{
            "code":400,
            "msg":"用户名或密码错误",
            "data":None
        }
    return {
        "code":200,
        "msg":"登录成功",
        "data":{
            "user_id":user[0].user_id,
            "user_name":user[0].user_name
        }
    }

from fastapi import APIRouter,HTTPException
from pydantic import BaseModel

from core.security import get_token, verify_pwd
from models.user import *

login_api = APIRouter()

class LoginData(BaseModel):
    user_name:str
    user_pwd:str

@login_api.post("/login")
async def verify_user_info(login_data:LoginData):
    user = await UserAccount.get_or_none(user_name=login_data.user_name)
    if not user or not verify_pwd(login_data.user_pwd,user.user_pwd):
        raise HTTPException(
            status_code=400,
            detail={
                "code":"BAD_CREDENTIALS",
                "msg":"用户名或密码错误"
            }
        )
    return {
        "code":200,
        "msg":"登录成功",
        "data":{
            "user_id":user.user_id,
            "user_name":user.user_name,
            "token":get_token({"user_id":user.user_id})
        }
    }

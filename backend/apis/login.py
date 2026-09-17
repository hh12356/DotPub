from fastapi import APIRouter,HTTPException
from pydantic import BaseModel

from core.security import get_token, verify_pwd, is_banned, is_muted
from models.user import *

login_api = APIRouter(prefix="/api")

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
    #封号验证
    if await is_banned(user.user_id):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "BAD_CREDENTIALS",
                "msg": "因违反社区规定，改账号已被封禁"
            }
        )
    msg = "登录成功"
    if await is_muted(user.user_id):
        msg = "登录成功，该账号已被禁言"
    return {
        "code":200,
        "msg":msg,
        "data":{
            "user_id":user.user_id,
            "user_name":user.user_name,
            "token":get_token({"user_id":user.user_id}),
            "user_role":user.user_role
        }
    }

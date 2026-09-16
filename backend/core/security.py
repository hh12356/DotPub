
from core.setting import SECRET_KEY
import jwt
from datetime import datetime,timedelta,timezone

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError
from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer

from models.user import *

ph = PasswordHasher(time_cost=3,memory_cost=65536,parallelism=4)

def hash_pwd(pwd:str)->str:
    #->str为类型注解，指返回类型为str
    return ph.hash(pwd)

def verify_pwd(pwd:str,store:str)->bool:
    try:
        ph.verify(store,pwd)
        return True
    except (Argon2Error,InvalidHashError):
        return False


ALGORITHM="HS256"
limited_time=360

def get_token(data:dict):
    to_encode = data.copy()
    to_encode.update({"exp":datetime.now(timezone.utc) + timedelta(minutes=limited_time)})
    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

async def verify_token(token:str=Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"msg":"登录已过期"},
            headers={"WWW-Authenticate":"Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail={"msg":"登录信息无效"},
            headers={"WWW-Authenticate": "Bearer"}
        )
    user_id = payload["user_id"]
    if await is_muted(user_id):
        raise HTTPException(
            status_code=400,
            detail={"msg":"该账号无权限"}
        )
    return payload

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl='/login',auto_error=False)

def optional_user(token: str | None = Depends(oauth2_scheme_optional)):
    #支持匿名请求
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        # ExpiredSignatureError 是 InvalidTokenError 的子类，这里一个 except 就够。
        # 坏 token 当匿名处理，不让整个列表页打不开
        return None


async def is_admin(user_id: int) -> bool:
    return await UserAccount.filter(user_id=user_id, user_role="admin").exists()

async def is_banned(user_id: int) -> bool:
    return await UserAccount.filter(user_id=user_id, is_banned=True).exists()

async def is_muted(user_id: int) -> bool:
    return await UserAccount.filter(user_id=user_id, is_muted=True).exists()

















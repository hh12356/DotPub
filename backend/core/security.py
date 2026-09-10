import jwt
from datetime import datetime,timedelta,timezone

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY ="540ef9b13c132658d871078fe5e125ce8aa1ce371ec483d073b5aa222dfdeeec"
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

def verify_token(token:str=Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="token已过期",
            headers={"WWW-Authenticate":"Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="token无效",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload



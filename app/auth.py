import os

from typing import Annotated
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

import jwt
import bcrypt

from model.model import AccessTokenPayload

ACCESS_SECRET = os.environ.get("ACCESS_SECRET", "abcde")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

BCRYPT_SALT_ROUND = int(os.environ.get("BCRYPT_SALT_ROUND", "12"))

ACCESS_TOKEN_EXPR_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPR_MINUTES", "30"))
SECRET_TOKEN_EXPR_MINUTES = int(os.environ.get("SECRET_TOKEN_EXPR_MINUTES", "1440"))

oauth_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

def encode_jwt(payload: AccessTokenPayload) -> str:
    return jwt.encode(payload.model_dump(), ACCESS_SECRET, JWT_ALGORITHM)

def decode_jwt(token: Annotated[str, Depends(oauth_scheme)]) -> AccessTokenPayload:
    try:
        payload = AccessTokenPayload(**jwt.decode(token, ACCESS_SECRET, JWT_ALGORITHM))
    except:
        raise HTTPException(401, detail="Verification Failed")

    return payload

def validate_jwt(payload: Annotated[AccessTokenPayload, Depends(decode_jwt)]):
    current_time = int(datetime.now(timezone.utc).timestamp())
    if current_time > payload.expr:
        raise HTTPException(403, detail="Token Expire")
    return payload

def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt(BCRYPT_SALT_ROUND))
    return hashed_password.decode()

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def generate_expire_time() -> int:
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPR_MINUTES)

    return int(expire_time.timestamp())

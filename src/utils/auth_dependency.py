from fastapi import Header, HTTPException, status
from typing import Optional
import jwt

#todo： 替换为更安全的密钥管理方式
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def encode_user_id(user_id: str) -> str:
    """
    生成用户的 JWT token
    :param user_id: 用户 ID
    :return: JWT token 字符串
    """
    payload = {"user_id": user_id}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token
def decode_user_id(token: str) -> str:
    """
    解码 JWT token 获取用户 ID
    :param token: JWT token 字符串
    :return: 用户 ID
    :raises HTTPException: 如果 token 无效或解码失败
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    

def get_current_user(Authorization: Optional[str] = Header(None)) -> str:
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = Authorization.split(" ")[1]
    user_id = decode_user_id(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    from src.modules.services.business.user_bussiness import UserBusiness

router = APIRouter()

def get_user_business() -> 'UserBusiness':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")

class BaseResponse(BaseModel):
    msg: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

# 注册请求体，包含所有前端传递字段
class RegisterRequest(BaseModel):
    username: str
    password: str
    id: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LogoutRequest(BaseModel):
    username: str

class UserInfoResponse(BaseModel):
    user: dict

@router.post("/register", summary="用户注册", response_model=BaseResponse)
def register(req: RegisterRequest, user_business: 'UserBusiness' = Depends(get_user_business)):
    try:
        user = user_business.register_user(
            user_id=req.id,
            username=req.username,
            email=req.email,
            password=req.password
        )
        return BaseResponse(msg="Register success", data={"user": user.__dict__})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", summary="用户登录", response_model=BaseResponse)
def login(req: LoginRequest, user_business: 'UserBusiness' = Depends(get_user_business)):
    try:
        user = user_business.login_user(req.username, req.password)
        # 这里应生成 token，暂用 uuid 代替
        token = str(uuid.uuid4())
        return BaseResponse(msg="Login success", data={"user": user.__dict__, "token": token})
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# 需要 token 认证的依赖（示例，实际应校验 token）
def get_current_user(Authorization: Optional[str] = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # 这里应校验 token 并返回 user_id，示例直接返回
    return {"user_id": "mock_user_id_from_token"}

@router.post("/protected/logout", summary="用户登出", response_model=BaseResponse)
def logout(req: LogoutRequest, current_user=Depends(get_current_user)):
    # 实际应移除 session/token
    return BaseResponse(msg="Logout success", data=None)

@router.get("/protected/userinfo", summary="获取用户信息", response_model=BaseResponse)
def get_user_info(current_user=Depends(get_current_user), user_business: 'UserBusiness' = Depends(get_user_business)):
    try:
        user_id = current_user["user_id"]
        user = user_business.get_user_info(user_id)
        return BaseResponse(msg="Success", data={"user": user.__dict__})
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

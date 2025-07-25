from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, Any
import uuid

from src.utils.response import BaseResponse

if TYPE_CHECKING:
    from src.modules.services.business.user_bussiness import UserBusiness
from src.utils.auth_dependency import encode_user_id


router = APIRouter()

def get_user_business() -> 'UserBusiness':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")

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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Registration failed.",
                "error_code": "VALUE_ERROR",
                "error_message": str(e)
            }
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "message": "Registration failed.",
                "error_code": "USER_ALREADY_EXISTS",
                "error_message": str(e)
            }
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Registration failed.",
                "error_code": "ATTRIBUTE_ERROR",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Registration failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

@router.post("/login", summary="用户登录", response_model=BaseResponse)
def login(req: LoginRequest, user_business: 'UserBusiness' = Depends(get_user_business)):
    try:
        user = user_business.login_user(req.username, req.password)
        token = encode_user_id(user.id)
        return BaseResponse(msg="Login success", data={"user": user.__dict__, "token": token})
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": "Login failed.",
                "error_code": "USER_NOT_FOUND",
                "error_message": str(e)
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Login failed.",
                "error_code": "INVALID_CREDENTIALS",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Login failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

# 需要 token 认证的依赖（示例，实际应校验 token）
def get_current_user(Authorization: Optional[str] = Header(None)) -> str:
    raise NotImplementedError("请在 auth_dependency.py 中实现 token 校验")

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
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": "User info fetch failed.",
                "error_code": "USER_NOT_FOUND",
                "error_message": str(e)
            }
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "User info fetch failed.",
                "error_code": "ATTRIBUTE_ERROR",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "User info fetch failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

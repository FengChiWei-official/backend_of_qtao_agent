from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, Any
from src.utils.response import BaseResponse
from src.utils.auth_dependency import encode_user_id, get_current_user

if TYPE_CHECKING:
    from src.modules.services.agent.agent_manager import AgentManager

def get_agent_manager() -> 'AgentManager':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")


def check_ownership_function_generator(user_id: str, session_id: str) -> bool:
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")


router = APIRouter(prefix="/api/v1", tags=["chat"])

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    query: str = Field(..., description="用户查询内容")

@router.post("/chat", summary="会话对话", response_model=BaseResponse)
def chat(req: ChatRequest, current_user=Depends(get_current_user), agent_manager: 'AgentManager' = Depends(get_agent_manager), ownership_checker_generator = Depends(check_ownership_function_generator)):
    try:
        user_id = current_user
        # user 一定要拥有session
        ownership_checker = ownership_checker_generator()
        if not ownership_checker(user_id, req.session_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限访问该会话")
        # 开始锁 agent
        answer = agent_manager.get_and_use_agent(user_id, req.session_id, req.query)
        # 结束锁 agent
        return BaseResponse(msg="success", data=answer)
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

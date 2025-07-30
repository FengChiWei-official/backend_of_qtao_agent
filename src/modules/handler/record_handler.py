from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, Any
from src.utils.response import BaseResponse
from src.utils.auth_dependency import encode_user_id, get_current_user

if TYPE_CHECKING:
    from src.modules.services.agent.agent_manager import AgentManager
def get_agent_manager() -> 'AgentManager':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")


class ChatRequest(BaseModel):
    session_id: str
    query: str




router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", summary="会话对话", response_model=BaseResponse)
def chat(req: ChatRequest, current_user=Depends(get_current_user), agent_manager: 'AgentManager' = Depends(get_agent_manager)):
    try:
        user_id = current_user
        # 开始锁 agent
        agent = agent_manager.get_and_use_agent(user_id, req.session_id, req.query)


        # 结束锁 agent
        return BaseResponse(msg="success", data=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.modules.services.agent.agent_manager import AgentManager

router = APIRouter()

def get_agent_manager() -> 'AgentManager':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")

def get_current_user(Authorization: Optional[str] = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"user_id": "mock_user_id_from_token"}

class BaseResponse(BaseModel):
    msg: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

class ChatRequest(BaseModel):
    session_id: str
    query: str

@router.post("/chat", summary="会话对话", response_model=BaseResponse)
def chat(req: ChatRequest, current_user=Depends(get_current_user), agent_manager: 'AgentManager' = Depends(get_agent_manager)):
    try:
        user_id = current_user["user_id"]
        agent = agent_manager.get_agent(user_id, req.session_id)
        answer = agent(req.query)
        return BaseResponse(msg="success", data={"answer": answer})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

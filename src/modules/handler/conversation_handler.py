from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, List, Any, Dict

if TYPE_CHECKING:
    from src.modules.services.business.conversation_bussiness import ConversationBusiness
    from src.modules.services.business.record_bussiness import DialogueRecordBusiness

router = APIRouter()

def get_conversation_business() -> 'ConversationBusiness':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")

def get_current_user(Authorization: Optional[str] = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # 这里应校验 token 并返回 user_id，示例直接返回
    return {"user_id": "mock_user_id_from_token"}

def get_record_business() -> 'DialogueRecordBusiness':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")

class BaseResponse(BaseModel):
    msg: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

class CreateSessionRequest(BaseModel):
    name: Optional[str] = Field(None, description="会话名称")

class UpdateSessionNameRequest(BaseModel):
    name: str = Field(..., description="新的会话名称")

class SessionResponse(BaseModel):
    session: Dict[str, Any]

class SessionsResponse(BaseModel):
    sessions: List[Dict[str, Any]]

class HistoryResponse(BaseModel):
    history: List[Dict[str, Any]]

@router.post("/session", summary="创建新会话", response_model=BaseResponse)
def create_session(req: CreateSessionRequest, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        user_id = current_user["user_id"]
        session = conversation_business.create_conversation(user_id, req.name)
        return BaseResponse(msg="Session created", data={"session": session.__dict__})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{session_id}", summary="获取会话详情", response_model=BaseResponse)
def get_session(session_id: str, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        session = conversation_business.get_conversation(session_id)
        return BaseResponse(msg="Success", data={"session": session.__dict__})
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/sessions", summary="列出所有会话", response_model=BaseResponse)
def list_sessions(current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        user_id = current_user["user_id"]
        sessions = conversation_business.list_user_conversations(user_id)
        return BaseResponse(msg="Success", data={"sessions": [s.__dict__ for s in sessions]})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/session/{session_id}/name", summary="更新会话名称", response_model=BaseResponse)
def update_session_name(session_id: str, req: UpdateSessionNameRequest, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        session = conversation_business.update_conversation(session_id, req.name)
        return BaseResponse(msg="Session name updated", data={"session": session.__dict__})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/session/{session_id}", summary="删除会话", response_model=BaseResponse)
def delete_session(session_id: str, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        conversation_business.delete_conversation(session_id)
        return BaseResponse(msg="Session deleted", data=None)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{session_id}/history", summary="获取会话历史", response_model=BaseResponse)
def get_session_history(session_id: str, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business), record_business: 'DialogueRecordBusiness' = Depends(get_record_business)):
    try:
        records = record_business.list_records_by_conversation(session_id)
        return BaseResponse(msg="Success", data={"history": [r.__dict__ for r in records]})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


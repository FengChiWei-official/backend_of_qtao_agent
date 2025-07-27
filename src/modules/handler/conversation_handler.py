from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, List, Any, Dict
from src.utils.response import BaseResponse
from src.utils.auth_dependency import encode_user_id, get_current_user

if TYPE_CHECKING:
    from src.modules.services.business.conversation_bussiness import ConversationBusiness
    from src.modules.services.business.record_bussiness import DialogueRecordBusiness



def get_conversation_business() -> 'ConversationBusiness':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")

def get_record_business() -> 'DialogueRecordBusiness':
    raise NotImplementedError("请在 main.py 中通过 Depends 覆盖此依赖")

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






router = APIRouter(prefix="/api/v1", tags=["conversation"])







@router.post("/session", summary="创建新会话", response_model=BaseResponse)
def create_session(req: CreateSessionRequest, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        user_id = current_user

        session = conversation_business.create_conversation(user_id, req.name)
        return BaseResponse(msg="Session created", data={"session": session.__dict__})
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Session create failed.",
                "error_code": "VALUE_ERROR",
                "error_message": str(e)
            }
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error",
                "message": "Session create failed.",
                "error_code": "SESSION_CONFLICT",
                "error_message": str(e)
            }
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Session create failed.",
                "error_code": "ATTRIBUTE_ERROR",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Session create failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

@router.get("/session/{session_id}", summary="获取会话详情", response_model=BaseResponse)
def get_session(session_id: str, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        session = conversation_business.get_conversation(session_id)
        return BaseResponse(msg="Success", data={"session": session.__dict__})
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": "Session not found.",
                "error_code": "SESSION_NOT_FOUND",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Session fetch failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

@router.get("/sessions", summary="列出所有会话", response_model=BaseResponse)
def list_sessions(current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        user_id = current_user  # 修正为直接取字符串
        sessions = conversation_business.list_user_conversations(user_id)
        return BaseResponse(msg="Success", data={"sessions": [s.__dict__ for s in sessions]})
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": "User not found.",
                "error_code": "USER_NOT_FOUND",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Session list fetch failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

@router.put("/session/{session_id}/name", summary="更新会话名称", response_model=BaseResponse)
def update_session_name(session_id: str, req: UpdateSessionNameRequest, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        session = conversation_business.update_conversation(session_id, req.name)
        return BaseResponse(msg="Session name updated", data={"session": session.__dict__})
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": "Session not found.",
                "error_code": "SESSION_NOT_FOUND",
                "error_message": str(e)
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Session name update failed.",
                "error_code": "VALUE_ERROR",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Session name update failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

@router.delete("/session/{session_id}", summary="删除会话", response_model=BaseResponse)
def delete_session(session_id: str, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business)):
    try:
        conversation_business.delete_conversation(session_id)
        return BaseResponse(msg="Session deleted", data=None)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": "Session not found.",
                "error_code": "SESSION_NOT_FOUND",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Session delete failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )

@router.get("/session/{session_id}/history", summary="获取会话历史", response_model=BaseResponse)
def get_session_history(session_id: str, current_user=Depends(get_current_user), conversation_business: 'ConversationBusiness' = Depends(get_conversation_business), record_business: 'DialogueRecordBusiness' = Depends(get_record_business)):
    try:
        records = record_business.list_records_by_conversation(session_id)
        return BaseResponse(msg="Success", data={"history": [r.__dict__ for r in records]})
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "message": "Session or history not found.",
                "error_code": "SESSION_OR_HISTORY_NOT_FOUND",
                "error_message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Session history fetch failed.",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
        )


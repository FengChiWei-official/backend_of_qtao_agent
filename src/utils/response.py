from pydantic import BaseModel, Field
from typing import Optional, Any

class BaseResponse(BaseModel):
    msg: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

    @classmethod
    def from_exc_detail(cls, detail, data=None):
        if isinstance(detail, dict):
            msg = detail.get("message", str(detail))
        else:
            msg = str(detail)
        return cls(msg=msg, data=data)

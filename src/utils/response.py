from pydantic import BaseModel, Field
from typing import Optional, Any

class BaseResponse(BaseModel):
    msg: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

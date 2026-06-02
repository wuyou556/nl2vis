from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
from datetime import datetime

class MessageCreate(BaseModel):
    """创建消息 - 请求体"""
    content: str

class MessageResponse(BaseModel):
    """响应消息 - 响应体"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sender: Literal["user","agent","system"]
    content: str
    created_at: datetime

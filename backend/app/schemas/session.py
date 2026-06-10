from datetime import datetime
from typing import Optional
from pydantic import BaseModel,Field,ConfigDict

class SessionCreate(BaseModel):
    """创建会话 - 请求体"""

class SessionUpdate(BaseModel):
    """修改会话 - 请求体"""

    title: Optional[str] = Field(default=None,max_length=200)

class SessionResponse(BaseModel):
    """会话信息 - 响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: Optional[str]
    started_at: datetime
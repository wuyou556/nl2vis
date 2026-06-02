from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FileCreate(BaseModel):
    """上传文件元信息"""
    filename: str = Field(min_length=1, max_length=512)


class FileResponse(BaseModel):
    """文件信息 - 响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    filename: str
    storage_path: str
    content_type: Optional[str]
    size: Optional[int]
    uploaded_at: datetime

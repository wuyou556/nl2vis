from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    """文件信息 - 响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    filename: str
    storage_path: str
    content_type: Optional[str]
    size: Optional[int]
    uploaded_at: datetime

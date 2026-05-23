from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, DateTime,func
from app.db.base import Base
from .base_mixins import TimestampMixin

class File(Base, TimestampMixin):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    filename = Column(String(512), nullable=False)
    storage_path = Column(String(1024), nullable=False)  # 本地路径或对象存储 URL
    content_type = Column(String(128), nullable=True)
    size = Column(BigInteger, nullable=True)
    uploaded_at = Column(DateTime, default=func.now)
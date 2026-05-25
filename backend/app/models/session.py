from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base
from .base_mixins import TimestampMixin

class Session(Base, TimestampMixin):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    started_at = Column(DateTime, default=func.now) #会话开始时间
    ended_at = Column(DateTime, nullable=True) #会话结束时间
    status = Column(String(32), default="open")

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message",back_populates="session")
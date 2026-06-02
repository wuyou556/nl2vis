from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(32), nullable=False)  # "user" | "agent" | "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    session = relationship("Session", back_populates="messages")
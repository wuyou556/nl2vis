from datetime import datetime
from sqlalchemy import Column,DateTime

class TimestampMixin:
    created_at = Column(DateTime,default=datetime.now,nullable=False)
    updated_at = Column(DateTime,default=datetime.now,onupdate=datetime.now,nullable=False)
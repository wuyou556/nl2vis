from sqlalchemy import Column,Integer,String,Boolean
from app.db.base import Base
from .base_mixins import TimestampMixin

class User(Base,TimestampMixin):
    __tablename__="users"
    id = Column(Integer,primary_key=True)
    username = Column(String(64),unique=True,nullable=False)
    email = Column(String(128),unique=True,nullable=False)
    hashed_password = Column(String(256),nullable=False)
    is_active = Column(Boolean,default=True,nullable=False)
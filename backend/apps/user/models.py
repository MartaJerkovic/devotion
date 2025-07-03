import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    username = Column(String(32), index=True, nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    avatar = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime, nullable=True, default=None)

    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role})>"

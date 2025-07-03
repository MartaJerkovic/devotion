import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.db import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    color = Column(String(7), nullable=True, default="default_color")
    icon = Column(String(50), nullable=True, default="default_icon")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="categories")
    account = relationship("Account", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")

    def __repr__(self):
        return f"<Category(name={self.name}, is_active={self.is_active})>"

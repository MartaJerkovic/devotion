import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.db import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    timestamp = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    account = relationship("Account", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")

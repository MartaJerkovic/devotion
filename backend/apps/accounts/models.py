import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .schema import AccountType
from core.db import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    account_type = Column(String(20), nullable=False, default=AccountType.SPENDING)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    balance = Column(Numeric(precision=10, scale=2), default=2000.00, nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="accounts")
    categories = relationship("Category", back_populates="account", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account(name={self.name}, balance={self.balance})>"

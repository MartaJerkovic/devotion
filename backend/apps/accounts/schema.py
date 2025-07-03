from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum


class AccountType(str, Enum):
    SPENDING = "spending"
    SAVING = "saving"
    INVESTMENT = "investment"


class AccountBase(BaseModel):
    user_id: str
    account_type: AccountType = AccountType.SPENDING
    name: str
    description: Optional[str] = None
    balance: Optional[Decimal] = Decimal("2000.00")
    currency: Optional[str] = "EUR"


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    balance: Optional[Decimal] = None
    currency: Optional[str] = None


class AccountResponse(AccountBase):
    id: str
    account_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BalanceResponse(BaseModel):
    account_id: str
    balance: Decimal

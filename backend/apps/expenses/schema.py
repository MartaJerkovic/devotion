from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


class ExpenseBase(BaseModel):
    account_id: str
    name: str
    amount: Decimal
    description: Optional[str] = None
    timestamp: date
    category_id: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    id: str
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    timestamp: Optional[date] = None


class ExpenseResponse(ExpenseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExpenseResponseWithBalance(ExpenseBase):
    id: str
    balance: Decimal

    model_config = {"from_attributes": True}


class ExpenseFilters(BaseModel):
    account_id: str
    category_id: Optional[str] = None
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


class ExpenseQueryParams(BaseModel):
    page: int = 1
    per_page: int = 10
    sort_order: Optional[str] = "desc"
    filters: ExpenseFilters


class ExpensePaginatedResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int
    filtered: int

    model_config = {"from_attributes": True}

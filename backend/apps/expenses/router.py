import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session

from .models import Expense
from .schema import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseResponseWithBalance, ExpenseQueryParams, \
    ExpensePaginatedResponse
from .utils import build_expense_filters
from ..user.utils import get_current_user
from ..user.models import User
from ..accounts.models import Account
from core.db import get_db

router = APIRouter(prefix="/expenses", tags=["Expense"])

logger = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_expense(expense_data: ExpenseCreate,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> ExpenseResponseWithBalance:
    try:
        account = db.query(Account).filter(
            Account.id == expense_data.account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or doesn't belong to user"
            )

        new_expense = Expense(
            **expense_data.model_dump()
        )

        account.balance -= expense_data.amount

        db.add(new_expense)
        db.add(account)
        db.flush()
        db.commit()

        logger.info(f"Expense '{new_expense.description}' added for user {current_user.username}. "
                    f"Account '{account.name}' balance updated to {account.balance}")

        if account.balance < 0:
            pass  #TODO Implement socketIO to notify user about negative balance

        return ExpenseResponseWithBalance.model_validate({
            **new_expense.__dict__,
            "account_balance": account.balance
        })
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to add expense for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add expense")

# TODO Implement caching with cachetools or Redis
@router.get("/", status_code=status.HTTP_200_OK)
async def get_expenses(query_data: ExpenseQueryParams, current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)) -> ExpensePaginatedResponse:
    expense_filters = build_expense_filters(query_data.filters)
    per_page = max(query_data.per_page, 1)
    skip = (query_data.page - 1) * per_page
    sort_expr = desc(Expense.timestamp) if query_data.sort_order == "desc" else asc(Expense.timestamp)

    try:
        expenses = (db.query(Expense)
                    .filter(*expense_filters)
                    .order_by(sort_expr)
                    .offset(skip)
                    .limit(per_page).all())

        total = db.query(Expense).filter(*expense_filters).count()
        filtered = len(expenses)

        if not expenses:
            logger.info(f"No expenses found for user {current_user.username} with filters: {expense_filters}")
            return ExpensePaginatedResponse(items=[], total=total, filtered=filtered)

        logger.info(
            f"Retrieved {len(expenses)} expenses for user {current_user.username} with filters: {expense_filters}")
        return ExpensePaginatedResponse(
            items=[ExpenseResponse.model_validate(expense) for expense in expenses],
            total=total,
            filtered=filtered
        )
    except Exception as e:
        logger.exception(f"Failed to retrieve expenses for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve expenses")


@router.get("/{expense_id}", status_code=status.HTTP_200_OK)
async def get_expense(expense_id: int, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> ExpenseResponse:
    try:
        expense = db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == current_user.id
        ).first()

        if not expense:
            logger.warning(f"Expense with ID {expense_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

        logger.info(f"Retrieved expense '{expense.description}' for user {current_user.username}")
        return ExpenseResponse.model_validate(expense)
    except Exception as e:
        logger.exception(f"Failed to retrieve expense with ID {expense_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve expense")


@router.put("/{expense_id}", status_code=status.HTTP_200_OK)
async def update_expense(
        expense_id: int,
        expense_data: ExpenseUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> ExpenseResponseWithBalance:
    update_data = expense_data.model_dump(exclude_unset=True)

    try:
        expense = db.query(Expense).join(Account).filter(
            Expense.id == expense_id,
            Account.user_id == current_user.id
        ).first()

        if not expense:
            logger.warning(f"Expense with ID {expense_id} not found for user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found or access denied"
            )

        old_account = db.query(Account).filter(Account.id == expense.account_id).first()

        old_amount = expense.amount
        new_amount = update_data.get("amount", old_amount)

        account_changed = update_data["account_id"] != expense.account_id

        if account_changed:
            new_account = db.query(Account).filter(
                Account.id == update_data["account_id"],
                Account.user_id == current_user.id
            ).first()

            if not new_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="New account not found or doesn't belong to user"
                )

            old_account.balance += old_amount
            new_account.balance -= new_amount

            db.add(old_account)
            db.add(new_account)

            final_account = new_account
        else:
            balance_difference = new_amount - old_amount
            old_account.balance -= balance_difference

            db.add(old_account)

            final_account = old_account

        for key, value in update_data.items():
            setattr(expense, key, value)

        db.add(expense)
        db.commit()

        logger.info(
            f"Expense '{expense.description}' (ID: {expense_id}) updated for user {current_user.username}. "
            f"Account '{final_account.name}' balance updated to {final_account.balance}"
        )

        return ExpenseResponseWithBalance.model_validate({
            **expense.__dict__,
            "account_balance": final_account.balance
        })
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to update expense with ID {expense_id} for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update expense"
        )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()

        if not expense:
            logger.warning(f"Expense with ID {expense_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

        account = db.query(Account).filter(
            Account.id == expense.account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or doesn't belong to user"
            )

        account.balance += expense.amount

        db.delete(expense)
        db.add(account)
        db.commit()

        logger.info(f"Expense '{expense.description}' deleted for user {current_user.username}. "
                    f"Account '{account.name}' balance updated to {account.balance}")
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to delete expense with ID {expense_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete expense")

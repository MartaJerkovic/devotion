import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc
from sqlalchemy.orm import Session

from .schema import AccountCreate, AccountResponse, AccountType, AccountUpdate, BalanceResponse
from .models import Account
from ..user.utils import get_current_user
from ..user.models import User
from ..categories.utils import create_default_categories_for_account
from core.db import get_db

router = APIRouter(prefix="/accounts", tags=["Account"])

logger = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_account(account_data: AccountCreate,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> AccountResponse:
    try:
        new_account = Account(
            user_id=current_user.id,
            **account_data.model_dump()
        )

        db.add(new_account)
        db.flush()

        if new_account.account_type == AccountType.SPENDING:
            create_default_categories_for_account(current_user.id, new_account.id, db)

        db.commit()

        logger.info(f"Account '{new_account.name}' added for user {current_user.username}")
        return AccountResponse.model_validate(new_account)
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to add account for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add account")


@router.get("/", status_code=status.HTTP_200_OK)
async def get_accounts(current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)) -> list[AccountResponse]:
    try:
        accounts = db.query(Account).filter(Account.user_id == current_user.id).order_by(
            asc(Account.created_at)).all()
        if not accounts:
            logger.info(f"No accounts found for user {current_user.username}")
            return []

        logger.info(f"Retrieved {len(accounts)} accounts for user {current_user.username}")
        return [AccountResponse.model_validate(account) for account in accounts]
    except Exception as e:
        logger.exception(f"Failed to retrieve accounts for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve accounts")


@router.get("/{account_id}", status_code=status.HTTP_200_OK)
async def get_account(account_id: int,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> AccountResponse:
    try:
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            logger.warning(f"Account with ID {account_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        logger.info(f"Retrieved account '{account.name}' for user {current_user.username}")
        return AccountResponse.model_validate(account)
    except Exception as e:
        logger.exception(f"Failed to retrieve account with ID {account_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve account")


@router.put("/{account_id}", status_code=status.HTTP_200_OK)
async def update_account(account_id: str,
                         account_data: AccountUpdate,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)) -> AccountResponse:
    update_data = account_data.model_dump(exclude_unset=True)

    try:
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user.id).first()

        if not account:
            logger.warning(f"Account with ID {account_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        for key, value in update_data.items():
            setattr(account, key, value)

        db.commit()

        logger.info(f"Account '{account.name}' updated for user {current_user.username}")
        return AccountResponse.model_validate(account)
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to update account with ID {account_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update account")


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    try:
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user.id).first()

        if not account:
            logger.warning(f"Account with ID {account_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        db.delete(account)
        db.commit()

        logger.info(f"Account '{account.name}' deleted for user {current_user.username}")
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to delete account with ID {account_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete account")


@router.get("/{account_id}/balance", status_code=status.HTTP_200_OK)
async def get_account_balance(account_id: str,
                              current_user: User = Depends(get_current_user),
                              db: Session = Depends(get_db)) -> Decimal:
    try:
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            logger.warning(f"Account with ID {account_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        logger.info(f"Retrieved balance for account '{account.name}' for user {current_user.username}")
        return BalanceResponse(account_id=account.id, balance=account.balance)
    except Exception as e:
        logger.exception(
            f"Failed to retrieve balance for account with ID {account_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to retrieve account balance")

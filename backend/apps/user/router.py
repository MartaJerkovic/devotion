import logging
from sqlite3 import IntegrityError

from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session

from core.db import get_db
from .schema import UserCreate, Token, UserUpdateSchema, PasswordChangeSchema
from .models import User
from .utils import hash_password, authenticate_user, create_access_token, get_current_user

router = APIRouter(prefix="/user", tags=["User"])

logger = logging.getLogger(__name__)


@router.post("/register")
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        logger.warning(f"User with email {user_data.email} already exists")
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            avatar=user_data.avatar,
            role=user_data.role
        )

        db.add(new_user)
        db.commit()

        logger.info(f"User {user_data.username} created successfully")
        return {"message": "User created successfully", "user_id": new_user.id}
    except IntegrityError as e:
        db.rollback()
        logger.exception(f"Integrity error while creating user {user_data.username}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")


@router.post("/login", response_model=Token)
async def login_using_password(
        email: str = Body(embed=True),
        password: str = Body(embed=True),
        db: Session = Depends(get_db)
):
    user = authenticate_user(db, email, password)

    if not user:
        logger.warning(f"Incorrect email or password for email: {email}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_data": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
        }
    }


@router.get("/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    logger.info(f"Current user: {current_user.username} with role {current_user.role}")
    return {
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role
    }


@router.delete("/me")
async def delete_current_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id

    try:
        db.delete(current_user)
        db.commit()
        logger.info(f"User {user_id} deleted successfully")
        return {"message": "Account deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


@router.put("/me")
async def update_current_user(user_data: UserUpdateSchema,
                              current_user: User = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        logger.warning("No update data provided")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    try:
        for key, value in update_data.items():
            setattr(current_user, key, value)

        db.commit()
        logger.info(f"User {current_user.username} updated successfully")
        return {"message": "User updated successfully", "user": current_user}
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to update user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user")


@router.put("/me/password")
async def change_password(password_data: PasswordChangeSchema,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    try:
        if not authenticate_user(db, current_user.email, password_data.current_password):
            logger.warning(f"Failed password change attempt for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

        if password_data.current_password == password_data.new_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different than the current password")

        current_user.hashed_password = hash_password(password_data.new_password)
        db.commit()

        logger.info(f"Password changed successfully for user {current_user.username}")
        return {"message": "Password changed successfully"}
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to change password for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to change password")

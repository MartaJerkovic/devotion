import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, asc
from sqlalchemy.orm import Session

from core.db import get_db
from .schema import CategoryCreate, CategoryResponse
from .models import Category
from ..user.utils import get_current_user
from ..user.models import User

router = APIRouter(prefix="/categories", tags=["Categories"])

logger = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_category(category_data: CategoryCreate,
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)) -> CategoryResponse:
    try:
        existing_category = db.query(Category).filter(
            Category.user_id == current_user.id,
            func.lower(Category.name) == func.lower(category_data.name.strip())
        ).first()

        if existing_category:
            logger.warning(f"Category '{category_data.name}' already exists for user {current_user.username}")
            raise HTTPException(status_code=400, detail="Category already exists")

        new_category = Category(
            user_id=current_user.id,
            **category_data.model_dump()
        )

        db.add(new_category)
        db.commit()

        logger.info(f"Category '{new_category.name}' added for user {current_user.username}")
        return CategoryResponse.model_validate(new_category)
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to add category for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add category")


@router.get("/", status_code=status.HTTP_200_OK)
async def get_categories(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)) -> list[CategoryResponse]:
    try:
        categories = db.query(Category).filter(Category.user_id == current_user.id).order_by(
            asc(Category.created_at)).all()
        if not categories:
            logger.info(f"No categories found for user {current_user.username}")
            return []

        logger.info(f"Retrieved {len(categories)} categories for user {current_user.username}")
        return [CategoryResponse.model_validate(category) for category in categories]
    except Exception as e:
        logger.exception(f"Failed to retrieve categories for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve categories")


@router.put("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(category_id: str,
                          category_data: CategoryCreate,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> CategoryResponse:
    update_data = category_data.model_dump(exclude_unset=True)

    try:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == current_user.id
        ).first()

        if not category:
            logger.warning(f"Category with ID {category_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        for key, value in update_data.items():
            setattr(category, key, value)

        db.commit()

        logger.info(f"Category '{category.name}' updated for user {current_user.username}")
        return CategoryResponse.model_validate(category)
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to update category for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update category")


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    try:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == current_user.id
        ).first()

        if not category:
            logger.warning(f"Category with ID {category_id} not found for user {current_user.username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        db.delete(category)
        db.commit()

        logger.info(f"Category '{category.name}' deleted for user {current_user.username}")
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to delete category for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete category")

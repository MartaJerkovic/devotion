import logging
from sqlalchemy.orm import Session
from .models import Category

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    {"name": "Groceries", "description": "Food and household items", "color": "#FF5733", "icon": "shopping-cart"},
    {"name": "Rent", "description": "Monthly housing expenses", "color": "#33FF57", "icon": "home"},
    {"name": "Utilities", "description": "Electricity, water, gas bills", "color": "#3357FF", "icon": "bolt"},
    {"name": "Transportation", "description": "Public transport and fuel costs", "color": "#FF33A1", "icon": "car"},
    {"name": "Entertainment", "description": "Movies, games, and leisure activities", "color": "#A133FF",
     "icon": "gamepad"},
    {"name": "Health & Fitness", "description": "Gym memberships and health expenses", "color": "#33FFF5",
     "icon": "dumbbell"},
]


def create_default_categories_for_account(user_id: str, account_id: str, db: Session):
    try:
        for category in DEFAULT_CATEGORIES:
            new_category = Category(
                user_id=user_id,
                account_id=account_id,
                name=category["name"],
                description=category["description"],
                color=category["color"],
                icon=category["icon"]
            )
            db.add(new_category)
        db.commit()

        logger.info(f"Default categories created for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to create default categories for user {user_id}: {e}")

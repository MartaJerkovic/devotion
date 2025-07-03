import os
import importlib
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .settings import DATABASE_URL

logger = logging.getLogger("db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def import_all_db_models():
    apps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps")
    apps_dir = os.path.abspath(apps_dir)
    for app_name in os.listdir(apps_dir):
        app_path = os.path.join(apps_dir, app_name)
        models_path = os.path.join(app_path, "models.py")
        if os.path.isdir(app_path) and os.path.isfile(models_path):
            try:
                importlib.import_module(f"apps.{app_name}.models")
            except ImportError as e:
                logger.error(f"Failed to import models from {app_name}: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

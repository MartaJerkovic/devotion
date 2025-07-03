import sys
import os
import uvicorn
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.db import import_all_db_models, Base, engine
from core.settings import LOGGING, ENVIRONMENT
from apps.user.utils import user_activity_middleware

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_app() -> FastAPI:
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    apps = [
        "apps.user",
        "apps.accounts",
        "apps.categories",
        "apps.expenses",
    ]

    api_app = FastAPI(
        title="API",
        description="Main API endpoints"
    )
    api_app.middleware("http")(user_activity_middleware)

    for app_name in apps:
        try:
            module = __import__(f"{app_name}.router", fromlist=["router"])
            api_app.include_router(module.router)

        except ImportError as e:
            logger.error(f"Failed to import router for {app_name}: {e}")

    fastapi_app = FastAPI()

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["WWW-Authenticate", "Set-Cookie"],
    )

    import_all_db_models()
    if ENVIRONMENT == "development":
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

    fastapi_app.mount("/api", api_app)

    return fastapi_app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

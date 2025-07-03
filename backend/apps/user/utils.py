import logging
from typing import Annotated, Optional
from datetime import timedelta, datetime, timezone
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, Request, Response, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from core.db import get_db
from .models import User
from core.db import SessionLocal

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"User with email {email} not found.")
            return None

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Password verification failed for user {email}.")
            return None

        logger.info(f"User {email} authenticated successfully.")
        return user

    except Exception as e:
        logger.error(f"Error during user authentication: {e}")
        return None


def create_access_token(data: dict, expires_delta=None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error encoding JWT: {e}")
        raise ValueError("Could not create access token") from e


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except jwt.JWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def user_activity_middleware(request: Request, call_next):
    response: Response = await call_next(request)

    if response.status_code != 200:
        return response

    try:
        auth_header = request.headers.get("Authorization")
        last_activity_cookie = request.cookies.get("Last-Activity", "0")
        try:
            last_activity_updated = datetime.fromtimestamp(float(last_activity_cookie), tz=timezone.utc)
        except Exception:
            last_activity_updated = datetime.fromtimestamp(0)

        if auth_header and last_activity_updated < datetime.now(timezone.utc) - timedelta(minutes=1):
            token = auth_header.split(" ")[1]
            db = SessionLocal()
            try:
                user = get_user_from_token(token, db)
                if user:
                    user.last_activity = datetime.now(timezone.utc)
                    db.commit()

                    response.set_cookie(
                        key="Last-Activity",
                        value=str(int(datetime.now(timezone.utc).timestamp())),
                        max_age=5 * 60,
                        httponly=True,
                    )
            finally:
                db.close()
            logger.info("User's last activity updated successfully.")
    except Exception as e:
        logger.warning(f"Failed to update user's activity: {e}")

    return response


def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None

        user = db.query(User).filter(User.email == email).first()
        return user
    except jwt.JWTError as e:
        logger.error(f"JWT error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user from token: {e}")
        return None

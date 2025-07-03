from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = "user"


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = "user"


class Token(BaseModel):
    access_token: str
    token_type: str
    user_data: Optional[UserBase] = None
    user_abilities: Optional[list[dict]] = None


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None


class PasswordChangeSchema(BaseModel):
    current_password: str
    new_password: str

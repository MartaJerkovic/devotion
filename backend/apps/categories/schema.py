from pydantic import BaseModel
from typing import Optional


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#63305D"
    icon: Optional[str] = "tag"


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: str

    model_config = {"from_attributes": True}

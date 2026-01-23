# app/schemas/category_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from marshmallow import fields, Schema

from app.schemas.schemas import MediaSchema


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Tên danh mục")
    description: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    description: Optional[str] = None




class CategoryResponse(Schema):
    id = fields.Integer()
    name = fields.String()
    slug = fields.String()
    description = fields.String()
    avatar = fields.Nested(MediaSchema, dump_only=True)




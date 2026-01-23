# app/schemas/skill_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from marshmallow import fields, Schema

from app.schemas.schemas import MediaSchema
class CreateSkillRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Tên kỹ năng (VD: Python)")
    description: Optional[str] = None
    category_id: int = Field(..., description="ID của danh mục cha")


class UpdateSkillRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    category_id: Optional[int] = None


class SkillResponse(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    category_id = fields.Integer()
    category_name = fields.String()
    avatar = fields.Nested(MediaSchema, dump_only=True)



    class Config:
        from_attributes = True
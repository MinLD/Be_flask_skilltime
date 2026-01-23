# app/schemas/user_skill_schema.py
from marshmallow import Schema, fields
from pydantic import BaseModel, Field, field_validator
from typing import Optional

from .schemas import MediaSchema
from.skill_schema import SkillResponse

class AddUserSkillRequest(BaseModel):
    skill_id: int = Field(..., description="ID kỹ năng muốn đăng ký")
    level: str = Field(..., description="beginner, intermediate, expert")
    proof_link: Optional[str] = Field(None, description="Link CV/Portfolio/Chứng chỉ")

    @field_validator('level')
    def validate_level(cls, v):
        allowed = ['beginner', 'intermediate', 'expert']
        if v not in allowed:
            raise ValueError(f"Level must be one of {allowed}")
        return v

class UpdateUserSkillRequest(BaseModel):
    level: Optional[str] = None
    proof_link: Optional[str] = None

    @field_validator('level')
    def validate_level(cls, v):
        if v and v not in ['beginner', 'intermediate', 'expert']:
            raise ValueError("Invalid level")
        return v

class UserSkillResponse(Schema):
    id = fields.Integer()
    skill_id = fields.Integer()

    level = fields.String()
    proof_link = fields.String()
    is_verified = fields.Boolean()
    skill = fields.Nested(SkillResponse)
    avatar = fields.Nested(MediaSchema, dump_only=True)


    class Config:
        from_attributes = True
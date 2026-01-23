from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email người dùng")
    password: str = Field(..., min_length=8, description="Mật khẩu tối thiểu 8 ký tự")
    fullname: str = Field(..., min_length=2, max_length=50, description="Họ và tên tối thiểu trên 2 ký tự")


class CreateUserRequest(BaseModel):
    email: EmailStr = Field(..., description="Login Email (Unique)")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    wallet_balance: float = Field(0.0, ge=0, description="Initial wallet balance")

    fullname: str = Field(..., min_length=2, max_length=100, description="Full Name")
    phone: Optional[str] = Field(None, max_length=10, pattern=r'^\d+$', description="Phone number (digits only)")
    bio: Optional[str] = Field(None, max_length=255, description="Short Bio")
    date_of_birth: Optional[datetime] = Field(None, description="Date of Birth (YYYY-MM-DD)")
    avatar: Optional[str] = Field(None, description="Avatar Image")

    role: str = Field(..., description="Role name: admin, user, mod...")

    @field_validator('role')
    def lowercase_role(cls, v):
        return v.lower()

class UpdateProfileRequest(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Login Email (Unique)")
    fullname: Optional[str] = Field(None, min_length=2, max_length=100, description="Full Name")
    phone: Optional[str] = Field(None, max_length=10, pattern=r'^\d+$', description="Phone number (digits only)")
    bio: Optional[str] = Field(None, max_length=255, description="Short Bio")
    date_of_birth: Optional[datetime] = Field(None, description="Date of Birth (YYYY-MM-DD)")
    social_links: Optional[dict] = Field(None, description="Social Links")

class AdminUpdateProfileRequest(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Login Email (Unique)")
    fullname: Optional[str] = Field(None, min_length=2, max_length=100, description="Full Name")
    phone: Optional[str] = Field(None, max_length=10, pattern=r'^\d+$', description="Phone number (digits only)")
    bio: Optional[str] = Field(None, max_length=255, description="Short Bio")
    date_of_birth: Optional[datetime] = Field(None, description="Date of Birth (YYYY-MM-DD)")
    social_links: Optional[dict] = Field(None, description="Social Links")

    wallet_balance: Optional[float] = Field(0.0, ge=0, description="Initial wallet balance")
    status: Optional[str] = Field(None, description="Status")
    reputation_score: Optional[int] = Field(None, description="Reputation Score")


    role: Optional[str] = Field(None, description="Role name: admin, user, mod...")

    @field_validator('role')
    def lowercase_role(cls, v):
        if v is None: return None
        return v.lower()



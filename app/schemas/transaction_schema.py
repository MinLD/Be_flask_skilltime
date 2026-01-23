# app/schemas/transaction_schema.py
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TransferRequest(BaseModel):
    receiver_id: str = Field(..., description="ID của người nhận (Mentor)")
    amount: int = Field(..., gt=0, description="Số Credits muốn chuyển (phải > 0)")
    description: str = Field(..., min_length=5, description="Nội dung chuyển (VD: Trả tiền học Python)")


class TransactionResponse(BaseModel):
    id: str
    trans_type: str  # earn, spend
    amount: int
    balance_after: int
    description: str
    created_at: datetime # Dạng chuỗi ISO

    # Thông tin người liên quan (Người gửi hoặc Người nhận)
    related_user_name: Optional[str] = None

    class Config:
        from_attributes = True
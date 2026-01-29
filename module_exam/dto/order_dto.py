from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class OrderDTO(BaseModel):
    """订单DTO"""
    id: Optional[int] = None
    order_no: Optional[str] = None
    user_id: Optional[int] = None
    status: Optional[str] = None
    total_amount: Optional[Decimal] = None
    pay_amount: Optional[Decimal] = None
    pay_time: Optional[datetime] = None
    pay_channel: Optional[str] = None
    transaction_id: Optional[str] = None
    refund_time: Optional[datetime] = None
    refund_amount: Optional[Decimal] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class OrderCreateDTO(BaseModel):
    """订单创建DTO"""
    user_id: int
    product_id: int
    total_amount: Decimal
    description: str
    create_time: Optional[datetime] = datetime.now()
    update_time: Optional[datetime] = datetime.now()

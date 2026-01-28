from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from typing import Optional

class OrderProductDTO(BaseModel):
    """订单商品DTO"""
    id: Optional[int] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    product_price: Optional[Decimal] = None
    quantity: Optional[int] = None
    subtotal: Optional[Decimal] = None
    create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class OrderProductCreateDTO(BaseModel):
    """创建订单商品DTO"""
    order_id: int
    product_id: int
    product_name: str
    product_price: Decimal
    quantity: int = 1
    subtotal: Decimal
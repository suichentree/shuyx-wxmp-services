from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductDTO(BaseModel):
    """商品DTO"""
    id: Optional[int] = None
    name: Optional[str] = None
    cover_image: Optional[str] = None
    description: Optional[str] = None
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    type_name: Optional[str] = None
    type_code: Optional[str] = None
    status: Optional[int] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ProductCreateDTO(BaseModel):
    """创建商品DTO"""
    name: str
    cover_image: Optional[str] = None
    description: Optional[str] = None
    current_price: Decimal
    original_price: Optional[Decimal] = None
    type_name: str
    type_code: str
    status: int = 1

class ProductUpdateDTO(BaseModel):
    """更新商品DTO"""
    name: Optional[str] = None
    cover_image: Optional[str] = None
    description: Optional[str] = None
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    type_name: Optional[str] = None
    status: Optional[int] = None
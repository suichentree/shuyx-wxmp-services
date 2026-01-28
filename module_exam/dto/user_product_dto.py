from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserProductDTO(BaseModel):
    """用户商品DTO"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    product_id: Optional[int] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    expire_time: Optional[datetime] = None
    is_valid: Optional[bool] = None
    create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserProductCreateDTO(BaseModel):
    """创建用户商品DTO"""
    user_id: int
    product_id: int
    source_type: str = 'PURCHASE'
    source_id: Optional[int] = None
    expire_time: Optional[datetime] = None

class UserProductUpdateDTO(BaseModel):
    """更新用户商品DTO"""
    source_type: Optional[str] = None
    expire_time: Optional[datetime] = None
    is_valid: Optional[bool] = None
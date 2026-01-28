# 导入sqlalchemy框架中的相关字段
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, DateTime, func, Index, DECIMAL, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from module_exam.model.base_model import myBaseModel

class UserProductModel(myBaseModel):
    """
    用户商品表 t_user_product
    记录用户拥有的商品
    """
    __tablename__ = 't_user_product'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='用户商品id')
    user_id: Mapped[int] = MappedColumn(Integer, ForeignKey('mp_user.id'), nullable=False, comment='用户id')
    product_id: Mapped[int] = MappedColumn(Integer, ForeignKey('t_product.id'), nullable=False, comment='商品id')

    # 来源：FREE-免费获得，PURCHASE-购买获得，GIFT-赠送获得
    source_type: Mapped[str] = MappedColumn(String(20), default='PURCHASE', comment='获得方式')
    source_id: Mapped[int] = MappedColumn(Integer, nullable=True, comment='来源ID（如订单ID）')

    expire_time: Mapped[datetime] = MappedColumn(DateTime, nullable=True, comment='过期时间，NULL表示永久有效')
    is_valid: Mapped[bool] = MappedColumn(Boolean, default=True, comment='是否有效')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_product_id', 'product_id'),
        Index('index_user_product', 'user_id', 'product_id'),
        Index('index_source_type', 'source_type'),
    )
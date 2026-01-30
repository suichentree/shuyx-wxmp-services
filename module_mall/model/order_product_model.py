# 导入sqlalchemy框架中的相关字段
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, func, Index, DECIMAL
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from base.base_model import myBaseModel

# 订单商品明细表
class OrderProductModel(myBaseModel):
    """
    订单商品明细表 t_order_product
    存储订单中的商品明细
    """
    __tablename__ = 't_order_product'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='订单项id')
    order_id: Mapped[int] = MappedColumn(Integer,nullable=False, comment='订单id')

    # 购买时的商品快照信息(购买时的商品名称和价格，防止商品信息变化导致订单金额异常)
    product_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='商品id')
    product_name: Mapped[str] = MappedColumn(String(200), nullable=False, comment='商品快照名称')
    product_price: Mapped[Decimal] = MappedColumn(DECIMAL(10, 2), nullable=False, comment='商品单价')

    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_order_id', 'order_id'),
    )
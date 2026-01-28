# 导入sqlalchemy框架中的相关字段
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, func, Index, DECIMAL, Boolean
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from module_exam.model.base_model import myBaseModel

class ProductModel(myBaseModel):
    """
    商品表 t_product
    存储所有商品信息，支持多种商品类型（如考试商品、课程商品、会员商品，优惠卷商品等）
    """
    __tablename__ = 't_product'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='商品id')
    name: Mapped[str] = MappedColumn(String(200), nullable=False, comment='商品名称')
    cover_image: Mapped[str] = MappedColumn(String(500), nullable=True, comment='商品封面图')
    description: Mapped[str] = MappedColumn(String(1000), nullable=True, comment='商品描述')
    current_price: Mapped[Decimal] = MappedColumn(DECIMAL(10, 2), nullable=False, comment='商品现价')
    original_price: Mapped[Decimal] = MappedColumn(DECIMAL(10, 2), nullable=True, comment='商品原价')
    type_name: Mapped[str] = MappedColumn(String(100), nullable=False, comment='商品类型名称')
    type_code: Mapped[str] = MappedColumn(String(50), unique=True, nullable=False, comment='商品类型编码，如：EXAM, COURSE, VIP')
    status: Mapped[int] = MappedColumn(Integer, default=1, comment='商品状态 1上架 0下架')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())
    update_time: Mapped[datetime] = MappedColumn(DateTime, comment='更新时间', default=func.now(), onupdate=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_product_type_id', 'product_type_id'),
        Index('index_status', 'status'),
        Index('index_is_free', 'is_free'),
    )

    @property
    def is_free(self):
        """通过现价判断是否免费"""
        return self.current_price == 0


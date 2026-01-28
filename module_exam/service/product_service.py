from typing import List
from decimal import Decimal

from module_exam.dao.product_dao import ProductDao
from module_exam.model.product_model import ProductModel
from module_exam.service.base_service import BaseService

class ProductService(BaseService[ProductModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = ProductDao()
        super().__init__(dao=self.dao_instance)

    def get_products_by_type(self, db_session, type_code: str, include_inactive: bool = False):
        """根据商品类型获取商品列表"""
        status = None if include_inactive else 1
        return self.dao_instance.get_by_type_code(db_session, type_code, status)

    def get_active_products(self, db_session):
        """获取上架的商品列表"""
        return self.dao_instance.get_by_status(db_session, 1)

    def create_product(self, db_session, product_data):
        """创建商品"""
        return self.dao_instance.create(db_session, product_data)

    def update_product_price(self, db_session, product_id: int, new_price: Decimal):
        """更新商品价格"""
        return self.dao_instance.update_by_id(db_session, product_id, {'current_price': new_price})

    def is_product_free(self, product: ProductModel):
        """判断商品是否免费"""
        return product.current_price == 0

    def calculate_discount_price(self, original_price: Decimal, discount_rate: float):
        """计算折扣价格"""
        return original_price * Decimal(discount_rate)
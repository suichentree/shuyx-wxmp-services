from typing import List
from datetime import datetime, timedelta

from module_exam.dao.user_product_dao import UserProductDao
from module_exam.model.user_product_model import UserProductModel
from module_exam.service.base_service import BaseService


class UserProductService(BaseService[UserProductModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = UserProductDao()
        super().__init__(dao=self.dao_instance)

    def add_user_product(self, db_session, user_id: int, product_id: int, source_type: str = 'PURCHASE', source_id: int = None, expire_days: int = None):
        """为用户添加商品"""
        expire_time = None
        if expire_days:
            expire_time = datetime.now() + timedelta(days=expire_days)

        user_product_data = {
            'user_id': user_id,
            'product_id': product_id,
            'source_type': source_type,
            'source_id': source_id,
            'expire_time': expire_time
        }

        return self.dao_instance.add(db_session, user_product_data)

    def check_user_product_access(self, db_session, user_id: int, product_id: int):
        """检查用户是否有商品访问权限"""
        user_product = self.dao_instance.get_by_user_and_product(db_session, user_id, product_id)

        if not user_product:
            return False

        if not user_product.is_valid:
            return False

        if user_product.expire_time and user_product.expire_time < datetime.now():
            return False

        return True

    def get_user_valid_products(self, db_session, user_id: int):
        """获取用户有效的商品列表"""
        return self.dao_instance.get_valid_products(db_session, user_id)

    def invalidate_user_product(self, db_session, user_product_id: int):
        """使用户商品失效"""
        return self.dao_instance.update_by_id(db_session, user_product_id, {'is_valid': False})

    def extend_product_expiry(self, db_session, user_product_id: int, additional_days: int):
        """延长商品有效期"""
        user_product = self.dao_instance.get_by_id(db_session, user_product_id)
        if user_product and user_product.expire_time:
            new_expire_time = user_product.expire_time + timedelta(days=additional_days)
            return self.dao_instance.update_by_id(db_session, user_product_id, {'expire_time': new_expire_time})
        return None
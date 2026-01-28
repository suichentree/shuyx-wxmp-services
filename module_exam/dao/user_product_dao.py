from module_exam.model.user_product_model import UserProductModel
from module_exam.dao.base_dao import BaseDao

class UserProductDao(BaseDao[UserProductModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model=UserProductModel)

    def get_by_user_id(self, db_session, user_id: int, is_valid: bool = None):
        """根据用户ID获取用户商品列表"""
        query = db_session.query(self.model).filter(self.model.user_id == user_id)
        if is_valid is not None:
            query = query.filter(self.model.is_valid == is_valid)
        return query.all()

    def get_by_user_and_product(self, db_session, user_id: int, product_id: int):
        """根据用户ID和商品ID获取用户商品"""
        return db_session.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.product_id == product_id
        ).first()

    def get_valid_products(self, db_session, user_id: int):
        """获取用户有效的商品列表"""
        from datetime import datetime
        return db_session.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.is_valid == True,
            (self.model.expire_time.is_(None)) | (self.model.expire_time > datetime.now())
        ).all()
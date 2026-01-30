from module_mall.model.product_model import ProductModel
from base.base_dao import BaseDao

class ProductDao(BaseDao[ProductModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model=ProductModel)

    def get_by_type_code(self, db_session, type_code: str, status: int = None):
        """根据商品类型编码获取商品列表"""
        query = db_session.query(self.model).filter(self.model.type_code == type_code)
        if status is not None:
            query = query.filter(self.model.status == status)
        return query.all()

    def get_by_status(self, db_session, status: int = 1):
        """根据状态获取商品列表"""
        return db_session.query(self.model).filter(self.model.status == status).all()
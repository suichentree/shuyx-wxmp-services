from module_exam.model.order_product_model import OrderProductModel
from module_exam.dao.base_dao import BaseDao

class OrderProductDao(BaseDao[OrderProductModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model=OrderProductModel)

    def get_by_order_id(self, db_session, order_id: int):
        """根据订单ID获取订单商品列表"""
        return db_session.query(self.model).filter(self.model.order_id == order_id).all()

    def get_by_product_id(self, db_session, product_id: int):
        """根据商品ID获取订单商品列表"""
        return db_session.query(self.model).filter(self.model.product_id == product_id).all()
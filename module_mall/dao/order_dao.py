from module_mall.model.order_model import OrderModel
from base.base_dao import BaseDao

class OrderDao(BaseDao[OrderModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model=OrderModel)

    def get_by_order_no(self, db_session, order_no: str):
        """根据订单号获取订单"""
        return db_session.query(self.model).filter(self.model.order_no == order_no).first()

    def get_by_user_id(self, db_session, user_id: int, status: str = None):
        """根据用户ID获取订单列表"""
        query = db_session.query(self.model).filter(self.model.user_id == user_id)
        if status:
            query = query.filter(self.model.status == status)
        return query.order_by(self.model.create_time.desc()).all()
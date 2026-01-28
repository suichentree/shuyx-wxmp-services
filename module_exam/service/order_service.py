from typing import List
from datetime import datetime

from module_exam.dao.order_dao import OrderDao
from module_exam.dao.order_product_dao import OrderProductDao
from module_exam.model.order_model import OrderModel
from module_exam.service.base_service import BaseService


class OrderService(BaseService[OrderModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = OrderDao()
        super().__init__(dao=self.dao_instance)
        self.order_product_dao = OrderProductDao()

    def create_order(self, db_session, order_data, order_items):
        """创建订单及订单项"""
        # 创建订单
        order = self.dao_instance.create(db_session, order_data)

        # 创建订单项
        for item in order_items:
            item.order_id = order.id
            self.order_product_dao.create(db_session, item)

        return order

    def get_order_with_items(self, db_session, order_id: int):
        """获取订单及订单项详情"""
        order = self.dao_instance.get_by_id(db_session, order_id)
        if order:
            order_items = self.order_product_dao.get_by_order_id(db_session, order_id)
            return order, order_items
        return None, []

    def update_order_status(self, db_session, order_id: int, status: str, **kwargs):
        """更新订单状态"""
        update_data = {'status': status}
        if status == 'PAID':
            update_data['pay_time'] = datetime.now()
            update_data.update(kwargs)
        elif status == 'REFUNDED':
            update_data['refund_time'] = datetime.now()
            update_data.update(kwargs)

        return self.dao_instance.update_by_id(db_session, order_id, update_data)

    def get_user_orders(self, db_session, user_id: int, status: str = None):
        """获取用户订单列表"""
        return self.dao_instance.get_by_user_id(db_session, user_id, status)
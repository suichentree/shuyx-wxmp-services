from sqlalchemy.orm import Session

from module_mall.dao.order_product_dao import OrderProductDao
from module_mall.model.order_product_model import OrderProductModel
from base.base_service import BaseService



# 继承Service类，专注于业务操作, 可添加自定义方法
class OrderProductService(BaseService[OrderProductModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = OrderProductDao()
        super().__init__(dao = self.dao_instance)

    # 可以根据业务需求添加自定义方法


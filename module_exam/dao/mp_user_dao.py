from module_exam.model.mp_user_model import MpUserModel
from base.base_dao import BaseDao



# 继承BaseDao类，专注于数据访问操作, 可添加自定义方法
class MpUserDao(BaseDao[MpUserModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model = MpUserModel)

    # 可以根据业务需求添加自定义方法

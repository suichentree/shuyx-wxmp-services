from module_exam.model.mp_user_option_model import MpUserOptionModel
from module_exam.dao.base_dao import BaseDao

# 继承BaseDao类，专注于数据访问操作, 可添加自定义方法
class MpUserOptionDao(BaseDao[MpUserOptionModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model = MpUserOptionModel)

    # 可以根据业务需求添加自定义方法

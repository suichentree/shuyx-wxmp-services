from module_exam.dao.mp_user_dao import MpUserDao
from module_exam.model.mp_user_model import MpUserModel
from base.base_service import BaseService

# 继承Service类，专注于业务操作, 可添加自定义方法
class MpUserService(BaseService[MpUserModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = MpUserDao()
        super().__init__(dao=self.dao_instance)

    # 可以根据业务需求添加自定义方法

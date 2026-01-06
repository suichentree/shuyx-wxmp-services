from typing import List

from module_exam.dao.mp_exam_dao import MpExamDao
from module_exam.model.mp_exam_model import MpExamModel
from module_exam.service.base_service import BaseService

# 继承Service类，专注于业务操作, 可添加自定义方法
class MpExamService(BaseService[MpExamModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = MpExamDao()
        super().__init__(dao = self.dao_instance)

    # 可以根据业务需求添加自定义方法



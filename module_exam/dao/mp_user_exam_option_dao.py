from module_exam.model.mp_user_exam_option_model import MpUserExamOptionModel
from module_exam.dao.base_dao import BaseDao

# 继承BaseDao类，专注于数据访问操作, 可添加自定义方法
class MpUserExamOptionDao(BaseDao[MpUserExamOptionModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model = MpUserExamOptionModel)

    # 可以根据业务需求添加自定义方法

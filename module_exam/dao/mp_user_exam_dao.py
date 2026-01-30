from sqlalchemy import desc

from module_exam.model.mp_user_exam_model import MpUserExamModel
from base.base_dao import BaseDao



# 继承BaseDao类，专注于数据访问操作, 可添加自定义方法
class MpUserExamDao(BaseDao[MpUserExamModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model = MpUserExamModel)

    # 可以根据业务需求添加自定义方法

    # 查询最后一个已完成的考试记录
    def findLastOneByIsFinish(self, db):
        return db.query(self.model).filter(self.model.finish_time != None).order_by(desc(self.model.id)).first()


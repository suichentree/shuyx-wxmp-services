from sqlalchemy.orm import Session

from module_exam.dao.mp_user_exam_dao import MpUserExamDao
from module_exam.model.mp_user_exam_model import MpUserExamModel
from base.base_service import BaseService

# 继承Service类，专注于业务操作, 可添加自定义方法
class MpUserExamService(BaseService[MpUserExamModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = MpUserExamDao()
        super().__init__(dao = self.dao_instance)

    # 可以根据业务需求添加自定义方法


    def find_last_one_not_finished_user_exam(self, db_session: Session,user_id:int, exam_id:int):
        """
        查询用户最近的未完成的测试记录
        """

        # 根据user_id, exam_id, finish_time 字段 查询最近的未完成记录,按照id降序
        last_not_finished_user_exam = self.dao_instance.get_one_by_filter(db_session, {"user_id": user_id,"exam_id": exam_id,"finish_time": False}, ["-id"])
        return last_not_finished_user_exam


    def find_last_one_finished_user_exam(self, db_session: Session,user_id:int, exam_id:int):
        """
        查询用户最近的已完成的测试记录
        """
        # 根据user_id, exam_id, finish_time 字段 查询最近的已完成记录,按照id降序
        last_finished_user_exam = self.dao_instance.get_one_by_filter(db_session, {"user_id": user_id, "exam_id": exam_id, "finish_time": True}, ["-id"])
        return last_finished_user_exam

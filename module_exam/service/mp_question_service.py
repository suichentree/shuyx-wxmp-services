from module_exam.dao.mp_question_dao import MpQuestionDao
from module_exam.model.mp_question_model import MpQuestionModel
from module_exam.service.base_service import BaseService

# 继承Service类，专注于业务操作, 可添加自定义方法
class MpQuestionService(BaseService[MpQuestionModel]):
    def __init__(self):
        """
        初始化服务实例
        创建DAO实例并传递给基类
        """
        self.dao_instance = MpQuestionDao()
        super().__init__(dao = self.dao_instance)

    # 可以根据业务需求添加自定义方法

    def get_questions_with_options(self, db_session, exam_id: int):
        """
        根据考试ID获取问题和对应的选项
        :param exam_id: 考试ID
        :return: 包含问题和选项的列表
        """
        # 查询问题列表

        # 查询指定exam_id的所有问题
        questions_options_list = self.dao_instance.get_questions_with_options(db_session, exam_id)

        return questions_options_list

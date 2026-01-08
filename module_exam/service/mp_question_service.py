from typing import List

from module_exam.dao.mp_question_dao import MpQuestionDao
from module_exam.dto.mp_option_dto import MpOptionDTO
from module_exam.dto.mp_question_dto import MpQuestionDTO, MpQuestionOptionDTO
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

    def get_questions_with_options(self, db_session, exam_id: int) -> List[MpQuestionOptionDTO]:
        """
        根据考试ID获取问题和对应的选项
        :param exam_id: 考试ID
        :return: 包含问题和选项的列表
        """

        # 查询指定exam_id的所有问题
        query_result = self.dao_instance.get_questions_with_options(db_session, exam_id)

        # 构建问题选项字典
        question_option_dict = {}
        for question, option in query_result:
            if question.id not in question_option_dict:
                # 初始化问题条目
                question_option_dict[question.id] = {
                    "question": question,
                    "options": []
                }
            # 如果选项不为None（outerjoin可能产生None），则添加到选项列表
            if option is not None:
                question_option_dict[question.id]["options"].append(option)


        # 转换为问题选项DTO列表
        result_dto = []
        for data in question_option_dict.values():
            dto = MpQuestionOptionDTO(
                question=MpQuestionDTO.model_validate(data["question"]),
                options=[MpOptionDTO.model_validate(opt) for opt in data["options"]]
            )
            result_dto.append(dto)

        # 返回问题选项DTO列表
        return result_dto

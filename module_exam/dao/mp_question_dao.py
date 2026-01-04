from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from module_exam.dto.mp_option_dto import MpOptionDTO
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO, MpQuestionDTO
from module_exam.model.mp_option_model import MpOptionModel
from module_exam.model.mp_question_model import MpQuestionModel
from module_exam.dao.base_dao import BaseDao

# 继承BaseDao类，专注于数据访问操作, 可添加自定义方法
class MpQuestionDao(BaseDao[MpQuestionModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model = MpQuestionModel)

    # 可以根据业务需求添加自定义方法
    def get_questions_with_options(self, db_session: Session, exam_id: int):
        """
        使用join查询获取指定exam_id的问题及其选项
        :param db_session: 数据库会话
        :param exam_id: 考试ID
        :return: 包含问题和选项的字典列表
        """
        # 使用join查询获取问题和对应的选项
        result = db_session.query(
            MpQuestionModel,
            MpOptionModel
        ).outerjoin(
            MpOptionModel,
            (MpQuestionModel.id == MpOptionModel.question_id) & (MpOptionModel.status == 0)
        ).filter(
            MpQuestionModel.exam_id == exam_id,
            MpQuestionModel.status == 0
        ).all()

        return result

    def get_questions_with_options222(self, db_session: Session, exam_id: int):
        """
        使用join查询获取指定exam_id的问题及其选项
        :param db_session: 数据库会话
        :param exam_id: 考试ID
        :return: 包含问题和选项的字典列表
        """
        # 使用join查询获取问题和对应的选项
        sql = select(MpQuestionModel,MpOptionModel).outerjoin(
            MpOptionModel,
            (MpQuestionModel.id == MpOptionModel.question_id) & (MpOptionModel.status == 0)
        ).where(
            MpQuestionModel.exam_id == exam_id,
            MpQuestionModel.status == 0
        )

        result = db_session.execute(sql).all()

        return result
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session
from module_exam.model.mp_option_model import MpOptionModel
from module_exam.model.mp_question_model import MpQuestionModel
from module_exam.dao.base_dao import BaseDao

# 继承BaseDao类，专注于数据访问操作, 可添加自定义方法
class MpQuestionDao(BaseDao[MpQuestionModel]):
    def __init__(self):
        """初始化DAO实例"""
        super().__init__(model = MpQuestionModel)

    def get_questions_with_options(self, db_session: Session, exam_id: int):
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

        return db_session.execute(sql).all()

    def get_questions_with_options_by_questionids(self, db_session: Session, question_ids: List[int]):
        """
        使用join查询获取指定exam_id的问题及其选项
        :param db_session: 数据库会话
        :param question_ids: 题目ID列表
        :return: 包含问题和选项的字典列表
        """
        # 使用join查询获取问题和对应的选项
        sql = select(MpQuestionModel,MpOptionModel).outerjoin(
            MpOptionModel,
            (MpQuestionModel.id == MpOptionModel.question_id) & (MpOptionModel.status == 0)
        ).where(
            MpQuestionModel.id.in_(question_ids),
            MpQuestionModel.status == 0
        )
        return db_session.execute(sql).all()

    def get_one_questions_with_options(self, db_session: Session, question_id: int):
        """
        使用join查询获取指定question_id的问题及其选项
        :param db_session: 数据库会话
        :param question_id: 问题ID
        :return: 包含问题和选项的字典列表
        """
        # 使用join查询获取问题和对应的选项
        sql = select(MpQuestionModel,MpOptionModel).outerjoin(
            MpOptionModel,
            (MpQuestionModel.id == MpOptionModel.question_id) & (MpOptionModel.status == 0)
        ).where(
            MpQuestionModel.id == question_id,
            MpQuestionModel.status == 0
        )

        return db_session.execute(sql).all()
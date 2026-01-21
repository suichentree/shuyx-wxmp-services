# 导入sqlalchemy框架中的相关字段
from datetime import datetime,date
from typing import List

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index, JSON
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from module_exam.model.base_model import myBaseModel

class MpUserQuestionEbbinghausTrackModel(myBaseModel):
    """
    用户题目艾宾浩斯轨迹表 mp_user_question_ebbinghaus_track
    该表记录，用户在某一个题目的答题情况。然后根据艾宾浩斯记忆曲线，计算出下一次需要复习该题目时的时间。
    """
    __tablename__ = 'mp_user_question_ebbinghaus_track'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='用户选项id')
    user_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户id')
    exam_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='测试id')
    question_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='问题id')
    question_type: Mapped[int] = MappedColumn(Integer, nullable=False, comment='问题类型')
    correct_count: Mapped[int] = MappedColumn(Integer, nullable=False, comment='做对次数')
    error_count: Mapped[int] = MappedColumn(Integer, nullable=False, comment='做错次数')
    total_count: Mapped[int] = MappedColumn(Integer, nullable=False, comment='总做题次数')
    last_answer_time: Mapped[date] = MappedColumn(DateTime, nullable=False, comment='最后一次答题时间')
    next_review_time: Mapped[date] = MappedColumn(DateTime, nullable=False, comment='下一次复习的时间')
    status: Mapped[int] = MappedColumn(Integer, nullable=False, comment='题目做题状态：待复习0 已巩固1')
    cycle_index: Mapped[int] = MappedColumn(Integer, nullable=False, comment='艾宾浩斯记忆周期索引，初始索引为0，记忆周期是[1,3,7,14,30]。-1表示已巩固')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())
    update_time: Mapped[datetime] = MappedColumn(DateTime, comment='更新时间', default=func.now(), onupdate=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_question_id', 'question_id'),
        Index('index_next_review_time', 'next_review_time'),
        Index('index_status', 'status'),
    )
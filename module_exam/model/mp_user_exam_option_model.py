# 导入sqlalchemy框架中的相关字段
from datetime import datetime
from typing import List

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index, JSON
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from module_exam.model.base_model import myBaseModel

class MpUserExamOptionModel(myBaseModel):
    """
    用户选项表 mp_user_exam_option
    """
    __tablename__ = 'mp_user_exam_option'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='用户选项id')
    user_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户id')
    exam_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='测试id')
    user_exam_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户测试id')
    question_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='问题id')
    option_ids: Mapped[List[int] | int] = MappedColumn(JSON, nullable=False, comment='选项id数组，单选是int,多选是列表。例如：1或[1, 3, 5, ...]')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_exam_id', 'exam_id'),
        Index('index_user_exam_id', 'user_exam_id'),
    )
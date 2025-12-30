# 导入sqlalchemy框架中的相关字段
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from config.database_config import myBase

class MpUserExamModel(myBase):
    """
    用户测试表 mp_user_exam
    """
    __tablename__ = 'mp_user_exam'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='用户测试id')
    user_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户id')
    exam_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='测试id')
    page_no: Mapped[int] = MappedColumn(Integer, nullable=False, comment='当前页码')
    score: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户测试分数')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())
    finish_time: Mapped[datetime] = MappedColumn(DateTime, comment='测试完成时间')

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_exam_id', 'exam_id'),
    )
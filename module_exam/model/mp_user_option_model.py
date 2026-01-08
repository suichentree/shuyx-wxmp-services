# 导入sqlalchemy框架中的相关字段
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from config.database_config import myBase

class MpUserOptionModel(myBase):
    """
    用户选项表 mp_user_option
    """
    __tablename__ = 'mp_user_option'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='用户选项id')
    user_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户id')
    exam_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='测试id')
    user_exam_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户测试id')
    question_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='问题id')
    option_id: Mapped[str] = MappedColumn(String(255), nullable=False, comment='选项id数组')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_exam_id', 'exam_id'),
        Index('index_user_exam_id', 'user_exam_id'),
    )
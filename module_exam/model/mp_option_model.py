# 导入sqlalchemy框架中的相关字段
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from module_exam.model.base_model import myBaseModel

class MpOptionModel(myBaseModel):
    """
    选项表 mp_option
    """
    __tablename__ = 'mp_option'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='选项id')
    question_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='问题id')
    content: Mapped[str] = MappedColumn(String(500), nullable=False, comment='选项内容')
    is_right: Mapped[int] = MappedColumn(Integer, default=0, comment='选项是否正确 0错误 1正确')
    status: Mapped[int] = MappedColumn(Integer, default=0, comment='状态 0正常 -1停用')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now()) # 默认为当前时间

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_question_id', 'question_id'),
    )
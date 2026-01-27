# 导入sqlalchemy框架中的相关字段
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index, DECIMAL
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from module_exam.model.base_model import myBaseModel

class MpExamModel(myBaseModel):
    """
    测试表 mp_exam
    """
    __tablename__ = 'mp_exam'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='测试id')
    name: Mapped[str] = MappedColumn(String(50), unique=True, nullable=False, comment='测试名称')
    tag: Mapped[str] = MappedColumn(String(20), unique=True, nullable=False, comment='测试标签')
    status: Mapped[int] = MappedColumn(Integer, default=0, comment='测试状态 0正常 -1停用')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now()) # 默认为当前时间

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_name', 'name'),
    )

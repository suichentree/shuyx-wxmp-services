# 导入sqlalchemy框架中的相关字段
from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
# 导入公共基类
from config.database_config import myBase

class MpQuestionModel(myBase):
    """
    问题表 mp_question
    """
    __tablename__ = 'mp_question'

    id = Column("id",Integer, primary_key=True, autoincrement=True, comment='问题id')
    exam_id = Column("exam_id", Integer, nullable=False, comment='测试id')
    name = Column("name",String(500),nullable=False, comment='问题名称')
    type = Column("type",Integer,nullable=False, comment='问题类型 1为单选，2为多选 3为判断')
    type_name = Column("type_name", String(20), nullable=False, comment='问题类型文本，对应type字段')
    status = Column("status",Integer, default=0, comment='测试状态 0正常 -1禁用')
    create_time = Column("create_time",DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_exam_id', 'exam_id'),
    )
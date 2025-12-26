# 导入sqlalchemy框架中的相关字段
from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
# 导入公共基类
from config.database_config import myBase

class MpOptionModel(myBase):
    """
    选项表 mp_option
    """
    __tablename__ = 'mp_option'

    id = Column("id",Integer, primary_key=True, autoincrement=True, comment='选项id')
    question_id = Column("question_id", Integer, nullable=False, comment='问题id')
    content = Column("content",String(500),nullable=False, comment='选项内容')
    is_right = Column("is_right",Integer, default=0, comment='选项是否正确 0错误 1正确')
    status = Column("status",Integer, default=0, comment='状态 0正常 -1停用')
    create_time = Column("create_time",DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_question_id', 'question_id'),
    )
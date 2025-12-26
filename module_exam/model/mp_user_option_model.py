# 导入sqlalchemy框架中的相关字段
from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
# 导入公共基类
from config.database_config import myBase

class MpUserOptionModel(myBase):
    """
    用户选项表 mp_user_option
    """
    __tablename__ = 'mp_user_option'

    id = Column("id",Integer, primary_key=True, autoincrement=True, comment='用户选项id')
    user_id = Column("user_id", Integer, nullable=False, comment='用户id')
    exam_id = Column("exam_id", Integer, nullable=False, comment='测试id')
    user_exam_id = Column("user_exam_id", Integer, nullable=False, comment='用户测试id')
    option_id = Column("option_id", Integer, nullable=False, comment='选项id')
    question_id = Column("question_id", Integer, nullable=False, comment='问题id')
    is_duoxue = Column("is_duoxue", Integer, nullable=False, comment='是否多选,0为否，1为是')
    is_right = Column("is_right", Integer, nullable=False, comment='是否正确,0为否，1为是')
    create_time = Column("create_time",DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_exam_id', 'exam_id'),
        Index('index_user_exam_id', 'user_exam_id'),
    )
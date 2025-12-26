# 导入sqlalchemy框架中的相关字段
from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
# 导入公共基类
from config.database_config import myBase

class MpExamModel(myBase):
    """
    测试表 mp_exam
    """
    __tablename__ = 'mp_exam'

    id = Column("id",Integer, primary_key=True, autoincrement=True, comment='测试id')
    name = Column("name",String(50),unique=True,nullable=False, comment='测试名称')
    type = Column("type",String(20),unique=True,nullable=False, comment='测试类型')
    status = Column("status",Integer, default=0, comment='测试状态 0正常 -1停用')
    create_time = Column("create_time",DateTime, comment='创建时间', default=func.now()) # 默认为当前时间

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_name', 'name'),
    )

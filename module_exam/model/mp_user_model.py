# 导入sqlalchemy框架中的相关字段
from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
# 导入公共基类
from config.database_config import myBase

class MpUserModel(myBase):
    """
    用户表 mp_user
    """
    __tablename__ = 'mp_user'

    id = Column("id",Integer, primary_key=True, autoincrement=True, comment='用户id')
    name = Column("name",String(500),nullable=False, comment='用户名')
    password = Column("password",String(500),nullable=False, comment='用户密码')
    phone = Column("phone", String(20), unique=True, nullable=False, comment='用户手机号')
    wx_openid = Column("wx_openid", String(500), unique=True, nullable=False, comment='用户微信openid')
    wx_unionid = Column("wx_unionid", String(500), unique=True, nullable=False, comment='用户微信unionid')
    head_url = Column("head_url", String(500), nullable=False, comment='用户头像url')
    age = Column("age", Integer, nullable=False, comment='用户年龄')
    address = Column("address", String(500), nullable=False, comment='用户地址')
    gender = Column("gender", Integer, nullable=False, comment='用户性别,0为暂无 1为男，2为女')
    email = Column("email", String(500), nullable=False, comment='用户邮箱')
    login_count = Column("login_count", Integer, nullable=False, comment='登录次数')
    last_login_time = Column("last_login_time", DateTime, comment='最后登录时间')
    is_admin = Column("is_admin", Integer, nullable=False, comment='是否管理员,0为否，1为是')
    create_time = Column("create_time",DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_phone', 'phone'),
    )
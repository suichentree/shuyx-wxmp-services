# 导入sqlalchemy框架中的相关字段
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, func, Index
from sqlalchemy.orm import MappedColumn, Mapped

# 导入公共基类
from base.base_model import myBaseModel

class MpUserModel(myBaseModel):
    """
    用户表 mp_user
    """
    __tablename__ = 'mp_user'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='用户id')
    name: Mapped[str] = MappedColumn(String(500), nullable=False, comment='用户名')
    nick_name: Mapped[str] = MappedColumn(String(500), nullable=False, comment='用户昵称')
    password: Mapped[str] = MappedColumn(String(500), nullable=False, comment='用户密码')
    phone: Mapped[str] = MappedColumn(String(20), unique=True, nullable=False, comment='用户手机号')
    wx_openid: Mapped[str] = MappedColumn(String(500), unique=True, nullable=False, comment='用户微信openid')
    wx_unionid: Mapped[str] = MappedColumn(String(500), unique=True, nullable=False, comment='用户微信unionid')
    head_url: Mapped[str] = MappedColumn(String(500), nullable=False, comment='用户头像url')
    age: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户年龄')
    address: Mapped[str] = MappedColumn(String(500), nullable=False, comment='用户地址')
    gender: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户性别,0为暂无 1为男，2为女')
    email: Mapped[str] = MappedColumn(String(500), nullable=False, comment='用户邮箱')
    login_count: Mapped[int] = MappedColumn(Integer, nullable=False, comment='登录次数')
    last_login_time: Mapped[datetime] = MappedColumn(DateTime, comment='最后登录时间')
    is_admin: Mapped[int] = MappedColumn(Integer, nullable=False, comment='是否管理员,0为否，1为是')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_phone', 'phone'),
    )
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional

# 定义用户模型类型
# 注意：DTO 是数据传输对象，用于在不同层之间传递数据，而不是直接与数据库交互。
class MpUserDTO(BaseModel):

    id:Optional[int] = None          # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    name:Optional[str] = None
    password:Optional[str] = None
    phone:Optional[str] = None
    wx_openid:Optional[str] = None
    wx_unionid:Optional[str] = None
    head_url:Optional[str] = None
    age:Optional[int] = None
    address:Optional[str] = None
    gender:Optional[int] = None
    email:Optional[str] = None
    login_count:Optional[int] = None
    is_admin: Optional[int] = None
    last_login_time:Optional[datetime] = None
    create_time:Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


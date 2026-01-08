from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional, List

from module_exam.dto.mp_option_dto import MpOptionDTO

# 定义用户模型类型
# 注意：DTO 是数据传输对象，用于在不同层之间传递数据，而不是直接与数据库交互。
# 不同的DTO类，用于不同的场景，有的场景需要返回所有字段，有的场景只需要返回部分字段
class MpQuestionDTO(BaseModel):
    id:Optional[int] = None          # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    exam_id:Optional[int] = None
    name:Optional[str] = None
    type:Optional[int] = None
    type_name:Optional[str] = None
    status:Optional[int] = None
    create_time:Optional[datetime] = None

    # 将sqlalchemy模型转换为pydantic模型的配置
    model_config = ConfigDict(from_attributes=True)


# 定义问题-选项模型类型
class MpQuestionOptionDTO(BaseModel):
    question: MpQuestionDTO
    options: Optional[List[MpOptionDTO]] = None  # 一个问题对应多个选项，默认空列表

    # 将sqlalchemy模型转换为pydantic模型的配置
    model_config = ConfigDict(from_attributes=True)





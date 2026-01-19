from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Json
from typing import Optional, List


# 定义用户问题艾宾浩斯轨迹表 DTO
# 注意：DTO 是数据传输对象，用于在不同层之间传递数据，而不是直接与数据库交互。
# 不同的DTO类，用于不同的场景，有的场景需要返回所有字段，有的场景只需要返回部分字段
class MpUserQuestionEbbinghausTrackDTO(BaseModel):
    id:Optional[int] = None          # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    user_id:Optional[int] = None
    question_id:Optional[int] = None
    question_type:Optional[int] = None
    correct_count: Optional[int] = None  # 做对次数
    error_count: Optional[int] = None  # 做错次数
    total_count: Optional[int] = None  # 总做题次数
    last_answer_time: Optional[date] = None  # 最后一次答题时间
    next_review_time: Optional[date] = None  # 下一次复习的时间
    status: Optional[int] = None  # 当前题目做题状态：待复习0 已巩固1
    cycle_index: Optional[int] = None  # 艾宾浩斯记忆周期索引，初始索引为0，记忆周期是[1,3,7,14,30]。-1表示已巩固
    create_time:Optional[datetime] = None
    update_time:Optional[datetime] = None

    # 将sqlalchemy模型转换为pydantic模型的配置
    model_config = ConfigDict(from_attributes=True)



# config/database_config.py（2.x版基类定义）
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
from sqlalchemy import inspect
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# 2.x中 自定义数据库工具类，添加to_dict方法
class myBaseModelUtil:
    """适配SQLAlchemy 2.x的自定义基类，带to_dict方法"""

    def to_dict(
            self,
            exclude_fields: Optional[List[str]] = None,
            include_relationships: bool = False,
            _depth: int = 3  # 防循环引用的递归深度限制
    ) -> Dict[str, Any]:
        """
        2.x版模型实例转dict
        :param exclude_fields: 排除字段列表，如['password', 'create_time']
        :param include_relationships: 是否包含关联字段（默认不包含）
        :param _depth: 递归深度限制（内部参数，外部无需传），防循环引用
        """
        if _depth <= 0:
            return {"_hint": "recursion depth limit exceeded"}

        exclude = exclude_fields or []
        inspector = inspect(self)
        result: Dict[str, Any] = {}

        # 1. 处理表列字段（核心）
        for attr in inspector.mapper.column_attrs:
            attr_key = attr.key
            if attr_key in exclude:
                continue
            value = getattr(self, attr_key, None)
            # 区分date和datetime的格式化
            if isinstance(value, datetime):
                result[attr_key] = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, date):
                result[attr_key] = value.strftime("%Y-%m-%d")
            else:
                result[attr_key] = value

        # 2. 可选：处理关联字段（2.x中relationship属性通过mapper.relationships获取）
        if include_relationships and _depth > 0:
            for rel in inspector.mapper.relationships:
                rel_key = rel.key
                if rel_key in exclude:
                    continue
                rel_value = getattr(self, rel_key, None)

                # 关联字段为None/空，直接赋值
                if rel_value is None:
                    result[rel_key] = None
                    continue

                # 处理关联列表（一对多/多对多）
                if isinstance(rel_value, list):
                    result[rel_key] = [
                        item.to_dict(
                            exclude_fields=exclude,
                            include_relationships=include_relationships,
                            _depth=_depth - 1
                        )
                        for item in rel_value if hasattr(item, "to_dict")
                    ]
                # 处理关联对象（一对一/多对一）
                elif hasattr(rel_value, "to_dict"):
                    result[rel_key] = rel_value.to_dict(
                        exclude_fields=exclude,
                        include_relationships=include_relationships,
                        _depth=_depth - 1
                    )
                # 无to_dict方法的关联对象，返回主键/提示
                else:
                    result[rel_key] = f"Unsupported type: {type(rel_value)}"

        return result


# 创建统一数据库模型基类
class myBaseModel(DeclarativeBase, myBaseModelUtil):
    pass
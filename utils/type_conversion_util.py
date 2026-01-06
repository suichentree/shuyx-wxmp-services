from typing import Any, Type, List, Optional, Union, Dict, TypeVar, cast
from pydantic import BaseModel, ValidationError, TypeAdapter
from pydantic_core import PydanticUndefined
from fastapi import HTTPException, status
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase  # SQLAlchemy 2.0 基类
from datetime import datetime

# 类型变量：限定SQLAlchemy模型类和Pydantic DTO类
ModelType = TypeVar("ModelType", bound=DeclarativeBase)  # 绑定到SQLAlchemy基类
DtoType = TypeVar("DtoType", bound=BaseModel)  # 绑定到Pydantic基类


class TypeConversionUtil:
    """
    将sqlalchemy模型实例转换为字典，仅包含表映射字段，排除内部属性
    :param source_data: SQLAlchemy模型实例或实例列表
    :param exclude_fields: 要排除的字段列表（可选）
    :return: 包含表映射字段的字典（单实例/列表）

    基于inspect的原生转换：仅获取表映射字段，排除内部属性
    """
    @staticmethod
    def sqlalchemy_to_dict(data:Union[ModelType, List[ModelType]], exclude_fields: list = None) -> Union[dict, List[dict]]:
        try:
            # 处理排除字段（默认空列表）
            exclude_fields = exclude_fields or []

            # 类型判断
            if isinstance(data, list):
                # 列表场景
                result_list = []
                for item in data:
                    # 反射ORM实例，获取元数据
                    insp = inspect(item)
                    item_dict = {}
                    # 遍历所有表字段（仅包含模型中定义的Column字段）
                    for attr in insp.mapper.column_attrs:
                        key = attr.key
                        # 跳过排除字段
                        if key in exclude_fields:
                            continue
                        value = getattr(item, key)
                        # 处理日期时间类型转换
                        if isinstance(value, datetime):
                            item_dict[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            item_dict[key] = value
                    result_list.append(item_dict)
                return result_list

            else:
                # 单实例场景

                # 反射ORM实例，获取元数据
                insp = inspect(data)
                # 遍历所有表字段（仅包含模型中定义的Column字段）
                result = {}
                for attr in insp.mapper.column_attrs:
                    key = attr.key
                    # 跳过排除字段
                    if key in exclude_fields:
                        continue
                    value = getattr(data, key)
                    # 处理日期时间类型转换
                    if isinstance(value, datetime):
                        result[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        result[key] = value

                return result

        except Exception as e:
            # 数据转换失败：抛出明确异常
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"数据转换失败：{str(e)}")


    """
    SQLAlchemy模型（单实例/列表）转换为Pydantic模型（单实例/列表）
    :param data: SQLAlchemy模型实例或实例列表（必须是model_cls的实例）
    :param model_cls: SQLAlchemy模型类（用于类型校验）
    :param dto_cls: 目标Pydantic模型类（用于类型校验,需配置from_attributes=True）
    :return: Pydantic模型实例或实例列表
    """
    @staticmethod
    def sqlalchemy_to_pydantic(data:Union[ModelType, List[ModelType]],model_cls: Type[ModelType],dto_cls: Type[DtoType]) -> Union[DtoType, List[DtoType]]:
        # 校验输入data是否匹配model_cls类型
        if isinstance(data, list):
            if not all(isinstance(item, model_cls) for item in data):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"列表中包含非{model_cls.__name__}类型的实例")
        elif not isinstance(data, model_cls):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"类型必须是{model_cls.__name__}，实际为{type(data).__name__}")

        # 校验Pydantic模型类是否开启ORM适配（必选配置）
        if not getattr(dto_cls.model_config, "from_attributes", False):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Pydantic模型类 {dto_cls.__name__} 未配置 from_attributes=True，无法解析SQLAlchemy模型")

        try:
            # 处理列表场景
            if isinstance(data, list):
                # 开始转换
                validated_list = TypeAdapter(List[dto_cls]).validate_python(data)
                # 类型断言
                validated_list = cast(List[DtoType], validated_list)  # 类型断言
                # 返回转换后的列表
                return validated_list

            # 处理单实例场景
            else:
                # 开始转换
                validated_obj = dto_cls.model_validate(data)
                # 类型断言
                validated_obj = cast(DtoType, validated_obj)
                # 返回转换后的单实例
                return validated_obj

        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"SQLAlchemy转Pydantic校验失败（{model_cls.__name__}→{dto_cls.__name__}）：{e.errors()}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"SQLAlchemy转Pydantic异常（{model_cls.__name__}→{dto_cls.__name__}）：{str(e)}")


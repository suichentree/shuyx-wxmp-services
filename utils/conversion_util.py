from datetime import datetime, date

from fastapi import HTTPException
from pydantic import BaseModel,TypeAdapter
from typing import List, Type, TypeVar, Union, cast
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from starlette import status

from module_exam.dto.mp_user_dto import MpUserDTO
from module_exam.model.mp_user_model import MpUserModel

# 类型变量：限定SQLAlchemy模型类和Pydantic DTO类
ModelType = TypeVar("ModelType", bound=DeclarativeBase)  # 绑定到SQLAlchemy基类
DtoType = TypeVar("DtoType", bound=BaseModel)  # 绑定到Pydantic基类


"""
    将sqlalchemy模型实例转换为字典，仅包含表映射字段，排除内部属性
        :param model_instance: SQLAlchemy模型实例或实例列表
        :param exclude_fields: 要排除的字段列表（可选） 例如 ['password', 'create_time']
        :return: 包含表映射字段的字典（单实例/列表）

    基于inspect的原生转换：仅获取表映射字段，排除内部属性
"""
def model_to_dict(model_instance: Union[ModelType, List[ModelType]], exclude_fields: list = None) -> Union[dict, List[dict]]:
    try:
        # 处理排除字段（默认空列表）
        exclude_fields = exclude_fields or []

        # 如果是列表，递归处理每个实例
        if isinstance(model_instance, list):
            # 列表场景
            result_list = []
            # 遍历列表中的每个模型实例
            for item in model_instance:
                # 2.x中inspect方法反射model实例，获取元数据
                inspector = inspect(item)
                item_dict = {}
                # 遍历所有表字段（仅包含模型中定义的Column字段）
                for attr in inspector.mapper.column_attrs:
                    # 提取字段
                    key = attr.key
                    # 跳过排除字段
                    if key in exclude_fields:
                        continue
                    # 提取字段值
                    value = getattr(model_instance, key)
                    # 日期类型序列化（可选，转为字符串）
                    if isinstance(value, (date, datetime)):
                        item_dict[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        item_dict[key] = value

                result_list.append(item_dict)
            return result_list

        else:
            # 单实例场景 适配SQLAlchemy 2.x的通用转换函数

            # 2.x中inspect方法反射model实例，获取元数据
            inspector = inspect(model_instance)
            # 遍历所有表字段（仅包含模型中定义的Column字段）
            result = {}
            for attr in inspector.mapper.column_attrs:
                # 提取字段
                key = attr.key
                # 跳过排除字段
                if key in exclude_fields:
                    continue
                # 提取字段值
                value = getattr(model_instance, key)
                # 日期类型序列化（可选，转为字符串）
                if isinstance(value, (date, datetime)):
                    result[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    result[key] = value

            return result


    except Exception as e:
        # 数据转换失败：抛出明确异常
        raise HTTPException(status_code=400, detail=f"model_to_dict 数据转换失败：{str(e)}")




"""
SQLAlchemy模型（单实例/列表）转换为Pydantic模型（单实例/列表），并支持是否序列化为字典数据
    :param data: SQLAlchemy模型实例或实例列表（必须是model_cls的实例）
    :param model_cls: SQLAlchemy模型类（用于类型校验）
    :param dto_cls: 目标Pydantic模型类（用于类型校验,需配置from_attributes=True）
    :param is_serialize: 是否将Pydantic模型实例序列化为字典数据（默认False）
    :return: Pydantic模型实例或实例列表
"""
def model_to_dto(data: Union[ModelType, List[ModelType]], model_cls: Type[ModelType], dto_cls: Type[DtoType], is_serialize: bool = False) -> Union[DtoType, List[DtoType]]:
    # 校验输入data是否匹配model_cls类型
    if isinstance(data, list):
        if not all(isinstance(item, model_cls) for item in data):
            raise HTTPException(status_code=400, detail=f"列表中包含非{model_cls.__name__}类型的实例")
    elif not isinstance(data, model_cls):
        raise HTTPException(status_code=400, detail=f"类型必须是{model_cls.__name__}，实际为{type(data).__name__}")

    try:
        # 处理列表场景
        if isinstance(data, list):
            # 开始转换
            validated_list = TypeAdapter(List[dto_cls]).validate_python(data)
            # 类型断言
            validated_list = cast(List[DtoType], validated_list)  # 类型断言

            # 是否序列化为字典数据
            if is_serialize:
                # 序列化时，将Pydantic模型实例转换为字典
                validated_list = [item.model_dump() for item in validated_list]

            # 返回转换后的列表
            return validated_list

        # 处理单实例场景
        else:
            # 开始转换
            validated_obj = dto_cls.model_validate(data)
            # 类型断言
            validated_obj = cast(DtoType, validated_obj)

            # 是否序列化为字典数据
            if is_serialize:
                # 序列化时，将Pydantic模型实例转换为字典
                validated_obj = validated_obj.model_dump()

            # 返回转换后的单实例
            return validated_obj

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"model_to_dto 转换失败（{model_cls.__name__}→{dto_cls.__name__}）：{str(e)}")


if __name__ == "__main__":
    # 测试：将SQLAlchemy模型实例转换为Pydantic模型实例（单实例场景）
     user = MpUserModel(id=1, name="test", create_time=datetime.now())
     user_dict = model_to_dict(user)
     print(user_dict)

    # 测试：将SQLAlchemy模型实例转换为Pydantic模型实例（单实例场景），并序列化为字典数据
     user_dict = model_to_dto(user,MpUserModel,MpUserDTO, is_serialize=False)
     print(type(user_dict))
     print(user_dict)
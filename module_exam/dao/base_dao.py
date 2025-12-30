from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import update, delete, desc, asc
from config.database_config import myBase

# 定义泛型类型变量，约束为SQLAlchemy的Base模型
ModelType = TypeVar("ModelType", bound=myBase)

class BaseDao(Generic[ModelType]):
    """通用DAO基类，封装所有表的通用CRUD方法"""
    def __init__(self, model: Type[ModelType]):
        """
        初始化BaseDAO
        :param model: 关联的SQLAlchemy数据库模型（如User、Order）
        """
        self.model = model

    def get_by_id(self, db_session: Session, id: int) -> Optional[ModelType]:
        """
        根据ID获取单条记录（注意包含字段id）
            id: 记录ID
        """
        return db_session.query(self.model).filter(self.model.id == id).first()

    def get_total_by_filters(self,db_session: Session,filters: Dict = None) -> int:
        """
        根据条件获取记录总数
            filters: 查询条件,字典类型。例如 {"filed1": value1, "filed2": value2}
        """
        # 初始化查询对象
        query = db_session.query(self.model)
        # 动态构建查询条件
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)

        return query.count()

    def get_one_by_filter(self, db_session: Session, filters: Dict = None) -> Optional[ModelType]:
        """
        根据条件获取单条记录
            filters: 查询条件，字典类型。例如 {"filed1": value1, "filed2": value2}
        """
        # 初始化查询对象
        query = db_session.query(self.model)
        # 动态构建查询条件
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)

        return query.first()

    def get_list_by_filters(self,db_session: Session,filters: Dict = None,sort_by: List[str] = None) -> List[ModelType]:
        """
        根据条件获取查询列表（支持条件过滤+排序）
            filters: 查询条件字典。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序。
        """
        # 初始化查询对象
        query = db_session.query(self.model)
        # 动态构建查询条件
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)
        # 动态构建排序条件
        if sort_by:
            # 遍历排序字段列表
            for sort_field in sort_by:
                # 判断排序方向
                if sort_field.startswith('-'):
                    # 降序
                    field_name = sort_field[1:]
                    if hasattr(self.model, field_name):
                        query = query.order_by(desc(getattr(self.model, field_name)))
                else:
                    # 升序
                    if hasattr(self.model, sort_field):
                        query = query.order_by(asc(getattr(self.model, sort_field)))

        # 执行查询并获取所有记录
        return query.all()

    def get_page_list_by_filters(self,db_session: Session,page_num: int,page_size: int,filters: Dict = None,sort_by: List[str] = None) -> List[ModelType]:
        """
        根据条件获取分页查询列表（支持分页+条件过滤+排序）
            page_num: 页码
            page_size: 每页大小
            filters: 查询条件字典。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序。
        """
        # 初始化查询对象
        query = db_session.query(self.model)
        # 动态构建查询条件
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)
        # 动态构建排序条件
        if sort_by:
            # 遍历排序字段列表
            for sort_field in sort_by:
                # 判断排序方向
                if sort_field.startswith('-'):
                    # 降序
                    field_name = sort_field[1:]
                    if hasattr(self.model, field_name):
                        query = query.order_by(desc(getattr(self.model, field_name)))
                else:
                    # 升序
                    if hasattr(self.model, sort_field):
                        query = query.order_by(asc(getattr(self.model, sort_field)))

        # 计算分页偏移量
        offset_value = (page_num - 1) * page_size
        # 获取当前分页数据
        return query.offset(offset_value).limit(page_size).all()

    def add(self, db_session: Session, dict_data: Dict = None) -> ModelType:
        """
        添加新记录
            dict_data: 新记录的字典数据
        """
        # 将字典转换为对应的model实例
        new_instance = self.model(**dict_data)
        db_session.add(new_instance)
        # 显式提交事务
        db_session.commit()
        # 刷新实例，获取自增id,默认值等
        db_session.refresh(new_instance)
        return new_instance

    def update_by_id(self,db_session: Session,id: int,update_data: Dict = None) -> bool:
        """
        根据ID更新信息
            id: 要更新的记录ID
            update_data: 更新数据字典
        """

        # 1. 先查询记录是否存在
        db_obj = self.get_by_id(db_session, id)
        # 若不存在，则返回False
        if not db_obj:
            return False

        # 2. 遍历更新数据字典，更新model实例的字段
        for key, value in update_data.items():
            if hasattr(db_obj, key) and key != "id":  # 禁止更新id字段
                setattr(db_obj, key, value)

        # 3. 提交事务
        db_session.commit()
        return True

    def delete_by_id(self, db_session: Session, id: int) -> bool:
        """
        根据ID删除记录
            id: 要删除的记录ID
        """

        # 1. 先查询记录是否存在
        db_obj = self.get_by_id(db_session, id)
        if not db_obj:
            return False

        # 2. 删除记录
        db_session.delete(db_obj)
        db_session.commit()
        return True


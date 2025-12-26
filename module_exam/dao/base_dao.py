from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import update, delete
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

    def create(self, db_session: Session, dict_data: Dict[str, Any]) -> ModelType:
        """通用创建方法"""
        # 将字典转换为模型实例
        model_data = self.model(**dict_data)
        db_session.add(model_data)
        db_session.commit()
        db_session.refresh(model_data)
        return model_data

    def get_by_id(self, db_session: Session, id: int) -> Optional[ModelType]:
        """根据ID查询单条记录"""
        return db_session.query(self.model).filter(self.model.id == id).first()

    def get_page_list_by_filters(self,db_session: Session,page_num: int,page_size: int,filters: Dict = None) -> List[ModelType]:
        """
        通用批量查询（支持分页+条件过滤）
        :param filters: 过滤条件字典，如{"username": "test"}
        """
        query = db_session.query(self.model)

        # 动态构建查询条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)

        # 计算分页偏移量
        offset_value = (page_num - 1) * page_size
        # 获取当前分页数据
        return query.offset(offset_value).limit(page_size).all()

    def update(self,db_session: Session,id: int,obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """通用更新方法（根据ID更新）"""

        # 1. 先查询记录是否存在
        db_obj = self.get_by_id(db_session, id)
        if not db_obj:
            return None

        # 2. 批量更新字段
        for key, value in obj_in.items():
            if hasattr(db_obj, key) and key != "id":  # 禁止修改ID
                setattr(db_obj, key, value)

        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def delete(self, db_session: Session, id: int) -> bool:
        """通用删除方法（根据ID删除）"""
        db_obj = self.get_by_id(db_session, id)
        if not db_obj:
            return False

        db_session.delete(db_obj)
        db_session.commit()
        return True

    def get_by_filter(self, db_session: Session, filters: Dict = None) -> Optional[ModelType]:
        """通用条件查询（单条记录）"""
        query = db_session.query(self.model)

        # 动态构建查询条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)

        return query.first()
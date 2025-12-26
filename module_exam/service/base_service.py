from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from config.database_config import myBase
from module_exam.dao.base_dao import BaseDao

# 定义泛型类型变量，约束为SQLAlchemy的Base模型
ModelType = TypeVar("ModelType", bound=myBase)

class BaseService(Generic[ModelType]):
    """通用Service基类，封装通用业务逻辑"""
    def __init__(self, dao: BaseDao[ModelType]):
        """
        初始化BaseService
        :param dao: 关联的DAO实例（如UserDAO）
        """
        self.dao = dao

    def create(self, db_session: Session, obj_in: Dict[str, Any]) -> ModelType:
        """通用新增方法，调用DAO层新增方法"""
        return self.dao.create(db_session, obj_in)

    def get_by_id(self, db_session: Session, id: int) -> ModelType:
        """通用查询（不存在则抛404异常）"""
        db_obj = self.dao.get_by_id(db_session, id)
        if not db_obj:
            raise HTTPException(status_code=404, detail=f"{self.dao.model.__tablename__}记录不存在")
        return db_obj

    def get_page_list_by_filters(self,db_session: Session,page_num: int = 1,page_size: int = 10,filters: Optional[Dict[str, Any]] = None) -> List[ModelType]:
        """通用批量查询"""
        return self.dao.get_page_list_by_filters(db_session, page_num, page_size, filters)

    def update(self,db_session: Session,id: int,obj_in: Dict[str, Any]) -> ModelType:
        """通用更新（不存在则抛404异常）"""
        db_obj = self.dao.update(db_session, id, obj_in)
        if not db_obj:
            raise HTTPException(status_code=404, detail=f"{self.dao.model.__tablename__}记录不存在")
        return db_obj

    def delete(self, db_session: Session, id: int) -> Dict[str, str]:
        """通用删除（不存在则抛404异常）"""
        success = self.dao.delete(db_session, id)
        if not success:
            raise HTTPException(status_code=404, detail=f"{self.dao.model.__tablename__}记录不存在")
        return {"message": f"{self.dao.model.__tablename__}记录删除成功"}

    def get_by_filter(self, db_session: Session, filters: Dict[str, Any]) -> ModelType:
        """通用条件查询（不存在则抛404异常）"""
        db_obj = self.dao.get_by_filter(db_session, filters)
        if not db_obj:
            raise HTTPException(status_code=404, detail=f"{self.dao.model.__tablename__}记录不存在")
        return db_obj
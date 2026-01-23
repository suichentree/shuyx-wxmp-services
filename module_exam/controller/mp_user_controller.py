from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session
from config.log_config import logger
from module_exam.dto.mp_user_dto import MpUserDTO, MpUserCommonDTO
from module_exam.service.mp_user_service import MpUserService
from utils.response_util import ResponseUtil

# 创建路由实例
router = APIRouter(prefix='/mp/user', tags=['mp_user接口'])

# 创建服务实例
MpUserService_instance = MpUserService()

"""
重置密码
"""
@router.post("/resetPass")
def phoneLogin(phone:str = Body(None),password:str = Body(None),newpassword:str = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/user/resetPass, phone = {phone} password = {password} newpassword = {newpassword}')
    # 构造用户字典数据
    user = {
        "phone": phone,
        "password": password
    }
    # 调用服务层方法，查询用户是否存在
    result = MpUserService_instance.get_one_by_filters(filters=user)
    if result is not None:
        # 构造需要更新的数据
        newuser = {
            "password": newpassword
        }
        newresult = MpUserService_instance.update_by_id(db_session,id=result["id"],update_data=newuser)
        if newresult["success"]:
            return ResponseUtil.success(data={"isReset": 1, "message": "重置密码成功"})
        else:
            return ResponseUtil.error(data={"isReset": 0,"message": "重置密码失败1"})
    else:
        return ResponseUtil.error(data={"isReset": 0,"message": "重置密码失败2"})

"""
手机号注册接口
"""
@router.get("/phoneRegister")
def phoneRegister(phone:str,password:str,db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/user/phoneRegister, phone = {phone} password = {password}')
    # 构造用户字典数据
    user = {
        "phone": phone,
        "password": password
    }
    # 调用服务层方法，新增用户
    result = MpUserService_instance.add(db_session,dict_data=user)
    if result["success"]:
        return ResponseUtil.success(data={"isRegister": 1, "message": "注册成功"})
    else:
        return ResponseUtil.error(data={"isRegister": 0, "message": "注册失败"})

@router.post("/saveUserInfo")
def saveUserInfo(userInfo:MpUserCommonDTO,db_session:Session = Depends(get_db_session)):
        logger.info(f'/mp/user/saveUserInfo, userInfo = {userInfo}')
        # 事务提交
        with db_session.begin():
            # dto 转换为 dict
            updateuser_dict = userInfo.model_dump(exclude_unset=True)

            # 调用服务层方法，更新用户信息
            result = MpUserService_instance.update_by_id(db_session,id=userInfo.id,update_data=updateuser_dict),
            if result is False:
                return ResponseUtil.error(data={"message": "更新失败"})

            return ResponseUtil.success(data={"message": "更新成功"})

@router.post("/getUserInfo")
def getUserInfo(userId:int = Body(None,embed=True),db_session:Session = Depends(get_db_session)):
        logger.info(f'/mp/user/getUserInfo, userId = {userId}')
        # 调用服务层方法，查询用户信息
        result = MpUserService_instance.get_by_id(db_session,id=userId)
        if result is None:
            return ResponseUtil.error(data={"message": "用户不存在"})

        # 若result为空，则返回空字典。不为空则返回result
        return ResponseUtil.success(data=MpUserCommonDTO.model_validate(result))

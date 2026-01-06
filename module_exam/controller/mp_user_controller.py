from datetime import datetime

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session
from config.log_config import logger
from module_exam.dto.mp_user_dto import MpUserDTO
from module_exam.model.mp_user_model import MpUserModel
from module_exam.service.mp_user_service import MpUserService
from module_exam.controller.wx_controller import get_wx_openid_by_code
from utils.response_util import ResponseUtil
from utils.jwt_util import JWTUtil

# 创建路由实例
router = APIRouter(prefix='/mp/user', tags=['mp_user接口'])

# 创建服务实例
MpUserService_instance = MpUserService()

"""
微信登录接口
1.传入code，得到微信用户的openId
2.注册或登录用户
"""
@router.post("/wxUserLogin")
def wxUserLogin(code:str = Body(None,embed=True),db_session: Session = Depends(get_db_session)):
        logger.info(f'/mp/user/wxUserLogin, code = {code}')
        # 根据code获取openId
        wxinfo = get_wx_openid_by_code(code)
        if wxinfo is not None:
            openId = wxinfo.get("openid")
            unionId = wxinfo.get("unionid")
        else:
            return ResponseUtil.error(data={"message": "无法获取用户openId,unionId"})

        # 根据openid 查询用户是否存在
        user = MpUserService_instance.get_one_by_filters(db_session,filters=MpUserDTO(wx_openid=openId).model_dump())

        if user is None:
            # 查询不出用户，则注册用户
            newuser = MpUserDTO(
                wx_openid=openId,
                wx_unionid=unionId,
                head_url=None,
                name=None,
                gender=None,
                login_count=1,
                last_login_time= datetime.now()
            )
            # 调用服务层方法，新增用户
            new_user = MpUserService_instance.add(db_session,dict_data=newuser.model_dump())
            if new_user is None:
                return ResponseUtil.error(data={"message": "微信注册用户失败"})

            # 获取user id
            userId = new_user.id
            # 创建token,传入openId,userId生成token
            token = JWTUtil.create_token({"open_id": openId, "user_id": userId})
            # 返回响应数据
            return ResponseUtil.success(data={"isFirstLogin": 1,"token": token,"userInfo":new_user})

        else:
            # 查询到用户，则登录用户
            user.login_count += 1
            user.last_login_time = datetime.now()
            # 调用服务层方法，更新用户
            result = MpUserService_instance.update_by_id(id=user.id,update_data=user)
            if result is False:
                return ResponseUtil.error(data={"message": "微信登录用户失败"})

            # 获取user的id
            userId = user.id
            # 创建token,传入openId,userId生成token
            token = JWTUtil.create_token({"openId": openId,"userId":userId})
            # 返回响应数据
            return ResponseUtil.success(data={"isFirstLogin": 0,"token":token,"userInfo":user})

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

"""
电话登录接口
"""
@router.post("/phoneLogin")
def phoneLogin(phone:str = Body(None),password:str = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/user/phoneLogin, phone = {phone} password = {password}')
    # 构造用户字典数据
    user = {
        "phone": phone,
        "password": password
    }
    # 调用服务层方法，新增用户
    result = MpUserService_instance.get_one_by_filters(db_session,filters=user)
    print(result)
    if result is None:
        return ResponseUtil.error(data={"userId": 0, "isLogin": 0, "message": "电话登录失败"})

    return ResponseUtil.success(data={"userId": result["id"], "isLogin": 1, "message": "电话登录成功"})

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



@router.post("/saveUserInfo")
def saveUserInfo(userInfo:MpUserDTO,db_session:Session = Depends(get_db_session)):
        logger.info(f'/mp/user/saveUserInfo, userInfo = {userInfo}')

        # dto 转换为 dict
        updateuser_dict = userInfo.model_dump(exclude_unset=True)

        # 调用服务层方法，更新用户信息
        result = MpUserService_instance.update_by_id(db_session,id=userInfo.id,update_data=updateuser_dict),
        if result is False:
            return ResponseUtil.error(data={"message": "更新失败"})

        return ResponseUtil.success(data={"message": "更新成功"})

@router.post("/getUserInfo")
def getUserInfo(userId:int = Body(None),db_session:Session = Depends(get_db_session)):
        logger.info(f'/mp/user/getUserInfo, userId = {userId}')
        # 调用服务层方法，查询用户信息
        result = MpUserService_instance.get_one_by_filters(db_session,filters={"id": userId})
        # 若result为空，则返回空字典。不为空则返回result
        return ResponseUtil.success(data=result)

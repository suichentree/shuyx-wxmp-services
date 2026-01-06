from fastapi import APIRouter, Body
from config.log_config import logger
from utils.response_util import ResponseUtil
import requests
import json

# 创建路由实例
router = APIRouter(prefix='/mp/wxservice', tags=['mp_wxservice接口'])

# 微信小程序应用ID和应用密钥
APP_ID:str = "wxf9788c249032b959"
APP_SECRET:str = "c69674e1cb73d754ef9cab64f3553867"


def get_wx_openid_by_code(code:str):
    """
    调用微信小程序登录接口,通过微信小程序登录凭证（code）获取微信用户OpenID
    """
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={APP_ID}&secret={APP_SECRET}&js_code={code}&grant_type=authorization_code"
    # 发送GET请求，调用接口
    response = requests.get(url)
    # 获取响应结果
    response_info = json.loads(response.text)
    return response_info

@router.post("/getOpenIdByWxCode")
# 单个参数的时候，需要使用Body(None,embed=True)来指定参数从请求体中获取。多个参数的时候，不需要指定embed=True
async def getOpenIdByWxCode(code:str = Body(None,embed=True)):
    """
    调用微信小程序登录接口,通过微信小程序登录凭证（code）获取微信用户OpenID
    """
    logger.info(f"/mp/wxservice/getOpenIdByWxCode , code = {code}")
    if not code:
        return ResponseUtil.error(message="微信小程序登录凭证（code）不能为空")

    # 获取openid
    response_info = get_wx_openid_by_code(code)
    return ResponseUtil.success(data=response_info)

@router.get("/getAccessToken")
async def getAccessToken():
    """
    调用微信小程序登录接口,获取访问令牌（access_token）
    """
    logger.info(f"调用微信小程序登录接口,获取访问令牌（access_token） /mp/wxservice/getAccessToken")
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    # 发送GET请求，调用接口
    response = requests.get(url)
    # 获取响应结果
    response_info = json.loads(response.text)
    return ResponseUtil.success(data=response_info)
from fastapi import APIRouter, Body, HTTPException
from config.log_config import logger
from utils.response_util import ResponseUtil
import requests
import json
import hashlib
import random
import string
from datetime import datetime

# 创建路由实例
router = APIRouter(prefix='/mp/wxservice', tags=['mp_wxservice接口'])

# 微信小程序应用ID和应用密钥
APP_ID: str = "wxf9788c249032b959"
APP_SECRET: str = "c69674e1cb73d754ef9cab64f3553867"
# 微信支付商户号
MCH_ID: str = "your_mch_id"
# 微信支付API密钥
API_KEY: str = "your_api_key"

def generate_sign(params: dict, key: str):
    """生成微信支付签名"""
    # 按参数名ASCII码从小到大排序
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    # 拼接字符串
    stringA = '&'.join([f"{k}={v}" for k, v in sorted_params if v])
    # 拼接API密钥
    stringSignTemp = f"{stringA}&key={key}"
    # MD5加密并转大写
    sign = hashlib.md5(stringSignTemp.encode('utf-8')).hexdigest().upper()
    return sign


# 模拟微信支付订单方法
@router.post("/mock/createWechatPayment")
async def mock_create_wechat_payment(
        openid: str = Body(...),
        order_no: str = Body(...),
        total_fee: int = Body(...),  # 单位为分
        description: str = Body(...),
):
    """
    创建微信支付订单 - 模拟测试版本
    """
    logger.info(f"创建微信支付订单(模拟): order_no={order_no}, total_fee={total_fee}, openid={openid}")

    try:
        # 模拟支付参数生成
        mock_prepay_id = f"mock_prepay_id_{order_no}_{int(datetime.now().timestamp())}"

        # 生成32随机字符串
        random_str = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

        # 返回给小程序的支付参数
        pay_sign_params = {
            'appId': APP_ID,
            'timeStamp': str(int(datetime.now().timestamp())),
            'nonceStr': random_str,
            'package': f'prepay_id={mock_prepay_id}',
            'signType': 'MD5'
        }

        # 生成模拟支付签名
        pay_sign = generate_sign(pay_sign_params, API_KEY)

        # 模拟响应数据
        mock_response = {
            'pay_params': pay_sign_params,
            'paySign': pay_sign,
            'mock_info': '这是模拟支付数据，仅用于测试',
            'order_no': order_no,
            'total_fee': total_fee,
            'description': description,
            'openid': openid,
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"模拟支付订单创建成功: {order_no}")
        return ResponseUtil.success(data=mock_response)

    except Exception as e:
        logger.error(f"模拟创建微信支付订单失败: {str(e)}")
        return ResponseUtil.error(message="模拟创建支付订单失败")

@router.post("/createWechatPayment")
async def create_wechat_payment(
        openid: str = Body(...),
        order_no: str = Body(...),
        total_fee: int = Body(...),  # 单位为分
        description: str = Body(...),
):
    """
    创建微信支付订单
    """
    logger.info(f"创建微信支付订单: order_no={order_no}, total_fee={total_fee}, openid={openid}")

    try:
        # 获取access_token
        access_token_response = getAccessToken()
        if access_token_response.get('code') != 200:
            return ResponseUtil.error(message="获取access_token失败")

        access_token = access_token_response['data']['access_token']

        # 生成32随机字符串
        random_str = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

        # 构造支付参数
        pay_params = {
            'appid': APP_ID,
            'mch_id': MCH_ID,
            'nonce_str': random_str,
            'body': description,
            'out_trade_no': order_no,
            'total_fee': total_fee,  # 单位为分
            'spbill_create_ip': '127.0.0.1',  # 用户IP
            'notify_url': 'https://your-domain.com/mp/wxservice/paymentNotify',
            'trade_type': 'JSAPI',
            'openid': openid
        }

        # 生成签名
        sign = generate_sign(pay_params, API_KEY)
        pay_params['sign'] = sign

        # 调用微信支付统一下单接口
        unified_order_url = "https://api.mch.weixin.qq.com/pay/unifiedorder"

        # 构造XML请求数据
        xml_data = f"""
        <xml>
            <appid><![CDATA[{pay_params['appid']}]]></appid>
            <mch_id><![CDATA[{pay_params['mch_id']}]]></mch_id>
            <nonce_str><![CDATA[{pay_params['nonce_str']}]]></nonce_str>
            <sign><![CDATA[{pay_params['sign']}]]></sign>
            <body><![CDATA[{pay_params['body']}]]></body>
            <out_trade_no><![CDATA[{pay_params['out_trade_no']}]]></out_trade_no>
            <total_fee>{pay_params['total_fee']}</total_fee>
            <spbill_create_ip><![CDATA[{pay_params['spbill_create_ip']}]]></spbill_create_ip>
            <notify_url><![CDATA[{pay_params['notify_url']}]]></notify_url>
            <trade_type><![CDATA[{pay_params['trade_type']}]]></trade_type>
            <openid><![CDATA[{pay_params['openid']}]]></openid>
        </xml>
        """

        headers = {'Content-Type': 'application/xml'}
        response = requests.post(unified_order_url, data=xml_data.encode('utf-8'), headers=headers)

        # 这里需要解析XML响应，简化处理
        if response.status_code == 200:
            # 解析响应获取prepay_id
            # 实际项目中需要使用XML解析库
            response_text = response.text
            if 'prepay_id' in response_text:
                # 提取prepay_id
                prepay_id = response_text.split('<prepay_id><![CDATA[')[1].split(']]></prepay_id>')[0]

                # 生成32随机字符串
                random_str = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

                # 返回给小程序的支付参数
                pay_sign_params = {
                    'appId': APP_ID,
                    'timeStamp': str(int(datetime.now().timestamp())),
                    'nonceStr': random_str,
                    'package': f'prepay_id={prepay_id}',
                    'signType': 'MD5'
                }

                # 生成支付签名
                pay_sign = generate_sign(pay_sign_params, API_KEY)

                return ResponseUtil.success(data={
                    'pay_params': pay_sign_params,
                    'paySign': pay_sign
                })
            else:
                return ResponseUtil.error(message="微信支付下单失败")
        else:
            return ResponseUtil.error(message="微信支付接口调用失败")

    except Exception as e:
        logger.error(f"创建微信支付订单失败: {str(e)}")
        return ResponseUtil.error(message="创建支付订单失败")


# 修改支付回调通知方法
@router.post("/mock/paymentNotify")
async def mock_payment_notify(notification: dict = Body(...)):
    """
    微信支付回调通知 - 模拟测试版本
    """
    logger.info(f"微信支付回调通知(模拟): {notification}")

    try:
        # 模拟支付结果处理
        mock_order_no = notification.get('out_trade_no', f"MOCK_ORDER_{int(datetime.now().timestamp())}")
        mock_transaction_id = f"MOCK_TRANS_{int(datetime.now().timestamp())}"

        # 模拟成功响应
        mock_response = {
            'result_code': 'SUCCESS',
            'return_code': 'SUCCESS',
            'order_no': mock_order_no,
            'transaction_id': mock_transaction_id,
            'payment_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mock_info': '这是模拟支付回调，仅用于测试'
        }

        logger.info(f"模拟支付回调处理成功: order_no={mock_order_no}")

        # 返回XML格式的成功响应
        return f"""<xml>
            <return_code><![CDATA[SUCCESS]]></return_code>
            <return_msg><![CDATA[OK]]></return_msg>
            <mock_order_no><![CDATA[{mock_order_no}]]></mock_order_no>
            <mock_transaction_id><![CDATA[{mock_transaction_id}]]></mock_transaction_id>
            <mock_info><![CDATA[这是模拟支付回调响应]]></mock_info>
        </xml>"""

    except Exception as e:
        logger.error(f"模拟支付通知处理失败: {str(e)}")
        return """<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[模拟处理失败]]></return_msg></xml>"""

@router.post("/paymentNotify")
async def payment_notify(notification: dict = Body(...)):
    """
    微信支付回调通知
    """
    logger.info(f"微信支付回调通知: {notification}")

    try:
        # 这里需要验证通知的签名
        # 解析XML格式的通知数据

        # 验证支付结果
        if notification.get('result_code') == 'SUCCESS':
            order_no = notification.get('out_trade_no')
            transaction_id = notification.get('transaction_id')

            # 更新订单状态
            # 这里需要调用订单服务更新订单状态
            logger.info(f"支付成功: order_no={order_no}, transaction_id={transaction_id}")

            return """<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"""
        else:
            logger.error(f"支付失败: {notification}")
            return """<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[支付失败]]></return_msg></xml>"""

    except Exception as e:
        logger.error(f"支付通知处理失败: {str(e)}")
        return """<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[处理失败]]></return_msg></xml>"""


# 修改查询支付状态方法
@router.post("/mock/queryPaymentStatus")
async def mock_query_payment_status(order_no: str = Body(...)):
    """
    查询支付状态 - 模拟测试版本
    """
    logger.info(f"查询支付状态(模拟): order_no={order_no}")

    try:
        # 模拟不同的支付状态
        import random
        mock_statuses = ["SUCCESS", "NOTPAY", "PROCESSING"]
        mock_status = random.choice(mock_statuses)

        # 模拟查询响应数据
        mock_response = {
            'order_no': order_no,
            'payment_status': mock_status,
            'transaction_id': f"MOCK_TRANS_{order_no}_{int(datetime.now().timestamp())}",
            'payment_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if mock_status == "SUCCESS" else None,
            'mock_info': '这是模拟支付状态查询，仅用于测试',
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"模拟支付状态查询成功: order_no={order_no}, status={mock_status}")
        return ResponseUtil.success(data=mock_response)

    except Exception as e:
        logger.error(f"模拟查询支付状态失败: {str(e)}")
        return ResponseUtil.error(message="模拟查询支付状态失败")

@router.post("/queryPaymentStatus")
async def query_payment_status(order_no: str = Body(...)):
    """
    查询支付状态
    """
    logger.info(f"查询支付状态: order_no={order_no}")

    # 生成32随机字符串
    random_str = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

    try:
        # 构造查询参数
        query_params = {
            'appid': APP_ID,
            'mch_id': MCH_ID,
            'out_trade_no': order_no,
            'nonce_str': random_str
        }

        # 生成签名
        sign = generate_sign(query_params, API_KEY)
        query_params['sign'] = sign

        # 调用查询接口
        query_url = "https://api.mch.weixin.qq.com/pay/orderquery"

        # 构造XML请求数据
        xml_data = f"""
        <xml>
            <appid><![CDATA[{query_params['appid']}]]></appid>
            <mch_id><![CDATA[{query_params['mch_id']}]]></mch_id>
            <nonce_str><![CDATA[{query_params['nonce_str']}]]></nonce_str>
            <sign><![CDATA[{query_params['sign']}]]></sign>
            <out_trade_no><![CDATA[{query_params['out_trade_no']}]]></out_trade_no>
        </xml>
        """

        headers = {'Content-Type': 'application/xml'}
        response = requests.post(query_url, data=xml_data.encode('utf-8'), headers=headers)

        if response.status_code == 200:
            response_text = response.text
            if 'SUCCESS' in response_text and 'trade_state' in response_text:
                # 解析支付状态
                if 'SUCCESS' in response_text:
                    return ResponseUtil.success(data={"payment_status": "SUCCESS"})
                elif 'NOTPAY' in response_text:
                    return ResponseUtil.success(data={"payment_status": "NOTPAY"})
                else:
                    return ResponseUtil.success(data={"payment_status": "OTHER"})
            else:
                return ResponseUtil.error(message="查询支付状态失败")
        else:
            return ResponseUtil.error(message="查询接口调用失败")

    except Exception as e:
        logger.error(f"查询支付状态失败: {str(e)}")
        return ResponseUtil.error(message="查询支付状态失败")
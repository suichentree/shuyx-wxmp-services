import json
import time
import requests
from datetime import datetime
from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from config.log_config import logger
from utils.response_util import ResponseUtil
from utils.wechat_pay_v3_util import WechatPayV3Util

"""
微信H5支付V3版本接口控制器
包含完整的微信支付功能：H5支付、订单查询、退款、回调等
"""

# 创建路由实例
router = APIRouter(prefix='/api/wechat/h5pay', tags=['微信H5支付接口V3'])

# ==================== 核心业务接口 ====================

@router.post("/create_Wechat_H5Pay")
async def create_Wechat_H5Pay(order_no: Body(...),amount: int = Body(...),description: str = Body(...),
                       time_expire: str = Body(...)):
    """
    创建微信H5支付订单,微信H5支付V3版本接口
    1. 构建请求体
    2. 生成随机字符串和时间戳
    3. 生成签名
    4. 构建Authorization头
    5. 构建请求头
    6. 发送请求。调用微信支付API创建H5支付订单接口
    7. 若请求成功，则该接口会返回H5支付URL，商户需要将该URL返回给前端，前端再跳转至该URL，让用户在该URL上完成微信支付。
    """
    logger.info(f"创建微信H5支付订单。订单号: {order_no}, 订单金额: {amount}分")
    try:
        # 构建请求体
        body_data = WechatPayV3Util.build_body(
            order_no=order_no,
            amount=amount,
            description=description,
            time_expire=time_expire,
        )
        # 生成随机字符串和时间戳
        nonce_str = WechatPayV3Util.generate_nonce_str()
        timestamp = WechatPayV3Util.generate_timestamp()

        # 生成签名
        signature = WechatPayV3Util.generate_sign(
            request_method='POST',
            request_url='/v3/pay/transactions/h5',
            nonce_str=nonce_str,
            timestamp=timestamp,
            request_body_data=body_data
        )

        # 构建Authorization头
        authorization = WechatPayV3Util.build_authorization(nonce_str,timestamp,signature)

        # 构建请求头
        headers = {
            'Authorization': authorization,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        # 发送请求。调用微信支付API创建H5支付订单接口
        response = requests.post(
            'https://api.mch.weixin.qq.com/v3/pay/transactions/h5',
            json=body_data,
            headers=headers,
        )
        # 若请求成功，则该接口会返回H5支付URL，商户需要将该URL返回给前端，前端再跳转至该URL，让用户在该URL上完成微信支付。
        if response.status_code == 200:
            result = response.json()
            logger.info(f"H5支付订单创建成功: {order_no}")
            return ResponseUtil.success(data={
                'h5_url': result.get('h5_url'),
                'order_no': order_no,
                'prepay_id': result.get('prepay_id', ''),
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            error_msg = f"H5支付创建失败: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return ResponseUtil.error(message=error_msg)

    except Exception as e:
        raise Exception(f"创建H5支付订单异常: {str(e)}")


@router.post("/queryWeChatOrder")
async def query_Wechat_Order(order_no: str = Body(...), transaction_id: str = Body(...)):
    """
    微信支付订单号查询订单(订单支付成功后，商户可通过微信交易订单号或使用商户订单号查询订单；若订单未支付，则只能使用商户订单号查询订单。)
    """
    logger.info(f"查询微信支付订单: 商户订单号 order_no={order_no}, 微信订单号 transaction_id={transaction_id}")

    try:
        # 若微信订单号存在，则查询微信订单号
        if transaction_id:
            request_url = f"https://api.mch.weixin.qq.com/v3/pay/transactions/id/{transaction_id}?mchid={WechatPayV3Util.get_mch_id()}"
        elif order_no:
            request_url = f"https://api.mch.weixin.qq.com/v3/pay/transactions/out-trade-no/{order_no}?mchid={WechatPayV3Util.get_mch_id()}"
        else:
            return ResponseUtil.error(message="商户订单号和微信订单号不能同时为空")

        # 生成随机字符串和时间戳
        nonce_str = WechatPayV3Util.generate_nonce_str()
        timestamp = WechatPayV3Util.generate_timestamp()

        # 生成签名
        signature = WechatPayV3Util.generate_sign(
            request_method='GET',
            request_url=request_url.split('https://api.mch.weixin.qq.com')[1],
            nonce_str=nonce_str,
            timestamp=timestamp,
            request_body_data=None
        )

        # 构建Authorization头
        authorization = WechatPayV3Util.build_authorization(nonce_str, timestamp, signature)

        # 构建请求头
        headers = {
            'Authorization': authorization,
            'Accept': 'application/json',
        }

        # 发送请求。调用微信支付API查询订单接口
        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"订单查询成功: {result}")

            # 格式化返回数据
            return ResponseUtil.success(data={
                'appid': result.get('appid'),  # 商户下单时传入的公众账号ID
                'mchid': result.get('mchid'),  # 商户ID
                'out_trade_no': result.get('out_trade_no'),         # 商户订单号
                'transaction_id': result.get('transaction_id'),  # 微信支付订单号
                'trade_type': result.get('trade_type'),  # 交易类型
                'trade_state': result.get('trade_state'),       # 交易状态
                'trade_state_desc': result.get('trade_state_desc'),  # 交易状态描述
                'amount': result.get('amount', {}),  # 订单金额
                'success_time': result.get('success_time'),  # 支付成功时间,订单支付成功后才会返回
                'attach': result.get('attach'),  # 附加数据
                'scene_info': result.get('scene_info', {})  # 场景信息
            })
        else:
            error_msg = f"订单查询失败: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return ResponseUtil.error(message=error_msg)

    except Exception as e:
        raise Exception(f"查询微信支付订单异常: {str(e)}")

@router.post("/closeWechatOrder")
async def close_Wechat_Order(order_no: str = Body(...)):
    """
    未支付状态的订单，可在无需支付时调用此接口关闭订单。常见关闭微信支付订单情况包括：
    - 用户在商户系统提交取消订单请求，商户需执行关单操作。
    - 订单超时未支付（超出商户系统设定的可支付时间或下单时的time_expire支付截止时间），商户需进行关单处理。
    """
    logger.info(f"关闭微信支付订单: 商户订单号 {order_no}")

    try:
        # 构建请求URL
        request_url = f"https://api.mch.weixin.qq.com/v3/pay/transactions/out-trade-no/{order_no}/close"
        # 构建请求体数据
        request_body_data = {
            "mchid": WechatPayV3Util.get_mch_id()
        }

        # 生成随机字符串和时间戳
        nonce_str = WechatPayV3Util.generate_nonce_str()
        timestamp = WechatPayV3Util.generate_timestamp()

        # 生成签名
        signature = WechatPayV3Util.generate_sign(
            request_method='POST',
            request_url=request_url.split('https://api.mch.weixin.qq.com')[1],
            nonce_str=nonce_str,
            timestamp=timestamp,
            request_body_data=request_body_data
        )

        # 构建Authorization头
        authorization = WechatPayV3Util.build_authorization(nonce_str, timestamp, signature)

        # 构建请求头
        headers = {
            'Authorization': authorization,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        # 发送请求。调用微信H5支付关闭订单接口
        response = requests.post(request_url, json=request_body_data, headers=headers)
        if response.status_code == 204:
            return ResponseUtil.success(message=f"订单关闭成功: {order_no}")
        else:
            error_msg = f"订单关闭失败: {response.status_code} - {response.text}"
            return ResponseUtil.error(message=error_msg)

    except Exception as e:
        raise Exception(f"关闭微信支付订单失败: {str(e)}")


@router.post("/apply-refund")
async def apply_wechat_refund(order_no: str = Body(...), refund_amount: int = Body(...),
    refund_order_no: str = Body(...), reason: str = Body(None)):
    """
    申请微信退款
    """
    logger.info(f"申请微信退款: order_no={order_no}, refund_amount={refund_amount}, refund_order_no={refund_order_no}, reason={reason}")

    try:
        # 构建请求URL
        request_url = "https://api.mch.weixin.qq.com/v3/refund/domestic/refunds"

        # 构建请求体数据
        request_body_data = {
            "out_trade_no": order_no,  # 商户订单号
            "out_refund_no": refund_order_no,  # 商户系统内部的退款单号，商户系统内部唯一。同一商户退款单号多次请求只退一笔。
            "reason": reason or "用户申请退款",  # 退款原因,会在退款消息中展示
            "notify_url": WechatPayV3Util.get_refund_notify_url(),  # 退款回调通知URL。如果传了该参数，则商户平台上配置的退款回调地址将不会生效，优先回调当前传的这个地址。
            "amount": {
                "refund": refund_amount,    # 退款金额,单位为分，只能为整数，不能超过原订单支付金额。
                "total": refund_amount,     # 原支付交易的订单总金额,单位为分
                "currency": "CNY"
            }
        }

        # 生成随机字符串和时间戳
        nonce_str = WechatPayV3Util.generate_nonce_str()
        timestamp = WechatPayV3Util.generate_timestamp()

        # 生成签名
        signature = WechatPayV3Util.generate_sign(
            request_method='POST',
            request_url=request_url.split('https://api.mch.weixin.qq.com')[1],
            nonce_str=nonce_str,
            timestamp=timestamp,
            request_body_data=request_body_data
        )

        # 构建Authorization头
        authorization = WechatPayV3Util.build_authorization(nonce_str, timestamp, signature)

        # 构建请求头
        headers = {
            'Authorization': authorization,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        # 发送请求。调用微信H5支付申请退款接口
        response = requests.post(
            url=request_url,
            json=request_body_data,
            headers=headers,
        )

        if response.status_code == 200:
            result = response.json()
            return ResponseUtil.success(message="退款申请成功", data={
                'refund_id': result.get('refund_id'),   # 微信退款单号
                'out_refund_no': result.get('out_refund_no'),   # 商户退款单号
                'out_trade_no': result.get('out_trade_no'),     # 商户订单号
                'transaction_id': result.get('transaction_id'), # 微信支付订单号
                'channel': result.get('channel'),   # 退款渠道
                'user_received_account': result.get('user_received_account'), # 退款入账账户类型
                'create_time': result.get('create_time'), # 退款创建时间
                'status': result.get('status'), # 退款状态
                'amount': result.get('amount'), # 退款金额信息
            })
        else:
            error_msg = f"退款申请失败: {response.status_code} - {response.text}"
            return ResponseUtil.error(message=error_msg)

    except Exception as e:
        raise Exception(f"申请微信退款失败: {str(e)}")


@router.post("/wechatPayNotify")
async def wechat_pay_notify(request: Request):
    """
    微信服务器调用此接口告知支付结果

    当用户使用普通支付（APP支付/H5支付/JSAPI支付/Native支付/小程序支付）成功支付订单后，
    微信支付会通过POST的请求方式，向商户预先设置的回调地址(APP支付/H5支付/JSAPI支付/Native支付/小程序支付下单接口传入的notify_url)发送回调通知，让商户知晓用户已完成支付。

    注意：
    1. 商户侧对微信支付回调IP有防火墙策略限制的，需要对微信回调IP段开通白名单，否则会导致收不到回调(微信支付回调被商户防火墙拦截)。
    2. 商户接收到回调通知报文后，需在5秒内完成对报文的验签，并应答回调通知。
    """
    logger.info("微信支付回调通知接口")
    try:
        # 获取请求体数据
        body = await request.body()
        logger.info(f"支付通知原始数据: {body.decode('utf-8')}")

        # 获取请求头中的签名信息
        wecharpay_serial = request.headers.get('Wechatpay-Serial', '')  # 微信支付验签的证书序列号
        wecharpay_signature = request.headers.get('Wechatpay-Signature', '')  # 微信支付验签的签名值
        wecharpay_timestamp = request.headers.get('Wechatpay-Timestamp', '')  # 微信支付验签的时间戳
        wecharpay_nonce = request.headers.get('Wechatpay-Nonce', '')  # 微信支付验签的随机字符串
        cert_path = "path/to/wechat_public_cert.pem"  # 微信公钥证书路径


        # 验证签名
        is_valid = WechatPayV3Util.verify_signature(wecharpay_serial,wecharpay_signature,
                    wecharpay_timestamp,wecharpay_nonce, body.decode('utf-8'), cert_path)
        if is_valid:
            # 签名验证成功，处理支付结果
            logger.info("微信签名验证成功")
        else:
            # 签名验证失败，拒绝处理
            logger.error("微信签名验证失败")
            return JSONResponse(content={"code": "FAIL", "message": "签名验证失败"}, status_code=400)

        # 解析请求体数据
        notify_data = json.loads(body.decode('utf-8'))

        # 处理支付结果
        if notify_data.get('event_type') == 'TRANSACTION.SUCCESS':
            # 获取支付信息
            resource = notify_data.get('resource', {})
            cipher_text = resource.get('ciphertext', '')
            nonce = resource.get('nonce', '')
            associated_data = resource.get('associated_data', '')

            # 解密支付数据（实际项目中需要解密）
            # decrypted_data = decrypt_data(cipher_text, nonce, associated_data)
            decrypted_data = {
                'out_trade_no': notify_data.get('out_trade_no', 'ORDER_NO'),
                'transaction_id': notify_data.get('transaction_id', 'TRANS_ID'),
                'trade_state': 'SUCCESS',
                'success_time': datetime.now().isoformat()
            }

            logger.info(f"支付成功通知: 订单号={decrypted_data['out_trade_no']}, 微信订单号={decrypted_data['transaction_id']}")

            # 这里需要调用订单服务更新订单状态
            # order_service.update_order_payment_status(decrypted_data['out_trade_no'], 'PAID', decrypted_data['transaction_id'])

            # 返回成功响应
            return JSONResponse(content={"code": "SUCCESS", "message": "成功"})
        else:
            logger.warning(f"支付通知事件类型: {notify_data.get('event_type')}")
            return JSONResponse(content={"code": "FAIL", "message": "事件类型不支持"})

    except Exception as e:
        logger.error(f"处理支付通知失败: {str(e)}")
        return JSONResponse(content={"code": "FAIL", "message": "处理失败"})


@router.post("/refund-notify")
async def wechat_refund_notify(request: Request):
    """
    微信退款结果通知
    微信服务器调用此接口通知退款结果
    """
    logger.info("收到微信退款结果通知")

    try:
        # 获取请求体
        body = await request.body()
        logger.info(f"退款通知原始数据: {body.decode('utf-8')}")

        # 解析通知数据
        notify_data = json.loads(body.decode('utf-8'))

        # 处理退款结果
        if notify_data.get('event_type') == 'REFUND.SUCCESS':
            # 获取退款信息
            resource = notify_data.get('resource', {})
            cipher_text = resource.get('ciphertext', '')
            nonce = resource.get('nonce', '')
            associated_data = resource.get('associated_data', '')

            # 解密退款数据（实际项目中需要解密）
            # decrypted_data = decrypt_data(cipher_text, nonce, associated_data)
            decrypted_data = {
                'out_refund_no': notify_data.get('out_refund_no', 'REFUND_NO'),
                'out_trade_no': notify_data.get('out_trade_no', 'ORDER_NO'),
                'refund_id': notify_data.get('refund_id', 'REFUND_ID'),
                'status': 'SUCCESS'
            }

            logger.info(f"退款成功通知: 退款单号={decrypted_data['out_refund_no']}, 订单号={decrypted_data['out_trade_no']}")

            # 这里需要调用订单服务更新退款状态
            # order_service.update_order_refund_status(decrypted_data['out_trade_no'], 'REFUNDED')

            # 返回成功响应
            return JSONResponse(content={"code": "SUCCESS", "message": "成功"})
        else:
            logger.warning(f"退款通知事件类型: {notify_data.get('event_type')}")
            return JSONResponse(content={"code": "FAIL", "message": "事件类型不支持"})

    except Exception as e:
        logger.error(f"处理退款通知失败: {str(e)}")
        return JSONResponse(content={"code": "FAIL", "message": "处理失败"})


# ==================== 模拟测试接口 ====================

@router.post("/mock/create-h5-pay")
async def mock_create_h5_pay(pay_request: WechatH5PayRequest):
    """
    模拟创建H5支付订单 - 用于测试
    """
    logger.info(f"模拟创建H5支付订单: {pay_request.order_no}, 金额: {pay_request.amount}分")

    try:
        # 模拟H5支付URL
        mock_h5_url = f"https://mock.weixin.qq.com/h5-pay?order_no={pay_request.order_no}&amount={pay_request.amount}&t={int(time.time())}"

        return ResponseUtil.success(data={
            'h5_url': mock_h5_url,
            'order_no': pay_request.order_no,
            'prepay_id': f"MOCK_PREPAY_ID_{pay_request.order_no}_{int(time.time())}",
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mock_info': '这是模拟H5支付数据，仅用于测试'
        })

    except Exception as e:
        logger.error(f"模拟创建H5支付订单失败: {str(e)}")
        return ResponseUtil.error(message="模拟创建H5支付订单失败")


@router.post("/mock/query-order")
async def mock_query_wechat_order(query_request: WechatOrderQueryRequest):
    """
    模拟查询微信支付订单 - 用于测试
    """
    logger.info(f"模拟查询微信支付订单: order_no={query_request.order_no}, transaction_id={query_request.transaction_id}")

    try:
        # 模拟不同的支付状态
        import random
        mock_statuses = ["SUCCESS", "NOTPAY", "CLOSED", "REVOKED"]
        mock_status = random.choice(mock_statuses)

        order_no = query_request.order_no or f"MOCK_ORDER_{int(time.time())}"

        return ResponseUtil.success(data={
            'order_no': order_no,
            'transaction_id': query_request.transaction_id or f"MOCK_TRANS_{int(time.time())}",
            'trade_state': mock_status,
            'trade_state_desc': f'模拟状态: {mock_status}',
            'amount': {
                'total': 100,
                'payer_total': 100,
                'currency': 'CNY'
            },
            'success_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00') if mock_status == "SUCCESS" else None,
            'mock_info': '这是模拟订单查询，仅用于测试'
        })

    except Exception as e:
        logger.error(f"模拟查询订单失败: {str(e)}")
        return ResponseUtil.error(message="模拟查询订单失败")


@router.post("/mock/apply-refund")
async def mock_apply_wechat_refund(refund_request: WechatRefundRequest):
    """
    模拟申请微信退款 - 用于测试
    """
    logger.info(f"模拟申请微信退款: order_no={refund_request.order_no}, refund_amount={refund_request.refund_amount}")

    try:
        return ResponseUtil.success(data={
            'refund_id': f"MOCK_REFUND_ID_{refund_request.refund_order_no}",
            'out_refund_no': refund_request.refund_order_no,
            'out_trade_no': refund_request.order_no,
            'transaction_id': f"MOCK_TRANS_{refund_request.order_no}",
            'channel': 'ORIGINAL',
            'user_received_account': '用户原支付账户',
            'create_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
            'status': 'SUCCESS',
            'mock_info': '这是模拟退款申请，仅用于测试'
        })

    except Exception as e:
        logger.error(f"模拟申请退款失败: {str(e)}")
        return ResponseUtil.error(message="模拟申请退款失败")
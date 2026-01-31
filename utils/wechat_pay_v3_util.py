import time
import base64
import os
import json
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from config.log_config import logger

# 微信支付V3配置
WECHAT_PAY_CONFIG = {
    # appid公众账号ID。是微信开放平台(移动应用)或微信公众平台(小程序、公众号)为开发者的应用程序提供的唯一标识。
    # 可以填写这三种类型中的任意一种APPID，但请确保该appid与mchid有绑定关系。
    'appid': 'wxf8a159d29ef63e5a',
    # 商户号。是微信支付系统生成并分配给每个商户的唯一标识符。
    'mch_id': '1422735102',
    'api_key': 'your_api_key',  # API密钥
    'serial_no': '66EF99FF2A6B6B1A285EEFC9A8A3929E38696DBC',  # 商户API证书序列号serial_no,注意是商户API证书而不是平台证书.
    'private_key_path': 'path/to/apiclient_key.pem',  # 商户私钥路径

    # 商户接收支付成功回调通知的地址
    'notify_url': 'https://your-domain.com/api/wechat/h5pay/notify',
    # 退款通知URL
    'refund_notify_url': 'https://your-domain.com/api/wechat/h5pay/refund-notify',
}

class WechatPayV3Util:
    """微信支付V3工具类"""

    @staticmethod
    def get_mch_id() -> str:
        """获取商户号"""
        return WECHAT_PAY_CONFIG['mch_id']

    @staticmethod
    def get_notify_url() -> str:
        """获取支付回调通知URL"""
        return WECHAT_PAY_CONFIG['notify_url']

    @staticmethod
    def get_refund_notify_url() -> str:
        """获取退款通知URL"""
        return WECHAT_PAY_CONFIG['refund_notify_url']

    @staticmethod
    def generate_nonce_str() -> str:
        """生成随机字符串 - 使用类似hexdump的方式生成32位十六进制随机字符串"""
        # 从os.urandom获取16字节（128位）的随机数据
        random_bytes = os.urandom(16)
        # 将16字节转换为4个32位整数，然后格式化为8位十六进制大写字母
        hex_str = ''.join([
            f'{int.from_bytes(random_bytes[i:i + 4], byteorder="big"):08X}'
            for i in range(0, 16, 4)
        ])
        return hex_str

    @staticmethod
    def generate_timestamp() -> str:
        """生成时间戳"""
        return str(int(time.time()))

    @staticmethod
    def build_body(order_no: str, amount: int, description: str,
                   time_expire: str, attach: str = None):
        """
        构建微信h5支付接口v3版本的请求体参数
        """
        request_body_data = {
            "appid": WECHAT_PAY_CONFIG['appid'],
            "mchid": WECHAT_PAY_CONFIG['mch_id'],
            "notify_url": WECHAT_PAY_CONFIG['notify_url'],
            # 必填 商户系统内部订单号
            "out_trade_no": order_no,
            # 必填 商品描述。商户需传递能真实代表商品信息的描述，不能超过127个字符。
            "description": description,
            # 选填 支付结束时间是指用户能够完成该笔订单支付的最后时限，并非订单关闭的时间。超过此时间后，用户将无法对该笔订单进行支付。如商户需在超时后关闭订单，请调用关闭订单API接口。
            # 格式为yyyy-MM-DDTHH:mm:ss+TIMEZONE。例如：2015-05-20T13:29:35+08:00
            "time_expire": time_expire,
            "amount": {
                "total": amount,        # 必填 支付金额，单位为分，例如1元=100分
                "currency": "CNY"
            },
            # scene_info场景信息，包含多个字段，用于描述支付场景。  必填
            # - payer_client_ip 用户端实际IP地址，支持IPv4和IPv6格式。  必填
            # - device_id 支付终端设备ID，例如：013467007045764。
            # - store_info store_info  门店信息，包含多个字段，用于描述门店信息。
            #   - id 门店ID，例如：001。 必填
            #   - name 门店名称，例如：测试门店。
            #   - area_code 门店所在区域编码，例如：440305。
            #   - address 门店详细地址，例如：深圳市南山区科技南十二路。
            # - h5_info H5支付场景信息，包含多个字段，用于描述H5支付场景。
            #   - type  场景类型，使用H5支付的场景：Wap、iOS、Android  必填
            #   - app_name 应用名称，例如：XXX系统。
            #   - app_url  网站域名等
            "scene_info": {
                "payer_client_ip": "127.0.0.1",
                "device_id": "WEB_DEVICE_TEST_001",
                "store_info": {
                    "id": "XDJ_001",
                    "name": "谢大家",
                    "area_code": "511400",
                    "address": "广州市番禺区新造镇思贤村"
                }
            }
        }
        # 若有附加数据，添加到请求参数中
        if attach:
            # attach 用于存储订单相关的商户自定义信息，其总长度限制在128字符以内。该数据对用户不可见。
            request_body_data["attach"] = attach

        return request_body_data

    @staticmethod
    def generate_sign(request_method: str,request_url: str,nonce_str:str,timestamp:str,request_body_data: Optional[dict] = None) -> str:
        """
        生成签名
        1. 先根据请求方法、请求URL、时间戳、随机字符串、请求体数据，拼接签名消息
        2. 再使用商户私钥对签名消息进行SHA256 with RSA签名
        3. 对签名结果进行Base64编码得到签名值
        """

        # 1. 签名消息由请求方法、URL、时间戳、随机字符串、请求体JSON字符串组成
        sign_message = f"{request_method}\n{request_url}\n{timestamp}\n{nonce_str}\n"
        if request_body_data is not None:
            # 若请求体数据不为空，则签名消息中添加请求体JSON字符串+\n
            sign_message += json.dumps(request_body_data) + "\n"
        else:
            # 若请求体数据为空，则签名消息中添加\n
            sign_message += "\n"

        # 2. 使用商户私钥对签名消息进行SHA256 with RSA签名，并对签名结果进行Base64编码得到签名值
        # 这里提供简化版本，实际项目中需要处理异常情况
        try:
            with open(WECHAT_PAY_CONFIG['private_key_path'], 'rb') as f:
                private_key = load_pem_private_key(f.read(), password=None)

            signature = private_key.sign(
                sign_message.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            raise Exception(f"签名生成失败: {str(e)}")

    @staticmethod
    def build_authorization(nonce_str:str,timestamp:str,signature: str) -> str:
        # 构建Authorization头
        # Authorization头由以下部分组成：
        # 1. 认证类型：WECHATPAY2-SHA256-RSA2048
        # 2. 商户ID：mchid
        # 3. 序列号：serial_no
        # 4. 随机字符串：nonce_str 与签名中使用中的随机字符串相同
        # 5. 时间戳：timestamp 与签名中使用中的时间戳相同
        # 6. 签名：signature

        authorization = f'WECHATPAY2-SHA256-RSA2048 mchid="{WECHAT_PAY_CONFIG['mch_id']}",'
        authorization += f'serial_no="{WECHAT_PAY_CONFIG['serial_no']}",'
        authorization += f'nonce_str="{nonce_str}",'
        authorization += f'timestamp="{timestamp}",'
        authorization += f'signature="{signature}"'
        return authorization

    @staticmethod
    def verify_signature(wecharpay_serial: str,wecharpay_signature: str, wecharpay_timestamp: str,
                         wecharpay_nonce: str,body_str: str, cert_path: str) -> bool:
        """
        验证微信签名 - 微信H5支付V3版本
        :param wecharpay_serial: 微信支付验签的证书序列号
        :param wecharpay_signature: 验签的签名值
        :param wecharpay_timestamp: 验签的时间戳
        :param wecharpay_nonce: 验签的随机字符串
        :param cert_path: 微信公钥证书路径
        :return: 验证结果，True表示验证成功，False表示验证失败
        """
        try:
            # 先根据 wecharpay_serial 证书序列号判断选择验签的方式
            if wecharpay_serial.startswith("PUB_KEY_ID_"):
                # 若序列号以 PUB_KEY_ID_ 开头，则表示需要使用微信支付公钥进行验签
                # 微信支付公钥证书路径
                cert_path = f"{WECHAT_PAY_CONFIG['cert_dir']}/{wecharpay_serial}.pem"
            else:
                # 否则使用平台证书进行验签
                # 平台证书路径
                cert_path = f"{WECHAT_PAY_CONFIG['cert_dir']}/{wecharpay_serial}.pem"

            # 1. 先构建验签串
            verify_message = f"{wecharpay_timestamp}\n{wecharpay_nonce}\n{body_str}\n"

            # 1. 对验签的签名值进行Base64解码得到签名字节数组
            signature_bytes = base64.b64decode(wecharpay_signature)

            # 2. 加载微信公钥证书
            with open(cert_path, 'rb') as f:
                public_key = load_pem_public_key(f.read())

            # 3. 使用公钥验证签名
            public_key.verify(
                signature_bytes,
                verify_message.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            logger.info("微信签名验证成功")
            return True

        except Exception as e:
            logger.error(f"微信签名验证失败: {str(e)}")
            return False
import time
import jwt
from typing import Optional, Dict, Any

class JWTUtil:
    # 建议从环境变量或配置文件中读取密钥
    SECRET_KEY: str = "shu-yx-token"
    ALGORITHM = "HS256"  # 正确的算法名称

    @staticmethod
    def create_token(payload: Dict[str, Any]) -> str:
        """
        创建JWT token

        Args:
            payload: 要编码的数据字典

        Returns:
            生成的JWT token字符串
        """
        # 设置过期时间为一个小时后
        payload["exp"] = int(time.time()) + 60 * 60  # 一个小时过期
        # 生成JWT token
        token = jwt.encode(payload, JWTUtil.SECRET_KEY, algorithm=JWTUtil.ALGORITHM)
        return token

    @staticmethod
    def verify_token(token: str) -> bool:
        """
        验证token是否有效

        Args:
            token: 要验证的JWT token字符串

        Returns:
            token是否有效
        """
        try:
            # 解码JWT token
            jwt.decode(token, JWTUtil.SECRET_KEY, algorithms=[JWTUtil.ALGORITHM])
            return True
        except jwt.ExpiredSignatureError:
            # Token过期
            return False
        except jwt.InvalidTokenError:
            # Token无效
            return False

    @staticmethod
    def get_payload(token: str) -> Optional[Dict[str, Any]]:
        """
        获取token中的payload数据

        Args:
            token: 要解析的JWT token字符串

        Returns:
            token中的payload数据，如果token无效则返回None
        """
        try:
            payload = jwt.decode(token, JWTUtil.SECRET_KEY, algorithms=[JWTUtil.ALGORITHM])
            return payload
        except jwt.InvalidTokenError:
            return None
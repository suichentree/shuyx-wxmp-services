import time
import jwt
from typing import Optional, Dict, Any

class CommonUtil:
    """通用工具类"""

    @staticmethod
    def generate_id() -> str:
        """
        生成唯一ID
        :return: 唯一ID
        """
        return str(int(time.time() * 1000))


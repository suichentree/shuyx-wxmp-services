import time
from datetime import datetime
import random

import jwt
from typing import Optional, Dict, Any

class CommonUtil:
    """通用工具类"""

    @staticmethod
    def generate_order_no() -> str:
        """
        生成订单号 - 年月日时分秒格式
        格式：YYYYMMDDhhmmss + 3位随机数
        总长度：19位
        示例：ORDER_NO_2026013016400295864
        """
        now = datetime.now()
        time_str = now.strftime('%Y%m%d%H%M%S')  # 14位：年月日时分秒
        random_suffix = random.randint(10000, 99999)  # 5位随机数
        return f"ORDERNO_{time_str}{random_suffix}"


if __name__ == '__main__':
    print(CommonUtil.generate_order_no())

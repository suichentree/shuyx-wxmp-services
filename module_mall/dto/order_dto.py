from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class OrderDTO(BaseModel):
    """订单DTO"""
    id: Optional[int] = None
    order_no: Optional[str] = None  # 订单号
    user_id: Optional[int] = None   # 用户ID
    status: Optional[str] = None    # 订单状态：PENDING(待支付), PAID(已支付), REFUND(已退款), CANCELLED(已取消)
    total_amount: Optional[Decimal] = None  # 订单总金额
    pay_amount: Optional[Decimal] = None  # 实际支付金额，这里可以添加优惠券逻辑
    pay_time: Optional[datetime] = None  # 支付时间
    pay_channel: Optional[str] = None  # 支付渠道：WECHAT_PAY(微信支付), ALIPAY_PAY(支付宝支付)
    transaction_id: Optional[str] = None  # 支付交易ID
    refund_time: Optional[datetime] = None  # 退款时间
    refund_amount: Optional[Decimal] = None  # 退款金额
    create_time: Optional[datetime] = None  # 创建时间
    update_time: Optional[datetime] = None  # 更新时间

    model_config = ConfigDict(from_attributes=True)


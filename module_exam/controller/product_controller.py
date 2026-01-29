from typing import List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session
from config.log_config import logger
from module_exam.dto.product_dto import ProductDTO
from module_exam.dto.order_dto import OrderDTO, OrderCreateDTO
from module_exam.dto.order_product_dto import OrderProductCreateDTO
from module_exam.model.product_model import ProductModel
from module_exam.service.order_product_service import OrderProductService
from module_exam.service.product_service import ProductService
from module_exam.service.order_service import OrderService
from module_exam.service.user_product_service import UserProductService
from utils.response_util import ResponseUtil
from utils.common_util import CommonUtil

# 创建路由实例
router = APIRouter(prefix='/api/product', tags=['商品商城接口'])

# 创建服务实例
product_service = ProductService()
order_service = OrderService()
order_product_service = OrderProductService()
user_product_service = UserProductService()

"""
购物流程
1. 用户浏览商品 -> getProductList
2. 查看商品详情 -> getProductDetail
3. 创建订单 -> createOrder
4. 发起支付 -> createWechatPayment
5. 支付回调 -> paymentNotify
6. 确认支付 -> confirmOrderPayment
"""

@router.post("/getProductList")
def get_product_list(page_num: int = Body(...),page_size: int = Body(...),status: int = Body(1),
                     product_type: str = Body(None),db_session: Session = Depends(get_db_session)):
    """
    获取商品列表，并标注是否已购买
    """
    logger.info(f'/api/product/getProductList, page_num={page_num}, page_size={page_size}, product_type={product_type}, status={status}')

    # 构建查询条件
    query_data = ProductModel(status=status,type_code=product_type).to_dict()

    # 分页查询
    product_list = product_service.get_page_list_by_filters(
        db_session,
        page_num=page_num,
        page_size=page_size,
        filters=query_data
    )

    return ResponseUtil.success(
        code=200,
        message="success",
        data={
            "products": [ProductDTO.model_validate(product) for product in product_list],
            "total": len(product_list)
        }
    )


@router.post("/getProductDetail")
def get_product_detail(
        product_id: int = Body(...),
        db_session: Session = Depends(get_db_session)
):
    """
    获取商品详情
    """
    logger.info(f'/mp/product/getProductDetail, product_id={product_id}')

    product = product_service.get_by_id(db_session, product_id)
    if not product:
        return ResponseUtil.error(message="商品不存在")

    return ResponseUtil.success(
        code=200,
        message="success",
        data=ProductDTO.model_validate(product)
    )


@router.post("/getUserProducts")
def get_user_products(
        user_id: int = Body(...),
        db_session: Session = Depends(get_db_session)
):
    """
    获取用户的商品列表
    """
    logger.info(f'/mp/product/getUserProducts, user_id={user_id}')

    user_products = user_product_service.get_user_valid_products(db_session, user_id)

    return ResponseUtil.success(
        code=200,
        message="success",
        data={
            "user_products": [product for product in user_products]
        }
    )


@router.post("/checkProductAccess")
def check_product_access(
        user_id: int = Body(...),
        product_id: int = Body(...),
        db_session: Session = Depends(get_db_session)
):
    """
    检查用户是否有商品访问权限
    """
    logger.info(f'/mp/product/checkProductAccess, user_id={user_id}, product_id={product_id}')

    has_access = user_product_service.check_user_product_access(db_session, user_id, product_id)

    return ResponseUtil.success(
        code=200,
        message="success",
        data={"has_access": has_access}
    )


@router.post("/createOrder")
def create_order(
        user_id: int = Body(...),
        product_ids: List[int] = Body(...),
        db_session: Session = Depends(get_db_session)
):
    """
    创建订单
    """
    with db_session.begin():
        logger.info(f'/mp/product/createOrder, user_id={user_id}, product_ids={product_ids}')

        if not product_ids:
            return ResponseUtil.error(message="请选择要购买的商品")

        # 获取商品信息
        products = []
        total_amount = 0
        for product_id in product_ids:
            product = product_service.get_by_id(db_session, product_id)
            if not product:
                return ResponseUtil.error(message=f"商品ID {product_id} 不存在")
            if product.status != 1:
                return ResponseUtil.error(message=f"商品 {product.name} 已下架")

            products.append(product)
            total_amount += float(product.current_price)

        # 生成订单号
        order_no = CommonUtil.generate_id()

        # 创建订单数据
        order_data = OrderCreateDTO(
            user_id=user_id,
            order_no=order_no,  # 订单号
            total_amount=total_amount,   # 订单总金额
            pay_amount=total_amount,  # 实际支付金额，这里可以添加优惠券逻辑
        )

        # 创建订单项数据
        order_items = []
        for product in products:
            order_item = OrderProductCreateDTO(
                order_id=0,  # 临时值，会在创建订单后更新
                product_id=product.id,
                product_name=product.name,
                product_price=product.current_price,
                quantity=1,
                subtotal=product.current_price
            )
            order_items.append(order_item)

        try:
            # 创建订单
            order = order_service.create_order(db_session, order_data, order_items)

            return ResponseUtil.success(
                code=200,
                message="订单创建成功",
                data={
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "total_amount": order.total_amount,
                    "status": order.status
                }
            )
        except Exception as e:
            logger.error(f"创建订单失败: {str(e)}")
            return ResponseUtil.error(message="订单创建失败")


@router.post("/getOrderDetail")
def get_order_detail(
        order_id: int = Body(...),
        db_session: Session = Depends(get_db_session)
):
    """
    获取订单详情
    """
    logger.info(f'/mp/product/getOrderDetail, order_id={order_id}')

    order, order_items = order_service.get_order_with_items(db_session, order_id)
    if not order:
        return ResponseUtil.error(message="订单不存在")

    return ResponseUtil.success(
        code=200,
        message="success",
        data={
            "order": OrderDTO.model_validate(order),
            "order_items": [item for item in order_items]
        }
    )


@router.post("/getUserOrders")
def get_user_orders(
        user_id: int = Body(...),
        status: str = Body(None),
        db_session: Session = Depends(get_db_session)
):
    """
    获取用户订单列表
    """
    logger.info(f'/mp/product/getUserOrders, user_id={user_id}, status={status}')

    orders = order_service.get_user_orders(db_session, user_id, status)

    return ResponseUtil.success(
        code=200,
        message="success",
        data={
            "orders": [OrderDTO.model_validate(order) for order in orders]
        }
    )


@router.post("/cancelOrder")
def cancel_order(
        order_id: int = Body(...),
        db_session: Session = Depends(get_db_session)
):
    """
    取消订单
    """
    logger.info(f'/mp/product/cancelOrder, order_id={order_id}')

    order = order_service.get_by_id(db_session, order_id)
    if not order:
        return ResponseUtil.error(message="订单不存在")

    if order.status != 'PENDING':
        return ResponseUtil.error(message="只有待支付订单可以取消")

    try:
        updated_order = order_service.update_order_status(db_session, order_id, 'CANCELLED')
        return ResponseUtil.success(
            code=200,
            message="订单取消成功",
            data={"status": updated_order.status}
        )
    except Exception as e:
        logger.error(f"取消订单失败: {str(e)}")
        return ResponseUtil.error(message="订单取消失败")


@router.post("/confirmOrderPayment")
def confirm_order_payment(
        order_id: int = Body(...),
        transaction_id: str = Body(...),
        db_session: Session = Depends(get_db_session)
):
    """
    确认订单支付（支付成功后调用）
    """
    logger.info(f'/mp/product/confirmOrderPayment, order_id={order_id}, transaction_id={transaction_id}')

    order = order_service.get_by_id(db_session, order_id)
    if not order:
        return ResponseUtil.error(message="订单不存在")

    if order.status != 'PENDING':
        return ResponseUtil.error(message="订单状态异常")

    try:
        # 更新订单状态
        updated_order = order_service.update_order_status(
            db_session,
            order_id,
            'PAID',
            transaction_id=transaction_id,
            pay_channel='WECHAT'
        )

        # 为用户添加商品
        order_items = order_product_service.get_by_order_id(db_session, order_id)
        for item in order_items:
            user_product_service.add_user_product(
                db_session,
                user_id=order.user_id,
                product_id=item.product_id,
                source_type='PURCHASE',
                source_id=order_id
            )

        return ResponseUtil.success(
            code=200,
            message="支付确认成功",
            data={"status": updated_order.status}
        )
    except Exception as e:
        logger.error(f"确认支付失败: {str(e)}")
        return ResponseUtil.error(message="支付确认失败")
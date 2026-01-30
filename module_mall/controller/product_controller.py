from typing import List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session
from config.log_config import logger
from module_mall.dto.product_dto import ProductDTO
from module_mall.model.product_model import ProductModel
from module_mall.service.order_product_service import OrderProductService
from module_mall.service.product_service import ProductService
from module_mall.service.order_service import OrderService
from utils.response_util import ResponseUtil

# 创建路由实例
router = APIRouter(prefix='/api/product', tags=['商品商城接口'])

# 创建服务实例
product_service = ProductService()
order_service = OrderService()
order_product_service = OrderProductService()

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
def get_product_list(page_num: int = Body(1),page_size: int = Body(10),
                     type_code: str = Body(None),db_session: Session = Depends(get_db_session)):
    """
    获取商品列表，并标注是否已购买
    """
    logger.info(f'/api/product/getProductList, page_num={page_num}, page_size={page_size}, type_code={type_code}')

    # 构建查询条件(status=1表示上架商品)
    query_data = ProductModel(status=1,type_code=type_code).to_dict()

    # 分页查询
    product_list = product_service.get_page_list_by_filters(
        db_session,
        page_num=page_num,
        page_size=page_size,
        filters=query_data
    )

    return ResponseUtil.success(data={
          "products": [ProductDTO.model_validate(product) for product in product_list],
          "page_num": page_num,
          "page_size": page_size,
          "total": len(product_list)
        }
    )


@router.post("/getProductDetail")
def get_product_detail(product_id: int = Body(embed=True),db_session: Session = Depends(get_db_session)
):
    """
    获取商品详情
    """
    logger.info(f'/api/product/getProductDetail, product_id={product_id}')

    product = product_service.get_by_id(db_session, product_id)
    if not product:
        return ResponseUtil.error(message="商品不存在")

    return ResponseUtil.success(
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

    user_products = product_service.get_list_by_filters(db_session, filters={
        "user_id": user_id,
    })

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



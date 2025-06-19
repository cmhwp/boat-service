from fastapi import APIRouter, Depends, Query, Path, Body
from typing import Optional
from datetime import datetime

from app.models.user import User
from app.models.order import OrderStatus
from app.schemas.order import (
    OrderCreateSchema,
    DirectOrderCreateSchema,
    PaymentCreateSchema,
    OrderStatusUpdateSchema,
    OrderQuerySchema,
    OrderResponseSchema,
    OrderDetailSchema,
    OrderListItemSchema,
    PaymentResponseSchema,
    OrderStatsSchema
)
from app.schemas.response import ApiResponse, PaginatedData
from app.services.order_service import OrderService
from app.utils.auth import get_current_user, require_merchant

router = APIRouter(prefix="/orders", tags=["orders"])


# =================== 用户端订单接口 ===================

@router.post("/from-cart", response_model=ApiResponse[OrderResponseSchema], summary="从购物车创建订单")
async def create_order_from_cart(
    order_data: OrderCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    从购物车创建订单
    
    - **cart_item_ids**: 购物车商品ID列表（必填）
    - **receiver_name**: 收货人姓名（必填）
    - **receiver_phone**: 收货人电话（必填）
    - **receiver_address**: 收货地址（必填）
    - **user_notes**: 用户备注（可选）
    
    系统会自动验证：
    - 购物车商品存在且可购买
    - 同一订单只能包含同一商家商品
    - 库存充足性检查
    - 自动计算金额和运费
    """
    return await OrderService.create_order_from_cart(current_user, order_data)


@router.post("/direct", response_model=ApiResponse[OrderResponseSchema], summary="立即购买创建订单")
async def create_direct_order(
    order_data: DirectOrderCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    立即购买创建订单（跳过购物车）
    
    - **product_id**: 商品ID（必填）
    - **quantity**: 数量（必填）
    - **receiver_name**: 收货人姓名（必填）
    - **receiver_phone**: 收货人电话（必填）
    - **receiver_address**: 收货地址（必填）
    - **user_notes**: 用户备注（可选）
    
    适用于直接下单的场景，跳过购物车步骤
    """
    return await OrderService.create_direct_order(current_user, order_data)


@router.post("/payment", response_model=ApiResponse[PaymentResponseSchema], summary="创建支付")
async def create_payment(
    payment_data: PaymentCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    创建支付（模拟支付）
    
    - **order_id**: 订单ID（必填）
    - **payment_method**: 支付方式（必填）
    
    支持的支付方式：
    - alipay: 支付宝
    - wechat: 微信支付
    - bankcard: 银行卡
    - balance: 余额支付
    
    模拟支付有90%成功率，支付成功后自动扣减库存
    """
    return await OrderService.create_payment(current_user, payment_data)


@router.get("/my", response_model=ApiResponse[PaginatedData[OrderListItemSchema]], summary="获取我的订单列表")
async def get_my_orders(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[OrderStatus] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的订单列表
    
    支持按状态、日期过滤和分页查询
    """
    query_params = OrderQuerySchema(
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    return await OrderService.get_user_orders(current_user, query_params)


@router.get("/{order_id}", response_model=ApiResponse[OrderDetailSchema], summary="获取订单详情")
async def get_order_detail(
    order_id: int = Path(..., description="订单ID"),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单详情
    
    只有订单用户可以查看详情
    """
    return await OrderService.get_order_detail(current_user, order_id)


@router.patch("/{order_id}/cancel", response_model=ApiResponse[OrderResponseSchema], summary="取消订单")
async def cancel_order(
    order_id: int = Path(..., description="订单ID"),
    cancel_reason: str = Body(..., description="取消原因"),
    current_user: User = Depends(get_current_user)
):
    """
    取消订单（用户操作）
    
    - **cancel_reason**: 取消原因（必填）
    
    限制条件：
    - 只能取消待支付状态的订单
    - 只能取消自己的订单
    """
    return await OrderService.cancel_order(current_user, order_id, cancel_reason)


# =================== 商家端订单管理接口 ===================

@router.get("/merchant/list", response_model=ApiResponse[PaginatedData[OrderDetailSchema]], summary="获取商家订单列表")
async def get_merchant_orders(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[OrderStatus] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    current_user: User = Depends(require_merchant)
):
    """
    获取商家订单列表（商家端）
    
    包含完整的订单信息和用户数据
    """
    query_params = OrderQuerySchema(
        status=status,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    return await OrderService.get_merchant_orders(current_user, query_params)


@router.patch("/{order_id}/status", response_model=ApiResponse[OrderResponseSchema], summary="更新订单状态")
async def update_order_status(
    order_id: int = Path(..., description="订单ID"),
    status_data: OrderStatusUpdateSchema = ...,
    current_user: User = Depends(require_merchant)
):
    """
    更新订单状态（商家操作）
    
    - **status**: 订单状态（必填）
    - **merchant_notes**: 商家备注（可选）
    - **cancel_reason**: 取消原因（取消时必填）
    
    状态转换规则：
    - paid -> shipped/cancelled
    - shipped -> delivered
    - delivered -> completed
    
    取消已支付订单会自动恢复库存
    """
    return await OrderService.update_order_status(current_user, order_id, status_data)


@router.get("/merchant/stats", response_model=ApiResponse[OrderStatsSchema], summary="获取订单统计")
async def get_order_stats(
    current_user: User = Depends(require_merchant)
):
    """
    获取商家订单统计数据
    
    包括：
    - 各状态订单数量
    - 订单总金额
    - 已收款金额
    """
    return await OrderService.get_order_stats(current_user) 
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
    OrderConfirmReceiptSchema,
    OrderQuerySchema,
    OrderResponseSchema,
    OrderDetailSchema,
    OrderListItemSchema,
    PaymentResponseSchema,
    OrderStatsSchema,
    AdminOrderQuerySchema,
    AdminOrderDetailSchema,
    AdminOrderOperationSchema,
    AdminOrderListItemSchema
)
from app.schemas.response import ApiResponse, PaginatedData
from app.services.order_service import OrderService
from app.utils.auth import get_current_user, require_merchant, require_admin

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


@router.patch("/{order_id}/confirm-receipt", response_model=ApiResponse[OrderResponseSchema], summary="确认收货")
async def confirm_receipt(
    order_id: int = Path(..., description="订单ID"),
    user_notes: Optional[str] = Body(None, description="用户备注"),
    current_user: User = Depends(get_current_user)
):
    """
    用户确认收货
    
    - **order_id**: 订单ID（路径参数）
    - **user_notes**: 用户备注（可选）
    
    限制条件：
    - 只能确认已送达状态的订单
    - 只能确认自己的订单
    - 确认收货后订单状态变为已完成
    
    业务说明：
    - 确认收货是订单流程的最后一步
    - 确认后订单不可再修改状态
    - 可以添加收货备注（如商品质量、服务评价等）
    """
    return await OrderService.confirm_receipt(current_user, order_id, user_notes)


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


@router.get("/merchant/stats", response_model=ApiResponse[OrderStatsSchema], summary="获取订单统计")
async def get_order_stats(
    current_user: User = Depends(require_merchant)
):
    """
    获取商家订单统计
    
    包含各状态订单数量、金额统计等
    """
    return await OrderService.get_order_stats(current_user)


@router.get("/merchant/{order_id}", response_model=ApiResponse[OrderDetailSchema], summary="获取商家订单详情")
async def get_merchant_order_detail(
    order_id: int = Path(..., description="订单ID"),
    current_user: User = Depends(require_merchant)
):
    """
    获取商家订单详情（商家端）
    
    - **order_id**: 订单ID
    
    只能查看属于当前商家的订单详情，包含：
    - 完整的订单信息
    - 用户信息
    - 订单项目详情
    - 支付信息
    - 物流状态等
    """
    return await OrderService.get_merchant_order_detail(current_user, order_id)


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


# =================== 管理员端订单管理接口 ===================

@router.get("/admin/all", response_model=ApiResponse[PaginatedData[AdminOrderListItemSchema]], summary="管理员获取所有订单")
async def admin_get_all_orders(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[OrderStatus] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    merchant_id: Optional[int] = Query(None, description="商家ID过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    order_number: Optional[str] = Query(None, description="订单号搜索"),
    current_user: User = Depends(require_admin)
):
    """
    管理员获取所有订单列表
    
    - **status**: 状态过滤（可选）
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    - **merchant_id**: 商家ID过滤（可选）
    - **user_id**: 用户ID过滤（可选）
    - **order_number**: 订单号搜索（可选）
    
    包含用户信息、商家信息、支付信息等完整数据
    """
    query_params = AdminOrderQuerySchema(
        status=status,
        start_date=start_date,
        end_date=end_date,
        merchant_id=merchant_id,
        user_id=user_id,
        order_number=order_number,
        page=page,
        page_size=page_size
    )
    return await OrderService.admin_get_all_orders(current_user, query_params)


@router.get("/admin/{order_id}", response_model=ApiResponse[AdminOrderDetailSchema], summary="管理员获取订单详情")
async def admin_get_order_detail(
    order_id: int = Path(..., description="订单ID"),
    current_user: User = Depends(require_admin)
):
    """
    管理员获取订单详情
    
    包含完整的订单信息、用户信息、商家信息、支付记录等
    """
    return await OrderService.admin_get_order_detail(current_user, order_id)


@router.post("/admin/{order_id}/operate", response_model=ApiResponse[OrderResponseSchema], summary="管理员操作订单")
async def admin_operate_order(
    order_id: int = Path(..., description="订单ID"),
    operation_data: AdminOrderOperationSchema = ...,
    current_user: User = Depends(require_admin)
):
    """
    管理员操作订单
    
    - **operation**: 操作类型（必填）
      - force_cancel: 强制取消订单
      - refund: 处理退款
    - **reason**: 操作原因（必填）
    - **notes**: 管理员备注（可选）
    
    支持的操作：
    - 强制取消：可取消除已完成外的任何状态订单，已支付订单会恢复库存
    - 处理退款：只能对已支付订单操作，会恢复库存并设置为退款状态
    """
    return await OrderService.admin_operate_order(current_user, order_id, operation_data)


@router.get("/admin/statistics", response_model=ApiResponse[dict], summary="管理员获取平台订单统计")
async def admin_get_order_statistics(
    current_user: User = Depends(require_admin)
):
    """
    管理员获取平台订单统计
    
    包含：
    - 各状态订单数量统计
    - 总金额和已支付金额
    - 平台抽成和商家收入统计
    """
    return await OrderService.admin_get_order_statistics(current_user) 
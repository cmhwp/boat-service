from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from app.models.order import OrderStatus, PaymentMethod


# =================== 购物车相关模式 ===================

class CartAddSchema(BaseModel):
    """添加商品到购物车数据验证"""
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., gt=0, le=999, description="数量")


class CartUpdateSchema(BaseModel):
    """更新购物车商品数量数据验证"""
    quantity: int = Field(..., gt=0, le=999, description="数量")


class CartItemResponseSchema(BaseModel):
    """购物车项响应数据"""
    id: int = Field(..., description="购物车项ID")
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., description="数量")
    created_at: datetime = Field(..., description="添加时间")
    updated_at: datetime = Field(..., description="更新时间")
    product: Optional[dict] = Field(None, description="商品信息")
    subtotal: float = Field(..., description="小计金额")

    class Config:
        from_attributes = True


# =================== 订单相关模式 ===================

class OrderCreateSchema(BaseModel):
    """创建订单数据验证"""
    cart_item_ids: List[int] = Field(..., min_items=1, description="购物车商品ID列表")
    receiver_name: str = Field(..., max_length=50, description="收货人姓名")
    receiver_phone: str = Field(..., max_length=20, description="收货人电话")
    receiver_address: str = Field(..., max_length=255, description="收货地址")
    user_notes: Optional[str] = Field(None, description="用户备注")

    @validator('receiver_phone')
    def validate_phone(cls, v):
        import re
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v


class DirectOrderCreateSchema(BaseModel):
    """立即购买创建订单数据验证"""
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., gt=0, le=999, description="数量")
    receiver_name: str = Field(..., max_length=50, description="收货人姓名")
    receiver_phone: str = Field(..., max_length=20, description="收货人电话")
    receiver_address: str = Field(..., max_length=255, description="收货地址")
    user_notes: Optional[str] = Field(None, description="用户备注")

    @validator('receiver_phone')
    def validate_phone(cls, v):
        import re
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v


class PaymentCreateSchema(BaseModel):
    """创建支付数据验证"""
    order_id: int = Field(..., description="订单ID")
    payment_method: PaymentMethod = Field(..., description="支付方式")


class OrderStatusUpdateSchema(BaseModel):
    """订单状态更新数据验证"""
    status: OrderStatus = Field(..., description="订单状态")
    merchant_notes: Optional[str] = Field(None, description="商家备注")
    cancel_reason: Optional[str] = Field(None, description="取消原因")

    @validator('cancel_reason')
    def validate_cancel_reason(cls, v, values):
        if values.get('status') == OrderStatus.CANCELLED and not v:
            raise ValueError('取消订单时必须填写取消原因')
        return v


class OrderConfirmReceiptSchema(BaseModel):
    """用户确认收货数据验证"""
    user_notes: Optional[str] = Field(None, max_length=500, description="用户备注")


class OrderQuerySchema(BaseModel):
    """订单查询数据验证"""
    status: Optional[OrderStatus] = Field(None, description="状态过滤")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    merchant_id: Optional[int] = Field(None, description="商家ID过滤")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


# =================== 响应数据模式 ===================

class OrderItemResponseSchema(BaseModel):
    """订单项响应数据"""
    id: int = Field(..., description="订单项ID")
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., description="数量")
    unit_price: float = Field(..., description="单价")
    total_price: float = Field(..., description="小计")
    product_name: str = Field(..., description="商品名称")
    product_unit: str = Field(..., description="计量单位")
    product_image: Optional[str] = Field(None, description="商品图片")
    created_at: datetime = Field(..., description="创建时间")
    product: Optional[dict] = Field(None, description="商品信息")

    class Config:
        from_attributes = True


class OrderResponseSchema(BaseModel):
    """订单响应数据"""
    id: int = Field(..., description="订单ID")
    order_number: str = Field(..., description="订单号")
    user_id: int = Field(..., description="用户ID")
    merchant_id: int = Field(..., description="商家ID")
    total_amount: float = Field(..., description="订单总金额")
    discount_amount: float = Field(..., description="优惠金额")
    shipping_fee: float = Field(..., description="运费")
    final_amount: float = Field(..., description="实付金额")
    status: OrderStatus = Field(..., description="订单状态")
    payment_method: Optional[PaymentMethod] = Field(None, description="支付方式")
    receiver_name: str = Field(..., description="收货人姓名")
    receiver_phone: str = Field(..., description="收货人电话")
    receiver_address: str = Field(..., description="收货地址")
    user_notes: Optional[str] = Field(None, description="用户备注")
    merchant_notes: Optional[str] = Field(None, description="商家备注")
    cancel_reason: Optional[str] = Field(None, description="取消原因")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    paid_at: Optional[datetime] = Field(None, description="支付时间")
    shipped_at: Optional[datetime] = Field(None, description="发货时间")
    delivered_at: Optional[datetime] = Field(None, description="送达时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    cancelled_at: Optional[datetime] = Field(None, description="取消时间")

    class Config:
        from_attributes = True


class OrderDetailSchema(OrderResponseSchema):
    """订单详情数据"""
    user: Optional[dict] = Field(None, description="用户信息")
    merchant: Optional[dict] = Field(None, description="商家信息")
    order_items: List[OrderItemResponseSchema] = Field(default=[], description="订单项列表")


class OrderListItemSchema(BaseModel):
    """订单列表项数据"""
    id: int = Field(..., description="订单ID")
    order_number: str = Field(..., description="订单号")
    merchant_id: int = Field(..., description="商家ID")
    merchant_name: str = Field(..., description="商家名称")
    total_amount: float = Field(..., description="订单总金额")
    final_amount: float = Field(..., description="实付金额")
    status: OrderStatus = Field(..., description="订单状态")
    item_count: int = Field(..., description="商品种类数")
    total_quantity: int = Field(..., description="商品总数量")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class PaymentResponseSchema(BaseModel):
    """支付响应数据"""
    id: int = Field(..., description="支付记录ID")
    payment_number: str = Field(..., description="支付单号")
    order_id: int = Field(..., description="订单ID")
    amount: float = Field(..., description="支付金额")
    payment_method: PaymentMethod = Field(..., description="支付方式")
    is_success: bool = Field(..., description="是否支付成功")
    third_party_number: Optional[str] = Field(None, description="第三方支付单号")
    created_at: datetime = Field(..., description="创建时间")
    paid_at: Optional[datetime] = Field(None, description="支付时间")

    class Config:
        from_attributes = True


class OrderStatsSchema(BaseModel):
    """订单统计数据"""
    total_orders: int = Field(..., description="订单总数")
    pending_orders: int = Field(..., description="待支付订单数")
    paid_orders: int = Field(..., description="已支付订单数")
    shipped_orders: int = Field(..., description="已发货订单数")
    completed_orders: int = Field(..., description="已完成订单数")
    cancelled_orders: int = Field(..., description="已取消订单数")
    total_amount: float = Field(..., description="订单总金额")
    paid_amount: float = Field(..., description="已支付金额")
    
    class Config:
        from_attributes = True


# =================== 管理员相关模式 ===================

class AdminOrderQuerySchema(BaseModel):
    """管理员订单查询数据验证"""
    status: Optional[OrderStatus] = Field(None, description="状态过滤")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    merchant_id: Optional[int] = Field(None, description="商家ID过滤")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    order_number: Optional[str] = Field(None, description="订单号搜索")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class AdminOrderDetailSchema(OrderDetailSchema):
    """管理员订单详情数据"""
    payment_records: List[PaymentResponseSchema] = Field(default=[], description="支付记录列表")


class AdminOrderOperationSchema(BaseModel):
    """管理员订单操作数据验证"""
    operation: str = Field(..., description="操作类型：force_cancel（强制取消）| refund（退款）")
    reason: str = Field(..., min_length=5, max_length=500, description="操作原因")
    notes: Optional[str] = Field(None, max_length=500, description="管理员备注")

    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['force_cancel', 'refund']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_operations)}')
        return v


class AdminOrderListItemSchema(OrderListItemSchema):
    """管理员订单列表项数据"""
    user_name: str = Field(..., description="用户名")
    user_phone: Optional[str] = Field(None, description="用户电话")
    payment_method: Optional[PaymentMethod] = Field(None, description="支付方式")
    paid_at: Optional[datetime] = Field(None, description="支付时间")

    class Config:
        from_attributes = True 
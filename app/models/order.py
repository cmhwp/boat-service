from tortoise import fields
from tortoise.models import Model
from enum import Enum
from decimal import Decimal
from datetime import datetime


class OrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "pending"          # 待支付
    PAID = "paid"               # 已支付
    SHIPPED = "shipped"         # 已发货
    DELIVERED = "delivered"     # 已送达
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消
    REFUNDED = "refunded"       # 已退款


class PaymentMethod(str, Enum):
    """支付方式枚举"""
    ALIPAY = "alipay"           # 支付宝
    WECHAT = "wechat"           # 微信支付
    BANKCARD = "bankcard"       # 银行卡
    BALANCE = "balance"         # 余额支付


class Cart(Model):
    """购物车模型"""
    
    id = fields.BigIntField(pk=True, description="购物车ID")
    quantity = fields.IntField(description="商品数量")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="添加时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    user = fields.ForeignKeyField('models.User', related_name='cart_items', description="用户")
    product = fields.ForeignKeyField('models.Product', related_name='cart_items', description="商品")

    class Meta:
        table = "cart"
        table_description = "购物车表"
        unique_together = (("user", "product"),)  # 同一用户对同一商品只能有一条记录

    def __str__(self):
        return f"Cart(id={self.id}, user_id={self.user_id}, product_id={self.product_id})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('user', 'product')
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user": await self.user.to_dict() if self.user else None,
            "product": await self.product.to_dict() if self.product else None,
        }


class Order(Model):
    """订单模型"""
    
    id = fields.BigIntField(pk=True, description="订单ID")
    order_number = fields.CharField(max_length=32, unique=True, description="订单号")
    
    # 金额信息
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="订单总金额")
    discount_amount = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="优惠金额")
    shipping_fee = fields.DecimalField(max_digits=8, decimal_places=2, default=0, description="运费")
    final_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="实付金额")
    
    # 状态信息
    status = fields.CharEnumField(OrderStatus, default=OrderStatus.PENDING, description="订单状态")
    payment_method = fields.CharEnumField(PaymentMethod, null=True, description="支付方式")
    
    # 收货信息
    receiver_name = fields.CharField(max_length=50, description="收货人姓名")
    receiver_phone = fields.CharField(max_length=20, description="收货人电话")
    receiver_address = fields.CharField(max_length=255, description="收货地址")
    
    # 备注信息
    user_notes = fields.TextField(null=True, description="用户备注")
    merchant_notes = fields.TextField(null=True, description="商家备注")
    cancel_reason = fields.TextField(null=True, description="取消原因")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    paid_at = fields.DatetimeField(null=True, description="支付时间")
    shipped_at = fields.DatetimeField(null=True, description="发货时间")
    delivered_at = fields.DatetimeField(null=True, description="送达时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    cancelled_at = fields.DatetimeField(null=True, description="取消时间")

    # 外键关系
    user = fields.ForeignKeyField('models.User', related_name='orders', description="用户")
    merchant = fields.ForeignKeyField('models.Merchant', related_name='orders', description="商家")

    class Meta:
        table = "order"
        table_description = "订单表"

    def __str__(self):
        return f"Order(id={self.id}, number={self.order_number}, status={self.status})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('user', 'merchant', 'order_items__product')
        return {
            "id": self.id,
            "order_number": self.order_number,
            "user_id": self.user_id,
            "merchant_id": self.merchant_id,
            "total_amount": float(self.total_amount),
            "discount_amount": float(self.discount_amount),
            "shipping_fee": float(self.shipping_fee),
            "final_amount": float(self.final_amount),
            "status": self.status,
            "payment_method": self.payment_method,
            "receiver_name": self.receiver_name,
            "receiver_phone": self.receiver_phone,
            "receiver_address": self.receiver_address,
            "user_notes": self.user_notes,
            "merchant_notes": self.merchant_notes,
            "cancel_reason": self.cancel_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "paid_at": self.paid_at,
            "shipped_at": self.shipped_at,
            "delivered_at": self.delivered_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "user": await self.user.to_dict() if self.user else None,
            "merchant": await self.merchant.to_dict() if self.merchant else None,
            "order_items": [await item.to_dict() for item in self.order_items] if hasattr(self, 'order_items') else []
        }


class OrderItem(Model):
    """订单项模型"""
    
    id = fields.BigIntField(pk=True, description="订单项ID")
    quantity = fields.IntField(description="商品数量")
    unit_price = fields.DecimalField(max_digits=10, decimal_places=2, description="单价")
    total_price = fields.DecimalField(max_digits=12, decimal_places=2, description="小计")
    
    # 商品快照信息（防止商品信息变更影响历史订单）
    product_name = fields.CharField(max_length=100, description="商品名称")
    product_unit = fields.CharField(max_length=20, description="计量单位")
    product_image = fields.CharField(max_length=255, null=True, description="商品图片")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    # 外键关系
    order = fields.ForeignKeyField('models.Order', related_name='order_items', description="订单")
    product = fields.ForeignKeyField('models.Product', related_name='order_items', description="商品")

    class Meta:
        table = "order_item"
        table_description = "订单项表"

    def __str__(self):
        return f"OrderItem(id={self.id}, order_id={self.order_id}, product_name={self.product_name})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('order', 'product')
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total_price": float(self.total_price),
            "product_name": self.product_name,
            "product_unit": self.product_unit,
            "product_image": self.product_image,
            "created_at": self.created_at,
            "product": await self.product.to_dict() if self.product else None
        }


class PaymentRecord(Model):
    """支付记录模型"""
    
    id = fields.BigIntField(pk=True, description="支付记录ID")
    payment_number = fields.CharField(max_length=32, unique=True, description="支付单号")
    amount = fields.DecimalField(max_digits=12, decimal_places=2, description="支付金额")
    payment_method = fields.CharEnumField(PaymentMethod, description="支付方式")
    
    # 支付状态
    is_success = fields.BooleanField(default=False, description="是否支付成功")
    
    # 第三方支付信息（模拟）
    third_party_number = fields.CharField(max_length=64, null=True, description="第三方支付单号")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    paid_at = fields.DatetimeField(null=True, description="支付时间")

    # 外键关系
    order = fields.ForeignKeyField('models.Order', related_name='payment_records', description="订单")
    user = fields.ForeignKeyField('models.User', related_name='payment_records', description="用户")

    class Meta:
        table = "payment_record"
        table_description = "支付记录表"

    def __str__(self):
        return f"PaymentRecord(id={self.id}, number={self.payment_number}, success={self.is_success})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('order', 'user')
        return {
            "id": self.id,
            "payment_number": self.payment_number,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": float(self.amount),
            "payment_method": self.payment_method,
            "is_success": self.is_success,
            "third_party_number": self.third_party_number,
            "created_at": self.created_at,
            "paid_at": self.paid_at,
            "order": await self.order.to_dict() if self.order else None,
            "user": await self.user.to_dict() if self.user else None
        } 
from tortoise import fields
from tortoise.models import Model
from enum import Enum
from decimal import Decimal


class SplitType(str, Enum):
    """分账类型枚举"""
    BOOKING = "booking"  # 预约分账
    ORDER = "order"      # 订单分账


class SplitStatus(str, Enum):
    """分账状态枚举"""
    PENDING = "pending"      # 待分账
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败


class RecipientType(str, Enum):
    """收款方类型枚举"""
    PLATFORM = "platform"    # 平台
    MERCHANT = "merchant"    # 商家
    CREW = "crew"           # 船员


class SplitRule(Model):
    """分账规则模型"""
    
    id = fields.BigIntField(pk=True, description="规则ID")
    split_type = fields.CharEnumField(SplitType, description="分账类型")
    
    # 分账比例（百分比）
    platform_ratio = fields.DecimalField(max_digits=5, decimal_places=2, description="平台分成比例")
    merchant_ratio = fields.DecimalField(max_digits=5, decimal_places=2, description="商家分成比例")
    crew_ratio = fields.DecimalField(max_digits=5, decimal_places=2, default=0, description="船员分成比例")
    
    # 规则说明
    description = fields.TextField(null=True, description="规则说明")
    is_active = fields.BooleanField(default=True, description="是否启用")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "split_rule"
        table_description = "分账规则表"

    def __str__(self):
        return f"SplitRule(type={self.split_type}, platform={self.platform_ratio}%, merchant={self.merchant_ratio}%, crew={self.crew_ratio}%)"

    async def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "split_type": self.split_type,
            "platform_ratio": float(self.platform_ratio),
            "merchant_ratio": float(self.merchant_ratio),
            "crew_ratio": float(self.crew_ratio),
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SplitPayment(Model):
    """分账记录模型"""
    
    id = fields.BigIntField(pk=True, description="分账ID")
    split_number = fields.CharField(max_length=32, unique=True, description="分账单号")
    split_type = fields.CharEnumField(SplitType, description="分账类型")
    
    # 关联订单信息
    booking_id = fields.BigIntField(null=True, description="预约ID")
    order_id = fields.BigIntField(null=True, description="订单ID")
    
    # 分账金额
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="总金额")
    platform_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="平台分账金额")
    merchant_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="商家分账金额")
    crew_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="船员分账金额")
    
    # 状态
    status = fields.CharEnumField(SplitStatus, default=SplitStatus.PENDING, description="分账状态")
    
    # 备注
    notes = fields.TextField(null=True, description="备注")
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")

    # 外键关系
    merchant = fields.ForeignKeyField('models.Merchant', related_name='split_payments', description="商家")
    crew = fields.ForeignKeyField('models.Crew', related_name='split_payments', null=True, description="船员")
    split_rule = fields.ForeignKeyField('models.SplitRule', related_name='split_payments', description="分账规则")

    class Meta:
        table = "split_payment"
        table_description = "分账记录表"

    def __str__(self):
        return f"SplitPayment(number={self.split_number}, total={self.total_amount}, status={self.status})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('merchant', 'crew', 'split_rule')
        return {
            "id": self.id,
            "split_number": self.split_number,
            "split_type": self.split_type,
            "booking_id": self.booking_id,
            "order_id": self.order_id,
            "total_amount": float(self.total_amount),
            "platform_amount": float(self.platform_amount),
            "merchant_amount": float(self.merchant_amount),
            "crew_amount": float(self.crew_amount),
            "status": self.status,
            "notes": self.notes,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "merchant": await self.merchant.to_dict() if self.merchant else None,
            "crew": await self.crew.to_dict() if self.crew else None,
            "split_rule": await self.split_rule.to_dict() if self.split_rule else None,
        }


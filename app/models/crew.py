from tortoise import fields
from tortoise.models import Model
from enum import Enum
from decimal import Decimal


class CrewApplicationStatus(str, Enum):
    """船员申请状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CrewStatus(str, Enum):
    """船员状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class CrewApplication(Model):
    """船员申请模型"""
    
    id = fields.BigIntField(pk=True, description="申请ID")
    status = fields.CharEnumField(CrewApplicationStatus, default=CrewApplicationStatus.PENDING, description="申请状态")
    apply_time = fields.DatetimeField(auto_now_add=True, description="申请时间")
    handle_time = fields.DatetimeField(null=True, description="处理时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    user = fields.ForeignKeyField('models.User', related_name='crew_applications', description="申请用户")
    merchant = fields.ForeignKeyField('models.Merchant', related_name='crew_applications', description="申请商家")

    class Meta:
        table = "crew_application"
        table_description = "船员申请表"
        unique_together = (("user", "merchant"),)  # 同一用户不能重复申请同一商家

    def __str__(self):
        return f"CrewApplication(id={self.id}, user_id={self.user_id}, merchant_id={self.merchant_id})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('user', 'merchant')
        return {
            "id": self.id,
            "user_id": self.user_id,
            "merchant_id": self.merchant_id,
            "status": self.status,
            "apply_time": self.apply_time,
            "handle_time": self.handle_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user": await self.user.to_dict() if self.user else None,
            "merchant": await self.merchant.to_dict() if self.merchant else None
        }


class Crew(Model):
    """船员模型"""
    
    id = fields.BigIntField(pk=True, description="船员ID")
    boat_license = fields.CharField(max_length=50, unique=True, description="船员证号")
    status = fields.CharEnumField(CrewStatus, default=CrewStatus.ACTIVE, description="状态")
    rating = fields.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'), description="评分")
    join_time = fields.DatetimeField(auto_now_add=True, description="加入时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    user = fields.OneToOneField('models.User', related_name='crew', description="关联用户")
    merchant = fields.ForeignKeyField('models.Merchant', related_name='crews', description="关联商家")

    class Meta:
        table = "crew"
        table_description = "船员表"

    def __str__(self):
        return f"Crew(id={self.id}, user_id={self.user_id}, merchant_id={self.merchant_id})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('user', 'merchant')
        return {
            "id": self.id,
            "user_id": self.user_id,
            "merchant_id": self.merchant_id,
            "boat_license": self.boat_license,
            "status": self.status,
            "rating": float(self.rating),
            "join_time": self.join_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user": await self.user.to_dict() if self.user else None,
            "merchant": await self.merchant.to_dict() if self.merchant else None
        } 
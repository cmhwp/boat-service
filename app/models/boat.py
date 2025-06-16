from tortoise import fields
from tortoise.models import Model
from enum import Enum


class BoatType(str, Enum):
    """船只类型枚举"""
    PASSENGER = "passenger"  # 客船
    SIGHTSEEING = "sightseeing"  # 观光船
    FISHING = "fishing"  # 钓鱼船


class BoatStatus(str, Enum):
    """船只状态枚举"""
    AVAILABLE = "available"  # 可用
    IN_USE = "in_use"  # 使用中
    MAINTENANCE = "maintenance"  # 维护中
    INACTIVE = "inactive"  # 停用


class Boat(Model):
    """船只模型"""
    
    id = fields.BigIntField(pk=True, description="船只ID")
    name = fields.CharField(max_length=100, description="船只名称")
    license_number = fields.CharField(max_length=50, unique=True, description="船只证书号")
    boat_type = fields.CharEnumField(BoatType, default=BoatType.SIGHTSEEING, description="船只类型")
    capacity = fields.IntField(description="载客量")
    hourly_rate = fields.DecimalField(max_digits=10, decimal_places=2, description="小时费率")
    description = fields.TextField(null=True, description="船只描述")
    images = fields.JSONField(default=list, description="船只图片列表")
    status = fields.CharEnumField(BoatStatus, default=BoatStatus.AVAILABLE, description="状态")
    current_location = fields.CharField(max_length=255, null=True, description="当前位置")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    merchant = fields.ForeignKeyField('models.Merchant', related_name='boats', description="所属商家")

    class Meta:
        table = "boat"
        table_description = "船只表"

    def __str__(self):
        return f"Boat(id={self.id}, name={self.name}, license={self.license_number})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('merchant')
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "name": self.name,
            "license_number": self.license_number,
            "boat_type": self.boat_type,
            "capacity": self.capacity,
            "hourly_rate": float(self.hourly_rate),
            "description": self.description,
            "images": self.images,
            "status": self.status,
            "current_location": self.current_location,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "merchant": await self.merchant.to_dict() if self.merchant else None
        } 
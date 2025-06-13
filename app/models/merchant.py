from tortoise import fields
from tortoise.models import Model
from enum import Enum
from datetime import datetime


class MerchantStatus(str, Enum):
    """商家状态枚举"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class AuditResult(str, Enum):
    """审核结果枚举"""
    APPROVED = "approved"
    REJECTED = "rejected"


class Merchant(Model):
    """商家模型"""
    
    id = fields.BigIntField(pk=True, description="商家ID")
    merchant_name = fields.CharField(max_length=100, unique=True, description="商家名称")
    license_number = fields.CharField(max_length=50, unique=True, description="营业执照号")
    license_image = fields.CharField(max_length=255, description="营业执照图片")
    contact_phone = fields.CharField(max_length=20, description="联系电话")
    address = fields.CharField(max_length=255, null=True, description="地址")
    description = fields.TextField(null=True, description="描述")
    status = fields.CharEnumField(MerchantStatus, default=MerchantStatus.PENDING, description="状态")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    user = fields.OneToOneField('models.User', related_name='merchant', description="关联用户")

    class Meta:
        table = "merchant"
        table_description = "商家表"

    def __str__(self):
        return f"Merchant(id={self.id}, name={self.merchant_name})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('user')
        return {
            "id": self.id,
            "user_id": self.user_id,
            "merchant_name": self.merchant_name,
            "license_number": self.license_number,
            "license_image": self.license_image,
            "contact_phone": self.contact_phone,
            "address": self.address,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user": await self.user.to_dict() if self.user else None
        }


class MerchantAudit(Model):
    """商家审核记录模型"""
    
    id = fields.BigIntField(pk=True, description="审核ID")
    audit_result = fields.CharEnumField(AuditResult, description="审核结果")
    comment = fields.TextField(null=True, description="审核意见")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    # 外键关系
    merchant = fields.ForeignKeyField('models.Merchant', related_name='audits', description="关联商家")
    admin = fields.ForeignKeyField('models.User', related_name='audit_records', description="审核管理员")

    class Meta:
        table = "merchant_audit"
        table_description = "商家审核记录"

    def __str__(self):
        return f"MerchantAudit(id={self.id}, result={self.audit_result})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('merchant', 'admin')
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "admin_id": self.admin_id,
            "audit_result": self.audit_result,
            "comment": self.comment,
            "created_at": self.created_at,
            "merchant": await self.merchant.to_dict() if self.merchant else None,
            "admin": await self.admin.to_dict() if self.admin else None
        } 
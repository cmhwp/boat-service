from tortoise import fields
from tortoise.models import Model
from enum import Enum
from datetime import datetime


class RealnameAuthStatus(str, Enum):
    """实名认证状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RealnameAuth(Model):
    """实名认证模型"""
    
    id = fields.BigIntField(pk=True, description="认证ID")
    user_id = fields.BigIntField(unique=True, description="用户ID")
    real_name = fields.CharField(max_length=50, description="真实姓名")
    id_card = fields.CharField(max_length=20, unique=True, description="身份证号")
    front_image = fields.CharField(max_length=255, description="身份证正面照片")
    back_image = fields.CharField(max_length=255, description="身份证背面照片")
    status = fields.CharEnumField(
        RealnameAuthStatus, 
        default=RealnameAuthStatus.PENDING, 
        description="认证状态"
    )
    reject_reason = fields.TextField(null=True, description="拒绝原因")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "realname_auth"
        table_description = "实名认证表"

    def __str__(self):
        return f"RealnameAuth(id={self.id}, user_id={self.user_id}, status={self.status})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "real_name": self.real_name,
            "id_card": self.id_card,
            "front_image": self.front_image,
            "back_image": self.back_image,
            "status": self.status,
            "reject_reason": self.reject_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        } 
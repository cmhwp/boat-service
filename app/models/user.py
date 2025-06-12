from tortoise import fields
from tortoise.models import Model
from enum import Enum
from datetime import datetime
import bcrypt


class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    CREW = "crew"
    MERCHANT = "merchant"
    ADMIN = "admin"


class RealnameStatus(str, Enum):
    """实名认证状态枚举"""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class User(Model):
    """用户模型"""
    
    id = fields.IntField(pk=True, description="用户ID")
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=100, unique=True, description="邮箱")
    password = fields.CharField(max_length=255, description="密码")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    avatar = fields.CharField(max_length=500, null=True, description="头像URL")
    role = fields.CharEnumField(UserRole, default=UserRole.USER, description="用户角色")
    is_active = fields.BooleanField(default=True, description="是否激活")
    realname_status = fields.CharEnumField(
        RealnameStatus, 
        default=RealnameStatus.UNVERIFIED, 
        description="实名认证状态"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "users"
        table_description = "用户表"

    def __str__(self):
        return f"User(id={self.id}, username={self.username})"

    @classmethod
    def hash_password(cls, password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    @classmethod
    async def get_by_username_or_email(cls, identifier: str):
        """通过用户名或邮箱获取用户"""
        return await cls.filter(
            username=identifier
        ).first() or await cls.filter(
            email=identifier
        ).first()

    async def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "avatar": self.avatar,
            "role": self.role,
            "is_active": self.is_active,
            "realname_status": self.realname_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        } 
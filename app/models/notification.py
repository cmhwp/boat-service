from tortoise import fields
from tortoise.models import Model
from enum import Enum


class NotificationType(str, Enum):
    """通知类型枚举"""
    BOOKING_CREATED = "booking_created"        # 预约创建
    BOOKING_CONFIRMED = "booking_confirmed"    # 预约确认
    BOOKING_CANCELLED = "booking_cancelled"    # 预约取消
    BOOKING_COMPLETED = "booking_completed"    # 预约完成
    ORDER_CREATED = "order_created"            # 订单创建
    ORDER_PAID = "order_paid"                  # 订单支付
    ORDER_SHIPPED = "order_shipped"            # 订单发货
    ORDER_DELIVERED = "order_delivered"        # 订单送达
    CREW_ASSIGNED = "crew_assigned"            # 船员被指派
    REVIEW_RECEIVED = "review_received"        # 收到评价
    REALNAME_AUTH_APPROVED = "realname_auth_approved"    # 实名认证通过
    REALNAME_AUTH_REJECTED = "realname_auth_rejected"    # 实名认证拒绝
    MERCHANT_APPROVED = "merchant_approved"    # 商家审核通过
    MERCHANT_REJECTED = "merchant_rejected"    # 商家审核拒绝
    CREW_APPLICATION_APPROVED = "crew_application_approved"    # 船员申请通过
    CREW_APPLICATION_REJECTED = "crew_application_rejected"    # 船员申请拒绝
    SYSTEM_NOTICE = "system_notice"            # 系统通知


class NotificationStatus(str, Enum):
    """通知状态枚举"""
    UNREAD = "unread"    # 未读
    READ = "read"        # 已读
    DELETED = "deleted"  # 已删除


class Notification(Model):
    """通知模型"""
    
    id = fields.BigIntField(pk=True, description="通知ID")
    notification_type = fields.CharEnumField(NotificationType, description="通知类型")
    
    # 通知内容
    title = fields.CharField(max_length=100, description="通知标题")
    content = fields.TextField(description="通知内容")
    
    # 关联数据
    related_id = fields.BigIntField(null=True, description="关联数据ID")
    extra_data = fields.JSONField(null=True, description="额外数据")
    
    # 状态
    status = fields.CharEnumField(NotificationStatus, default=NotificationStatus.UNREAD, description="通知状态")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    read_at = fields.DatetimeField(null=True, description="阅读时间")

    # 外键关系
    user = fields.ForeignKeyField('models.User', related_name='notifications', description="接收用户")

    class Meta:
        table = "notification"
        table_description = "通知表"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification(type={self.notification_type}, user_id={self.user_id}, status={self.status})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('user')
        return {
            "id": self.id,
            "notification_type": self.notification_type,
            "title": self.title,
            "content": self.content,
            "related_id": self.related_id,
            "extra_data": self.extra_data,
            "status": self.status,
            "created_at": self.created_at,
            "read_at": self.read_at,
            "user_id": self.user_id,
        }


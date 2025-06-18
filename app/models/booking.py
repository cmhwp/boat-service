from tortoise import fields
from tortoise.models import Model
from enum import Enum
from decimal import Decimal
from datetime import datetime


class BookingStatus(str, Enum):
    """预约状态枚举"""
    PENDING = "pending"          # 待确认
    CONFIRMED = "confirmed"      # 已确认
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消
    REJECTED = "rejected"        # 已拒绝


class PaymentStatus(str, Enum):
    """支付状态枚举"""
    UNPAID = "unpaid"           # 未付款
    PAID = "paid"               # 已付款
    REFUNDED = "refunded"       # 已退款
    REFUNDING = "refunding"     # 退款中


class BoatBooking(Model):
    """船艇预约订单模型"""
    
    id = fields.BigIntField(pk=True, description="预约ID")
    booking_number = fields.CharField(max_length=32, unique=True, description="预约单号")
    
    # 预约基本信息
    start_time = fields.DatetimeField(description="开始时间")
    end_time = fields.DatetimeField(description="结束时间")
    duration_hours = fields.DecimalField(max_digits=4, decimal_places=1, description="预约时长(小时)")
    passenger_count = fields.IntField(description="乘客人数")
    
    # 费用信息
    hourly_rate = fields.DecimalField(max_digits=10, decimal_places=2, description="小时费率")
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="总金额")
    
    # 状态管理
    status = fields.CharEnumField(BookingStatus, default=BookingStatus.PENDING, description="预约状态")
    payment_status = fields.CharEnumField(PaymentStatus, default=PaymentStatus.UNPAID, description="支付状态")
    
    # 联系信息
    contact_name = fields.CharField(max_length=50, description="联系人姓名")
    contact_phone = fields.CharField(max_length=20, description="联系电话")
    
    # 备注信息
    user_notes = fields.TextField(null=True, description="用户备注")
    merchant_notes = fields.TextField(null=True, description="商家备注")
    cancel_reason = fields.TextField(null=True, description="取消原因")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    confirmed_at = fields.DatetimeField(null=True, description="确认时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    cancelled_at = fields.DatetimeField(null=True, description="取消时间")

    # 外键关系
    user = fields.ForeignKeyField('models.User', related_name='boat_bookings', description="预约用户")
    boat = fields.ForeignKeyField('models.Boat', related_name='bookings', description="预约船只")
    merchant = fields.ForeignKeyField('models.Merchant', related_name='boat_bookings', description="商家")
    assigned_crew = fields.ForeignKeyField('models.Crew', related_name='assigned_bookings', null=True, description="指派船员")

    class Meta:
        table = "boat_booking"
        table_description = "船艇预约订单表"

    def __str__(self):
        return f"BoatBooking(id={self.id}, number={self.booking_number}, status={self.status})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('user', 'boat', 'merchant', 'assigned_crew')
        return {
            "id": self.id,
            "booking_number": self.booking_number,
            "user_id": self.user_id,
            "boat_id": self.boat_id,
            "merchant_id": self.merchant_id,
            "assigned_crew_id": self.assigned_crew_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_hours": float(self.duration_hours),
            "passenger_count": self.passenger_count,
            "hourly_rate": float(self.hourly_rate),
            "total_amount": float(self.total_amount),
            "status": self.status,
            "payment_status": self.payment_status,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "user_notes": self.user_notes,
            "merchant_notes": self.merchant_notes,
            "cancel_reason": self.cancel_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confirmed_at": self.confirmed_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "user": await self.user.to_dict() if self.user else None,
            "boat": await self.boat.to_dict() if self.boat else None,
            "merchant": await self.merchant.to_dict() if self.merchant else None,
            "assigned_crew": await self.assigned_crew.to_dict() if self.assigned_crew else None,
        }


class CrewRating(Model):
    """船员评价模型"""
    
    id = fields.BigIntField(pk=True, description="评价ID")
    rating = fields.IntField(description="评分(1-5)")
    comment = fields.TextField(null=True, description="评价内容")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    # 外键关系
    booking = fields.OneToOneField('models.BoatBooking', related_name='crew_rating', description="关联预约")
    user = fields.ForeignKeyField('models.User', related_name='crew_ratings', description="评价用户")
    crew = fields.ForeignKeyField('models.Crew', related_name='received_ratings', description="被评价船员")

    class Meta:
        table = "crew_rating"
        table_description = "船员评价表"

    def __str__(self):
        return f"CrewRating(id={self.id}, rating={self.rating}, booking_id={self.booking_id})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('booking', 'user', 'crew')
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "crew_id": self.crew_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at,
            "user": await self.user.to_dict() if self.user else None,
            "crew": await self.crew.to_dict() if self.crew else None,
        } 
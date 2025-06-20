from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.booking import BookingStatus, PaymentStatus


class BookingCreateSchema(BaseModel):
    """创建预约数据验证"""
    boat_id: int = Field(..., description="船只ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    passenger_count: int = Field(..., ge=1, le=50, description="乘客人数")
    contact_name: str = Field(..., min_length=2, max_length=50, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, max_length=20, description="联系电话")
    user_notes: Optional[str] = Field(None, max_length=500, description="用户备注")

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('结束时间必须晚于开始时间')
        return v

    @validator('start_time')
    def validate_start_time(cls, v):
        if v <= datetime.now():
            raise ValueError('预约时间必须是未来时间')
        return v


class BookingStatusUpdateSchema(BaseModel):
    """预约状态更新数据验证"""
    status: BookingStatus = Field(..., description="预约状态")
    merchant_notes: Optional[str] = Field(None, max_length=500, description="商家备注")
    cancel_reason: Optional[str] = Field(None, max_length=500, description="取消原因")


class CrewAssignmentSchema(BaseModel):
    """船员派单数据验证"""
    booking_id: int = Field(..., description="预约ID")
    crew_id: int = Field(..., description="船员ID")
    notes: Optional[str] = Field(None, max_length=500, description="派单备注")


class CrewRatingCreateSchema(BaseModel):
    """船员评价创建数据验证"""
    booking_id: int = Field(..., description="预约ID")
    rating: int = Field(..., ge=1, le=5, description="评分(1-5)")
    comment: Optional[str] = Field(None, max_length=500, description="评价内容")


class BookingResponseSchema(BaseModel):
    """预约响应数据"""
    id: int = Field(..., description="预约ID")
    booking_number: str = Field(..., description="预约单号")
    user_id: int = Field(..., description="用户ID")
    boat_id: int = Field(..., description="船只ID")
    merchant_id: int = Field(..., description="商家ID")
    assigned_crew_id: Optional[int] = Field(None, description="指派船员ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    duration_hours: float = Field(..., description="预约时长(小时)")
    passenger_count: int = Field(..., description="乘客人数")
    hourly_rate: float = Field(..., description="小时费率")
    total_amount: float = Field(..., description="总金额")
    status: BookingStatus = Field(..., description="预约状态")
    payment_status: PaymentStatus = Field(..., description="支付状态")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系电话")
    user_notes: Optional[str] = Field(None, description="用户备注")
    merchant_notes: Optional[str] = Field(None, description="商家备注")
    cancel_reason: Optional[str] = Field(None, description="取消原因")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    confirmed_at: Optional[datetime] = Field(None, description="确认时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    cancelled_at: Optional[datetime] = Field(None, description="取消时间")

    class Config:
        from_attributes = True
        use_enum_values = True


class BookingDetailSchema(BookingResponseSchema):
    """预约详情数据"""
    user: Optional[dict] = Field(None, description="用户信息")
    boat: Optional[dict] = Field(None, description="船只信息")
    merchant: Optional[dict] = Field(None, description="商家信息")
    assigned_crew: Optional[dict] = Field(None, description="船员信息")
    crew_rating: Optional[dict] = Field(None, description="船员评价")

    class Config:
        from_attributes = True
        use_enum_values = True


class BookingListItemSchema(BaseModel):
    """预约列表项数据"""
    id: int = Field(..., description="预约ID")
    booking_number: str = Field(..., description="预约单号")
    boat_name: str = Field(..., description="船只名称")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    passenger_count: int = Field(..., description="乘客人数")
    total_amount: float = Field(..., description="总金额")
    status: BookingStatus = Field(..., description="预约状态")
    payment_status: PaymentStatus = Field(..., description="支付状态")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系电话")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        use_enum_values = True


class CrewRatingResponseSchema(BaseModel):
    """船员评价响应数据"""
    id: int = Field(..., description="评价ID")
    booking_id: int = Field(..., description="预约ID")
    user_id: int = Field(..., description="用户ID")
    crew_id: int = Field(..., description="船员ID")
    rating: int = Field(..., description="评分")
    comment: Optional[str] = Field(None, description="评价内容")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class BookingQuerySchema(BaseModel):
    """预约查询参数"""
    status: Optional[BookingStatus] = Field(None, description="状态过滤")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    boat_id: Optional[int] = Field(None, description="船只ID过滤")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class BookingStatsSchema(BaseModel):
    """预约统计数据"""
    total_bookings: int = Field(..., description="总预约数")
    pending_bookings: int = Field(..., description="待确认预约数")
    confirmed_bookings: int = Field(..., description="已确认预约数")
    completed_bookings: int = Field(..., description="已完成预约数")
    cancelled_bookings: int = Field(..., description="已取消预约数")
    total_revenue: float = Field(..., description="总收入")
    average_rating: float = Field(..., description="平均评分")


class BookingAvailabilityQuerySchema(BaseModel):
    """船只可用性查询参数"""
    boat_id: int = Field(..., description="船只ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")


class BookingAvailabilityResponseSchema(BaseModel):
    """船只可用性响应"""
    available: bool = Field(..., description="是否可用")
    reason: Optional[str] = Field(None, description="不可用原因")
    conflicting_bookings: List[dict] = Field(default=[], description="冲突预约列表")


# =================== 船员相关数据模式 ===================

class CrewTaskListItemSchema(BaseModel):
    """船员任务列表项数据"""
    id: int = Field(..., description="预约ID")
    booking_number: str = Field(..., description="预约单号")
    boat_name: str = Field(..., description="船只名称")
    customer_name: str = Field(..., description="客户姓名")
    customer_phone: str = Field(..., description="客户电话")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    passenger_count: int = Field(..., description="乘客人数")
    total_amount: float = Field(..., description="总金额")
    status: BookingStatus = Field(..., description="预约状态")
    user_notes: Optional[str] = Field(None, description="用户备注")
    merchant_notes: Optional[str] = Field(None, description="商家备注")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        use_enum_values = True


class CrewTaskDetailSchema(BaseModel):
    """船员任务详情数据"""
    id: int = Field(..., description="预约ID")
    booking_number: str = Field(..., description="预约单号")
    boat: dict = Field(..., description="船只信息")
    customer: dict = Field(..., description="客户信息")
    merchant: dict = Field(..., description="商家信息")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    duration_hours: float = Field(..., description="预约时长(小时)")
    passenger_count: int = Field(..., description="乘客人数")
    hourly_rate: float = Field(..., description="小时费率")
    total_amount: float = Field(..., description="总金额")
    status: BookingStatus = Field(..., description="预约状态")
    payment_status: PaymentStatus = Field(..., description="支付状态")
    user_notes: Optional[str] = Field(None, description="用户备注")
    merchant_notes: Optional[str] = Field(None, description="商家备注")
    created_at: datetime = Field(..., description="创建时间")
    confirmed_at: Optional[datetime] = Field(None, description="确认时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    crew_rating: Optional[dict] = Field(None, description="船员评价")

    class Config:
        from_attributes = True
        use_enum_values = True


class CrewTaskStatusUpdateSchema(BaseModel):
    """船员任务状态更新数据验证"""
    status: BookingStatus = Field(..., description="任务状态")
    notes: Optional[str] = Field(None, max_length=500, description="船员备注")

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = [BookingStatus.IN_PROGRESS, BookingStatus.COMPLETED]
        if v not in allowed_statuses:
            raise ValueError('船员只能更新任务为进行中或已完成状态')
        return v


class CrewTaskQuerySchema(BaseModel):
    """船员任务查询参数"""
    status: Optional[BookingStatus] = Field(None, description="状态过滤")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class CrewTaskStatsSchema(BaseModel):
    """船员任务统计数据"""
    total_tasks: int = Field(..., description="总任务数")
    confirmed_tasks: int = Field(..., description="已确认任务数")
    in_progress_tasks: int = Field(..., description="进行中任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    total_earnings: float = Field(..., description="总收入")
    average_rating: float = Field(..., description="平均评分")
    current_month_tasks: int = Field(..., description="本月任务数")
    current_month_earnings: float = Field(..., description="本月收入")


# =================== 支付相关数据模式 ===================

class PaymentRequestSchema(BaseModel):
    """支付请求数据验证"""
    booking_id: int = Field(..., description="预约ID")
    payment_method: str = Field("simulate", description="支付方式（模拟支付）")
    payment_notes: Optional[str] = Field(None, max_length=200, description="支付备注")


class PaymentResponseSchema(BaseModel):
    """支付响应数据"""
    booking_id: int = Field(..., description="预约ID")
    booking_number: str = Field(..., description="预约单号")
    total_amount: float = Field(..., description="支付金额")
    payment_status: str = Field(..., description="支付状态")
    payment_time: datetime = Field(..., description="支付时间")
    payment_method: str = Field(..., description="支付方式")
    payment_notes: Optional[str] = Field(None, description="支付备注")

    class Config:
        from_attributes = True
        use_enum_values = True


class RefundRequestSchema(BaseModel):
    """退款请求数据验证"""
    booking_id: int = Field(..., description="预约ID")
    refund_reason: str = Field(..., min_length=5, max_length=500, description="退款原因")


class RefundResponseSchema(BaseModel):
    """退款响应数据"""
    booking_id: int = Field(..., description="预约ID")
    booking_number: str = Field(..., description="预约单号")
    refund_amount: float = Field(..., description="退款金额")
    refund_status: str = Field(..., description="退款状态")
    refund_time: datetime = Field(..., description="退款时间")
    refund_reason: str = Field(..., description="退款原因")

    class Config:
        from_attributes = True
        use_enum_values = True


class PaymentStatusResponseSchema(BaseModel):
    """支付状态查询响应"""
    booking_id: int = Field(..., description="预约ID")
    booking_number: str = Field(..., description="预约单号")
    total_amount: float = Field(..., description="订单金额")
    payment_status: str = Field(..., description="支付状态")
    booking_status: str = Field(..., description="预约状态")
    created_at: datetime = Field(..., description="创建时间")
    payment_time: Optional[datetime] = Field(None, description="支付时间")

    class Config:
        from_attributes = True
        use_enum_values = True 
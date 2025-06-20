from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from app.models.boat import BoatType, BoatStatus


class BoatCreateSchema(BaseModel):
    """船只创建数据验证"""
    name: str = Field(..., max_length=100, description="船只名称")
    license_number: str = Field(..., max_length=50, description="船只证书号")
    boat_type: BoatType = Field(default=BoatType.SIGHTSEEING, description="船只类型")
    capacity: int = Field(..., gt=0, le=100, description="载客量")
    hourly_rate: Decimal = Field(..., gt=0, description="小时费率")
    description: Optional[str] = Field(None, description="船只描述")
    images: Optional[List[str]] = Field(default=[], description="船只图片列表")
    current_location: Optional[str] = Field(None, max_length=255, description="当前位置")

    @validator('images')
    def validate_images(cls, v):
        if v and len(v) > 10:
            raise ValueError('最多只能上传10张图片')
        return v


class BoatUpdateSchema(BaseModel):
    """船只更新数据验证"""
    name: Optional[str] = Field(None, max_length=100, description="船只名称")
    boat_type: Optional[BoatType] = Field(None, description="船只类型")
    capacity: Optional[int] = Field(None, gt=0, le=100, description="载客量")
    hourly_rate: Optional[Decimal] = Field(None, gt=0, description="小时费率")
    description: Optional[str] = Field(None, description="船只描述")
    images: Optional[List[str]] = Field(None, description="船只图片列表")
    current_location: Optional[str] = Field(None, max_length=255, description="当前位置")
    status: Optional[BoatStatus] = Field(None, description="状态")

    @validator('images')
    def validate_images(cls, v):
        if v and len(v) > 10:
            raise ValueError('最多只能上传10张图片')
        return v


class BoatResponseSchema(BaseModel):
    """船只响应数据"""
    id: int = Field(..., description="船只ID")
    merchant_id: int = Field(..., description="商家ID")
    name: str = Field(..., description="船只名称")
    license_number: str = Field(..., description="船只证书号")
    boat_type: BoatType = Field(..., description="船只类型")
    capacity: int = Field(..., description="载客量")
    hourly_rate: float = Field(..., description="小时费率")
    description: Optional[str] = Field(None, description="船只描述")
    images: List[str] = Field(default=[], description="船只图片列表")
    status: BoatStatus = Field(..., description="状态")
    current_location: Optional[str] = Field(None, description="当前位置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class BoatDetailSchema(BoatResponseSchema):
    """船只详情数据"""
    merchant: Optional[dict] = Field(None, description="商家信息")


class BoatListItemSchema(BaseModel):
    """船只列表项数据"""
    id: int = Field(..., description="船只ID")
    merchant_id: int = Field(..., description="商家ID")
    name: str = Field(..., description="船只名称")
    boat_type: BoatType = Field(..., description="船只类型")
    capacity: int = Field(..., description="载客量")
    hourly_rate: float = Field(..., description="小时费率")
    status: BoatStatus = Field(..., description="状态")
    current_location: Optional[str] = Field(None, description="当前位置")
    images: List[str] = Field(default=[], description="船只图片列表")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class BoatStatusUpdateSchema(BaseModel):
    """船只状态更新数据验证"""
    status: BoatStatus = Field(..., description="状态")
    current_location: Optional[str] = Field(None, max_length=255, description="当前位置")


# =================== 管理员相关模式 ===================

class AdminBoatQuerySchema(BaseModel):
    """管理员船只查询数据验证"""
    merchant_id: Optional[int] = Field(None, description="商家ID过滤")
    boat_type: Optional[BoatType] = Field(None, description="船只类型过滤")
    status: Optional[BoatStatus] = Field(None, description="状态过滤")
    name: Optional[str] = Field(None, description="船只名称搜索")
    license_number: Optional[str] = Field(None, description="证书号搜索")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class AdminBoatOperationSchema(BaseModel):
    """管理员船只操作数据验证"""
    operation: str = Field(..., description="操作类型：suspend（暂停）| activate（激活）| maintenance（维护）")
    reason: str = Field(..., min_length=5, max_length=500, description="操作原因")
    notes: Optional[str] = Field(None, max_length=500, description="管理员备注")

    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['suspend', 'activate', 'maintenance']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_operations)}')
        return v


class AdminBoatListItemSchema(BoatListItemSchema):
    """管理员船只列表项数据"""
    merchant_name: str = Field(..., description="商家名称")
    booking_count: int = Field(default=0, description="预约次数")
    total_income: float = Field(default=0.0, description="总收入")

    class Config:
        from_attributes = True


class AdminBoatDetailSchema(BoatDetailSchema):
    """管理员船只详情数据"""
    booking_count: int = Field(default=0, description="预约次数")
    total_income: float = Field(default=0.0, description="总收入")
    recent_bookings: List[dict] = Field(default=[], description="最近预约记录") 
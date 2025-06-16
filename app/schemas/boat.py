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
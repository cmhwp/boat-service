from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class SplitRuleCreateSchema(BaseModel):
    """分账规则创建"""
    split_type: str = Field(..., description="分账类型: booking/order")
    platform_ratio: Decimal = Field(..., ge=0, le=100, description="平台分成比例")
    merchant_ratio: Decimal = Field(..., ge=0, le=100, description="商家分成比例")
    crew_ratio: Decimal = Field(0, ge=0, le=100, description="船员分成比例")
    description: Optional[str] = Field(None, description="规则说明")


class SplitRuleResponseSchema(BaseModel):
    """分账规则响应"""
    id: int
    split_type: str
    platform_ratio: float
    merchant_ratio: float
    crew_ratio: float
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SplitPaymentResponseSchema(BaseModel):
    """分账记录响应"""
    id: int
    split_number: str
    split_type: str
    booking_id: Optional[int]
    order_id: Optional[int]
    total_amount: float
    platform_amount: float
    merchant_amount: float
    crew_amount: float
    status: str
    notes: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class SplitPaymentDetailSchema(BaseModel):
    """分账记录详情"""
    id: int
    split_number: str
    split_type: str
    booking_id: Optional[int]
    order_id: Optional[int]
    total_amount: float
    platform_amount: float
    merchant_amount: float
    crew_amount: float
    status: str
    notes: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    merchant: Optional[dict]
    crew: Optional[dict]
    split_rule: Optional[dict]


class SplitPaymentQuerySchema(BaseModel):
    """分账记录查询"""
    split_type: Optional[str] = None
    status: Optional[str] = None
    merchant_id: Optional[int] = None
    crew_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class SplitPaymentStatsSchema(BaseModel):
    """分账统计"""
    total_count: int
    pending_count: int
    completed_count: int
    failed_count: int
    total_platform_amount: float
    total_merchant_amount: float
    total_crew_amount: float


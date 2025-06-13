from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.crew import CrewApplicationStatus, CrewStatus


class CrewApplicationSchema(BaseModel):
    """船员申请schema"""
    merchant_id: int

    @validator('merchant_id')
    def validate_merchant_id(cls, v):
        if v <= 0:
            raise ValueError('商家ID必须大于0')
        return v


class CrewApplicationResponseSchema(BaseModel):
    """船员申请响应schema"""
    id: int
    user_id: int
    merchant_id: int
    status: CrewApplicationStatus
    apply_time: datetime
    handle_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class CrewApplicationDetailSchema(BaseModel):
    """船员申请详情schema"""
    id: int
    user_id: int
    merchant_id: int
    status: CrewApplicationStatus
    apply_time: datetime
    handle_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # 包含用户信息
    user: Optional[dict] = None
    # 包含商家信息
    merchant: Optional[dict] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class CrewApplicationHandleSchema(BaseModel):
    """船员申请处理schema"""
    application_id: int
    status: CrewApplicationStatus
    boat_license: Optional[str] = None  # 如果同意申请，需要提供船员证号

    @validator('application_id')
    def validate_application_id(cls, v):
        if v <= 0:
            raise ValueError('申请ID必须大于0')
        return v

    @validator('boat_license')
    def validate_boat_license(cls, v, values):
        # 如果状态是approved，船员证号不能为空
        if values.get('status') == CrewApplicationStatus.APPROVED:
            if not v or len(v.strip()) == 0:
                raise ValueError('同意申请时必须提供船员证号')
        if v and len(v.strip()) > 50:
            raise ValueError('船员证号长度不能超过50个字符')
        return v.strip() if v else v


class CrewResponseSchema(BaseModel):
    """船员响应schema"""
    id: int
    user_id: int
    merchant_id: int
    boat_license: str
    status: CrewStatus
    rating: float
    join_time: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class CrewDetailSchema(BaseModel):
    """船员详情schema"""
    id: int
    user_id: int
    merchant_id: int
    boat_license: str
    status: CrewStatus
    rating: float
    join_time: datetime
    created_at: datetime
    updated_at: datetime
    # 包含用户信息
    user: Optional[dict] = None
    # 包含商家信息
    merchant: Optional[dict] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class CrewUpdateSchema(BaseModel):
    """船员更新schema"""
    boat_license: Optional[str] = None
    status: Optional[CrewStatus] = None
    rating: Optional[float] = None

    @validator('boat_license')
    def validate_boat_license(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('船员证号不能为空')
        if v is not None and len(v.strip()) > 50:
            raise ValueError('船员证号长度不能超过50个字符')
        return v.strip() if v else v

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('评分必须在0-5之间')
        return v


class CrewListItemSchema(BaseModel):
    """船员列表项schema"""
    id: int
    user_id: int
    merchant_id: int
    boat_license: str
    status: CrewStatus
    rating: float
    join_time: datetime

    class Config:
        from_attributes = True
        use_enum_values = True 
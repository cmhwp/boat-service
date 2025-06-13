from pydantic import BaseModel, validator, HttpUrl
from typing import Optional
from datetime import datetime
from app.models.merchant import MerchantStatus, AuditResult


class MerchantApplySchema(BaseModel):
    """商家申请schema"""
    merchant_name: str
    license_number: str
    license_image: str
    contact_phone: str
    address: Optional[str] = None
    description: Optional[str] = None

    @validator('merchant_name')
    def validate_merchant_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('商家名称不能为空')
        if len(v.strip()) > 100:
            raise ValueError('商家名称长度不能超过100个字符')
        return v.strip()

    @validator('license_number')
    def validate_license_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('营业执照号不能为空')
        if len(v.strip()) > 50:
            raise ValueError('营业执照号长度不能超过50个字符')
        return v.strip()

    @validator('license_image')
    def validate_license_image(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('营业执照图片不能为空')
        # 检查是否是有效的URL格式
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('营业执照图片必须是有效的URL地址')
        return v.strip()

    @validator('contact_phone')
    def validate_contact_phone(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('联系电话不能为空')
        if len(v.strip()) > 20:
            raise ValueError('联系电话长度不能超过20个字符')
        return v.strip()


class MerchantUpdateSchema(BaseModel):
    """商家更新schema"""
    merchant_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None

    @validator('merchant_name')
    def validate_merchant_name(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('商家名称不能为空')
        if v is not None and len(v.strip()) > 100:
            raise ValueError('商家名称长度不能超过100个字符')
        return v.strip() if v else v

    @validator('contact_phone')
    def validate_contact_phone(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('联系电话不能为空')
        if v is not None and len(v.strip()) > 20:
            raise ValueError('联系电话长度不能超过20个字符')
        return v.strip() if v else v


class MerchantResponseSchema(BaseModel):
    """商家响应schema"""
    id: int
    user_id: int
    merchant_name: str
    license_number: str
    license_image: str
    contact_phone: str
    address: Optional[str]
    description: Optional[str]
    status: MerchantStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class MerchantAuditSchema(BaseModel):
    """商家审核schema"""
    merchant_id: int
    audit_result: AuditResult
    comment: Optional[str] = None

    @validator('comment')
    def validate_comment(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('审核意见长度不能超过1000个字符')
        return v


class MerchantAuditResponseSchema(BaseModel):
    """商家审核响应schema"""
    id: int
    merchant_id: int
    admin_id: int
    audit_result: AuditResult
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class MerchantListItemSchema(BaseModel):
    """商家列表项schema"""
    id: int
    user_id: int
    merchant_name: str
    license_number: str
    contact_phone: str
    address: Optional[str]
    status: MerchantStatus
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class MerchantDetailSchema(BaseModel):
    """商家详情schema"""
    id: int
    user_id: int
    merchant_name: str
    license_number: str
    license_image: str
    contact_phone: str
    address: Optional[str]
    description: Optional[str]
    status: MerchantStatus
    created_at: datetime
    updated_at: datetime
    # 可以包含用户信息
    user: Optional[dict] = None
    # 可以包含审核记录
    audits: Optional[list] = None

    class Config:
        from_attributes = True
        use_enum_values = True 
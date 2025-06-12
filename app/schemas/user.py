from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, RealnameStatus


class UserRegisterSchema(BaseModel):
    """用户注册schema"""
    username: str
    email: EmailStr
    password: str

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少为6个字符')
        return v


class UserLoginSchema(BaseModel):
    """用户登录schema"""
    identifier: str  # 可以是用户名或邮箱
    password: str

    @validator('identifier')
    def validate_identifier(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('用户名或邮箱不能为空')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('密码不能为空')
        return v


class UserResponseSchema(BaseModel):
    """用户响应schema"""
    id: int
    username: str
    email: str
    phone: Optional[str]
    avatar: Optional[str]
    role: UserRole
    is_active: bool
    realname_status: RealnameStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class UserUpdateSchema(BaseModel):
    """用户更新schema"""
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    realname_status: Optional[RealnameStatus] = None

    class Config:
        use_enum_values = True


class LoginResponseSchema(BaseModel):
    """登录响应schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponseSchema


class TokenPayload(BaseModel):
    """JWT Token载荷"""
    user_id: int
    username: str
    role: str
    exp: int


class ChangePasswordSchema(BaseModel):
    """修改密码schema"""
    old_password: str
    new_password: str
    confirm_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('新密码长度至少为6个字符')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class SendVerificationCodeSchema(BaseModel):
    """发送验证码schema"""
    email: EmailStr


class VerifyEmailCodeSchema(BaseModel):
    """验证邮箱验证码schema"""
    email: EmailStr
    code: str

    @validator('code')
    def validate_code(cls, v):
        if len(v) != 6 or not v.isdigit():
            raise ValueError('验证码必须是6位数字')
        return v


class CompleteRegistrationSchema(BaseModel):
    """完成注册schema"""
    username: str
    email: EmailStr
    password: str
    verification_code: str

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少为6个字符')
        return v

    @validator('verification_code')
    def validate_code(cls, v):
        if len(v) != 6 or not v.isdigit():
            raise ValueError('验证码必须是6位数字')
        return v


class ForgotPasswordSchema(BaseModel):
    """忘记密码schema"""
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    """重置密码schema"""
    token: str
    new_password: str
    confirm_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('新密码长度至少为6个字符')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class VerificationCodeResponseSchema(BaseModel):
    """验证码响应schema"""
    message: str
    expires_in: int  # 过期时间（秒）


class UploadResponseSchema(BaseModel):
    """文件上传响应schema"""
    url: str
    filename: str
    size: int
    content_type: str 
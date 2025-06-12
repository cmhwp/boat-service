from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from app.models.realname_auth import RealnameAuthStatus
import re


class RealnameAuthSubmitSchema(BaseModel):
    """提交实名认证schema"""
    real_name: str
    id_card: str

    @validator('real_name')
    def validate_real_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('真实姓名不能为空')
        v = v.strip()
        if len(v) < 2 or len(v) > 50:
            raise ValueError('真实姓名长度必须在2-50个字符之间')
        # 简单的中文姓名验证（支持中文字符和·）
        if not re.match(r'^[\u4e00-\u9fa5·]+$', v):
            raise ValueError('姓名只能包含中文字符和间隔符·')
        return v

    @validator('id_card')
    def validate_id_card(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('身份证号不能为空')
        v = v.strip().upper()  # 转换为大写
        
        # 验证身份证号格式
        if not re.match(r'^\d{17}[\dX]$', v):
            raise ValueError('身份证号格式不正确')
        
        # 验证校验码
        if not cls._validate_id_card_checksum(v):
            raise ValueError('身份证号校验失败')
        
        return v

    @staticmethod
    def _validate_id_card_checksum(id_card: str) -> bool:
        """验证身份证校验码"""
        if len(id_card) != 18:
            return False
        
        # 前17位系数
        coefficients = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        # 校验码对应表
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        try:
            # 计算校验码
            sum_val = sum(int(id_card[i]) * coefficients[i] for i in range(17))
            remainder = sum_val % 11
            expected_check_code = check_codes[remainder]
            
            return id_card[17] == expected_check_code
        except (ValueError, IndexError):
            return False


class RealnameAuthResponseSchema(BaseModel):
    """实名认证响应schema"""
    id: int
    user_id: int
    real_name: str
    id_card: str
    front_image: str
    back_image: str
    status: RealnameAuthStatus
    reject_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class RealnameAuthUpdateStatusSchema(BaseModel):
    """更新实名认证状态schema（管理员用）"""
    status: RealnameAuthStatus
    reject_reason: Optional[str] = None

    @validator('reject_reason')
    def validate_reject_reason(cls, v, values):
        if 'status' in values and values['status'] == RealnameAuthStatus.REJECTED:
            if not v or len(v.strip()) == 0:
                raise ValueError('拒绝时必须提供拒绝原因')
            if len(v.strip()) > 500:
                raise ValueError('拒绝原因长度不能超过500个字符')
        return v.strip() if v else None


class RealnameAuthListItemSchema(BaseModel):
    """实名认证列表项schema"""
    id: int
    user_id: int
    real_name: str
    id_card: str  # 可能需要脱敏显示
    status: RealnameAuthStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True

    def dict(self, **kwargs):
        """重写dict方法，对身份证号进行脱敏"""
        data = super().dict(**kwargs)
        if 'id_card' in data and data['id_card']:
            # 身份证号脱敏：显示前4位和后4位，中间用*代替
            id_card = data['id_card']
            if len(id_card) >= 8:
                data['id_card'] = id_card[:4] + '*' * (len(id_card) - 8) + id_card[-4:]
        return data


class RealnameAuthUpdateSchema(BaseModel):
    """用户更新实名认证schema"""
    real_name: Optional[str] = None
    id_card: Optional[str] = None

    @validator('real_name')
    def validate_real_name(cls, v):
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError('真实姓名不能为空')
            v = v.strip()
            if len(v) < 2 or len(v) > 50:
                raise ValueError('真实姓名长度必须在2-50个字符之间')
            # 简单的中文姓名验证（支持中文字符和·）
            if not re.match(r'^[\u4e00-\u9fa5·]+$', v):
                raise ValueError('姓名只能包含中文字符和间隔符·')
        return v

    @validator('id_card')
    def validate_id_card(cls, v):
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError('身份证号不能为空')
            v = v.strip().upper()  # 转换为大写
            
            # 验证身份证号格式
            if not re.match(r'^\d{17}[\dX]$', v):
                raise ValueError('身份证号格式不正确')
            
            # 验证校验码
            if not RealnameAuthSubmitSchema._validate_id_card_checksum(v):
                raise ValueError('身份证号校验失败')
        return v


class IdCardUploadResponseSchema(BaseModel):
    """身份证图片上传响应schema"""
    front_image: Optional[str] = None
    back_image: Optional[str] = None
    message: str 
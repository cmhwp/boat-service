from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import Dict, Any, Optional
from app.schemas.user import (
    UserRegisterSchema,
    UserLoginSchema,
    UserResponseSchema,
    LoginResponseSchema,
    UserUpdateSchema,
    ChangePasswordSchema,
    SendVerificationCodeSchema,
    VerifyEmailCodeSchema,
    CompleteRegistrationSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema,
    VerificationCodeResponseSchema,
    UploadResponseSchema
)
from app.schemas.response import ApiResponse, ResponseHelper, DictResponse, PaginatedData
from app.services.user_service import UserService
from app.utils.auth import get_current_user, require_admin
from app.models.user import User, UserRole, RealnameStatus

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/send-verification-code", response_model=ApiResponse[VerificationCodeResponseSchema], summary="发送邮箱验证码")
async def send_verification_code(email_data: SendVerificationCodeSchema):
    """
    发送邮箱验证码
    
    - **email**: 邮箱地址
    
    验证码有效期5分钟，用于注册验证
    """
    return await UserService.send_verification_code(email_data)


@router.post("/verify-email-code", response_model=ApiResponse[dict], summary="验证邮箱验证码")
async def verify_email_code(verify_data: VerifyEmailCodeSchema):
    """
    验证邮箱验证码
    
    - **email**: 邮箱地址
    - **code**: 6位验证码
    """
    return await UserService.verify_email_code(verify_data)


@router.post("/register", response_model=ApiResponse[UserResponseSchema], summary="完成用户注册")
async def complete_registration(user_data: CompleteRegistrationSchema):
    """
    完成用户注册
    
    - **username**: 用户名（3-50个字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6个字符）
    - **verification_code**: 6位邮箱验证码
    
    注册前需要先通过邮箱验证
    """
    return await UserService.complete_registration(user_data)


@router.post("/login", response_model=ApiResponse[LoginResponseSchema], summary="用户登录")
async def login(login_data: UserLoginSchema):
    """
    用户登录接口
    
    - **identifier**: 用户名或邮箱
    - **password**: 密码
    
    返回访问令牌和用户信息
    """
    return await UserService.login(login_data)


@router.post("/logout", response_model=ApiResponse[dict], summary="用户退出登录")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户退出登录接口
    
    退出当前登录状态，前端需要清除本地存储的token
    """
    return await UserService.logout(current_user)


@router.get("/me", response_model=ApiResponse[UserResponseSchema], summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    user_data = UserResponseSchema.from_orm(current_user)
    return ResponseHelper.success(user_data, "获取用户信息成功")


@router.put("/me", response_model=ApiResponse[UserResponseSchema], summary="更新当前用户信息")
async def update_current_user(
    update_data: UserUpdateSchema, 
    current_user: User = Depends(get_current_user)
):
    """更新当前登录用户的信息"""
    return await UserService.update_user(current_user.id, update_data)


@router.post("/change-password", response_model=ApiResponse[dict], summary="修改密码")
async def change_password(
    password_data: ChangePasswordSchema,
    current_user: User = Depends(get_current_user)
):
    """修改当前用户密码"""
    return await UserService.change_password(current_user, password_data)


@router.get("/{user_id}", response_model=ApiResponse[UserResponseSchema], summary="根据ID获取用户")
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """根据用户ID获取用户信息（仅管理员）"""
    return await UserService.get_user_by_id(user_id)


@router.put("/{user_id}", response_model=ApiResponse[UserResponseSchema], summary="更新用户信息")
async def update_user(
    user_id: int,
    update_data: UserUpdateSchema,
    current_user: User = Depends(require_admin)
):
    """更新指定用户信息（仅管理员）"""
    return await UserService.update_user(user_id, update_data)


@router.delete("/{user_id}", response_model=ApiResponse[dict], summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """删除指定用户（仅管理员）"""
    return await UserService.delete_user(user_id)


@router.post("/forgot-password", response_model=ApiResponse[dict], summary="忘记密码")
async def forgot_password(forgot_data: ForgotPasswordSchema):
    """
    忘记密码，发送重置链接
    
    - **email**: 注册邮箱地址
    
    如果邮箱存在，将发送密码重置链接，有效期30分钟
    """
    return await UserService.forgot_password(forgot_data)


@router.post("/reset-password", response_model=ApiResponse[dict], summary="重置密码")
async def reset_password(reset_data: ResetPasswordSchema):
    """
    使用重置token重置密码
    
    - **token**: 重置token（来自邮件链接）
    - **new_password**: 新密码（至少6个字符）
    - **confirm_password**: 确认新密码
    """
    return await UserService.reset_password(reset_data)


@router.get("/verify-reset-token/{token}", response_model=ApiResponse[dict], summary="验证重置token")
async def verify_reset_token(token: str):
    """
    验证密码重置token是否有效
    
    - **token**: 重置token
    """
    return await UserService.verify_reset_token(token)

@router.get("/", response_model=ApiResponse[PaginatedData[UserResponseSchema]], summary="获取用户列表")
async def get_users_list(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    role: Optional[UserRole] = Query(None, description="用户角色筛选"),
    realname_status: Optional[RealnameStatus] = Query(None, description="实名认证状态筛选"),
    is_active: Optional[bool] = Query(None, description="账户状态筛选"),
    current_user: User = Depends(require_admin)
):
    """
    获取用户列表（仅管理员）
    
    支持以下筛选条件：
    - **search**: 搜索用户名或邮箱
    - **role**: 用户角色筛选 (user, crew, merchant, admin)
    - **realname_status**: 实名认证状态筛选 (unverified, pending, verified)
    - **is_active**: 账户状态筛选 (true/false)
    """
    return await UserService.get_users_list(
        page=page, 
        page_size=page_size,
        search=search,
        role=role,
        realname_status=realname_status,
        is_active=is_active
    )


@router.post("/upload-avatar", response_model=ApiResponse[UploadResponseSchema], summary="上传用户头像")
async def upload_avatar(
    file: UploadFile = File(..., description="头像文件"),
    current_user: User = Depends(get_current_user)
):
    """
    上传用户头像
    
    - **file**: 头像图片文件（支持jpg、jpeg、png、gif、webp格式，最大10MB）
    
    自动压缩图片并上传到腾讯云COS
    """
    return await UserService.upload_avatar(current_user, file)


@router.delete("/avatar", response_model=ApiResponse[dict], summary="删除用户头像")
async def delete_avatar(current_user: User = Depends(get_current_user)):
    """删除当前用户的头像"""
    return await UserService.delete_avatar(current_user) 
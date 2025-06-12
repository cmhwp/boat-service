from fastapi import HTTPException, status, UploadFile
from tortoise.exceptions import IntegrityError
from typing import Optional, Dict, Any
from app.models.user import User
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
    VerificationCodeResponseSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData
from app.utils.jwt_utils import jwt_manager
from app.utils.email_utils import email_sender, generate_verification_code, generate_reset_token
from app.utils.redis_utils import EmailVerificationManager, PasswordResetManager
from app.utils.cos_utils import cos_uploader


class UserService:
    """用户服务类"""

    @staticmethod
    async def send_verification_code(email_data: SendVerificationCodeSchema) -> ApiResponse[VerificationCodeResponseSchema]:
        """发送验证码"""
        try:
            email = email_data.email
            
            # 检查邮箱是否已被注册
            existing_user = await User.get_or_none(email=email)
            if existing_user:
                return ResponseHelper.error("邮箱已被注册", 400)
            
            # 检查是否频繁发送
            existing_ttl = await EmailVerificationManager.get_code_ttl(email)
            if existing_ttl > 240:  # 如果距离上次发送不到1分钟
                return ResponseHelper.error("发送过于频繁，请稍后再试", 429)
            
            # 生成验证码
            code = generate_verification_code()
            
            # 存储到Redis
            success = await EmailVerificationManager.store_verification_code(email, code)
            if not success:
                return ResponseHelper.server_error("验证码存储失败，请稍后重试")
            
            # 发送邮件
            email_success = email_sender.send_verification_code(email, code)
            if not email_success:
                await EmailVerificationManager.delete_verification_code(email)
                return ResponseHelper.server_error("邮件发送失败，请检查邮箱地址")
            
            data = VerificationCodeResponseSchema(
                message="验证码已发送到您的邮箱",
                expires_in=EmailVerificationManager.VERIFICATION_CODE_EXPIRE
            )
            return ResponseHelper.success(data, "验证码发送成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"发送验证码失败: {str(e)}")

    @staticmethod
    async def verify_email_code(verify_data: VerifyEmailCodeSchema) -> ApiResponse[dict]:
        """验证邮箱验证码"""
        try:
            email = verify_data.email
            code = verify_data.code
            
            # 验证验证码
            is_valid = await EmailVerificationManager.verify_code(email, code)
            if not is_valid:
                return ResponseHelper.error("验证码错误或已过期", 400)
            
            return ResponseHelper.success({"verified": True}, "邮箱验证成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"验证失败: {str(e)}")

    @staticmethod
    async def complete_registration(user_data: CompleteRegistrationSchema) -> ApiResponse[UserResponseSchema]:
        """完成注册"""
        try:
            # 验证验证码
            is_valid = await EmailVerificationManager.verify_code(user_data.email, user_data.verification_code)
            if not is_valid:
                return ResponseHelper.error("验证码错误或已过期", 400)
            
            # 检查用户名是否已存在
            existing_user = await User.get_or_none(username=user_data.username)
            if existing_user:
                return ResponseHelper.error("用户名已存在", 400)
            
            # 检查邮箱是否已存在
            existing_email = await User.get_or_none(email=user_data.email)
            if existing_email:
                return ResponseHelper.error("邮箱已存在", 400)
            
            # 创建新用户
            hashed_password = User.hash_password(user_data.password)
            user = await User.create(
                username=user_data.username,
                email=user_data.email,
                password=hashed_password,
                role="user"  # 默认角色
            )
            
            user_response = UserResponseSchema.from_orm(user)
            return ResponseHelper.created(user_response, "注册成功")
            
        except IntegrityError as e:
            return ResponseHelper.error("用户名或邮箱已存在", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"注册失败: {str(e)}")

    @staticmethod
    async def login(login_data: UserLoginSchema) -> ApiResponse[LoginResponseSchema]:
        """用户登录"""
        try:
            # 通过用户名或邮箱查找用户
            user = await User.get_by_username_or_email(login_data.identifier)
            
            if not user:
                return ResponseHelper.unauthorized("用户名或邮箱不存在")
            
            # 验证密码
            if not user.verify_password(login_data.password):
                return ResponseHelper.unauthorized("密码错误")
            
            # 检查用户是否被禁用
            if not user.is_active:
                return ResponseHelper.unauthorized("用户已被禁用")
            
            # 生成JWT token
            token_data = jwt_manager.create_access_token(user)
            
            login_response = LoginResponseSchema(
                access_token=token_data["access_token"],
                token_type=token_data["token_type"],
                expires_in=token_data["expires_in"],
                user=UserResponseSchema.from_orm(user)
            )
            
            return ResponseHelper.success(login_response, "登录成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"登录失败: {str(e)}")

    @staticmethod
    async def get_user_by_id(user_id: int) -> ApiResponse[UserResponseSchema]:
        """根据ID获取用户"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return ResponseHelper.not_found("用户不存在")
            
            user_data = UserResponseSchema.from_orm(user)
            return ResponseHelper.success(user_data, "获取用户信息成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取用户失败: {str(e)}")

    @staticmethod
    async def update_user(user_id: int, update_data: UserUpdateSchema) -> ApiResponse[UserResponseSchema]:
        """更新用户信息"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return ResponseHelper.not_found("用户不存在")
            
            # 更新用户信息
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(user, field, value)
            
            await user.save()
            user_data = UserResponseSchema.from_orm(user)
            return ResponseHelper.success(user_data, "用户信息更新成功")
            
        except IntegrityError as e:
            return ResponseHelper.error("数据完整性错误，可能用户名或邮箱已存在", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"更新用户失败: {str(e)}")

    @staticmethod
    async def change_password(user: User, password_data: ChangePasswordSchema) -> ApiResponse[dict]:
        """修改密码"""
        try:
            # 验证旧密码
            if not user.verify_password(password_data.old_password):
                return ResponseHelper.error("旧密码错误", 400)
            
            # 更新密码
            user.password = User.hash_password(password_data.new_password)
            await user.save()
            
            return ResponseHelper.success({"changed": True}, "密码修改成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"密码修改失败: {str(e)}")

    @staticmethod
    async def delete_user(user_id: int) -> ApiResponse[dict]:
        """删除用户"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return ResponseHelper.not_found("用户不存在")
            
            await user.delete()
            return ResponseHelper.success({"deleted": True}, "用户删除成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"删除用户失败: {str(e)}")

    @staticmethod
    async def forgot_password(forgot_data: ForgotPasswordSchema) -> ApiResponse[dict]:
        """忘记密码"""
        try:
            email = forgot_data.email
            
            # 查找用户
            user = await User.get_or_none(email=email)
            if not user:
                # 为了安全考虑，即使用户不存在也返回成功消息
                return ResponseHelper.success({"sent": True}, "如果邮箱存在，重置链接已发送")
            
            # 生成重置token
            reset_token = generate_reset_token()
            
            # 存储到Redis
            success = await PasswordResetManager.store_reset_token(email, reset_token, user.id)
            if not success:
                return ResponseHelper.server_error("系统错误，请稍后重试")
            
            # 发送重置邮件
            email_success = email_sender.send_password_reset_email(email, reset_token, user.username)
            if not email_success:
                await PasswordResetManager.delete_reset_token(reset_token)
                return ResponseHelper.server_error("邮件发送失败，请稍后重试")
            
            return ResponseHelper.success({"sent": True}, "密码重置链接已发送到您的邮箱")
            
        except Exception as e:
            return ResponseHelper.server_error(f"密码重置请求失败: {str(e)}")

    @staticmethod
    async def reset_password(reset_data: ResetPasswordSchema) -> ApiResponse[dict]:
        """重置密码"""
        try:
            token = reset_data.token
            new_password = reset_data.new_password
            
            # 验证token
            token_data = await PasswordResetManager.verify_reset_token(token)
            if not token_data:
                return ResponseHelper.error("重置链接无效或已过期", 400)
            
            # 获取用户
            user = await User.get_or_none(id=token_data["user_id"])
            if not user:
                return ResponseHelper.not_found("用户不存在")
            
            # 更新密码
            user.password = User.hash_password(new_password)
            await user.save()
            
            return ResponseHelper.success({"reset": True}, "密码重置成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"密码重置失败: {str(e)}")

    @staticmethod
    async def verify_reset_token(token: str) -> ApiResponse[dict]:
        """验证重置token"""
        try:
            token_data = await PasswordResetManager.get_reset_token_data(token)
            if not token_data:
                return ResponseHelper.error("重置链接无效或已过期", 400)
            
            # 获取token剩余时间
            ttl = await PasswordResetManager.get_token_ttl(token)
            
            data = {
                "valid": True,
                "email": token_data["email"],
                "expires_in": ttl
            }
            return ResponseHelper.success(data, "重置链接验证成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"验证重置链接失败: {str(e)}")

    @staticmethod
    async def get_users_list(page: int = 1, page_size: int = 10) -> ApiResponse[PaginatedData[UserResponseSchema]]:
        """获取用户列表"""
        try:
            offset = (page - 1) * page_size
            users = await User.all().offset(offset).limit(page_size)
            total = await User.all().count()
            total_pages = (total + page_size - 1) // page_size
            
            user_list = [UserResponseSchema.from_orm(user) for user in users]
            
            paginated_data = PaginatedData(
                items=user_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
            return ResponseHelper.success(paginated_data, "获取用户列表成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取用户列表失败: {str(e)}")

    @staticmethod
    async def upload_avatar(user: User, file: UploadFile) -> ApiResponse[dict]:
        """上传用户头像"""
        try:
            # 上传到COS
            file_url, upload_info = await cos_uploader.upload_avatar(file, user.id)
            
            # 删除旧头像（如果存在）
            if user.avatar:
                old_filename = user.avatar.split('/')[-1]
                if old_filename.startswith(cos_uploader.bucket):
                    cos_uploader.delete_file(old_filename)
            
            # 更新用户头像URL
            user.avatar = file_url
            await user.save()
            
            return ResponseHelper.success(upload_info, "头像上传成功")
            
        except HTTPException as e:
            return ResponseHelper.error(e.detail, e.status_code)
        except Exception as e:
            return ResponseHelper.server_error(f"头像上传失败: {str(e)}")

    @staticmethod
    async def delete_avatar(user: User) -> ApiResponse[dict]:
        """删除用户头像"""
        try:
            if not user.avatar:
                return ResponseHelper.error("用户未设置头像", 400)
            
            # 从COS删除文件
            old_filename = user.avatar.split('/')[-1]
            cos_uploader.delete_file(old_filename)
            
            # 清空用户头像URL
            user.avatar = None
            await user.save()
            
            return ResponseHelper.success({"deleted": True}, "头像删除成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"头像删除失败: {str(e)}")

    @staticmethod
    async def logout(user: User) -> ApiResponse[dict]:
        """用户退出登录"""
        try:
            # 简单的退出登录，主要在前端清除token
            return ResponseHelper.success(
                {"logout": True}, 
                "退出登录成功"
            )
        except Exception as e:
            return ResponseHelper.server_error(f"退出登录失败: {str(e)}") 
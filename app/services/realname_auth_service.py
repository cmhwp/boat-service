from fastapi import HTTPException, status, UploadFile
from tortoise.exceptions import IntegrityError
from typing import Optional, Dict, Any, Tuple
from app.models.realname_auth import RealnameAuth, RealnameAuthStatus
from app.models.user import User, RealnameStatus
from app.schemas.realname_auth import (
    RealnameAuthSubmitSchema,
    RealnameAuthResponseSchema,
    RealnameAuthUpdateStatusSchema,
    RealnameAuthUpdateSchema,
    RealnameAuthListItemSchema,
    IdCardUploadResponseSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData
from app.utils.cos_utils import cos_uploader
import logging

logger = logging.getLogger(__name__)


class RealnameAuthService:
    """实名认证服务类"""

    @staticmethod
    async def upload_id_card_images(
        user: User,
        front_image: Optional[UploadFile] = None,
        back_image: Optional[UploadFile] = None
    ) -> ApiResponse[IdCardUploadResponseSchema]:
        """上传身份证图片"""
        try:
            result = IdCardUploadResponseSchema(message="图片上传成功")
            
            if front_image:
                # 上传身份证正面
                front_url, _ = await cos_uploader.upload_image(
                    front_image, 
                    prefix="id_cards/front/"
                )
                result.front_image = front_url
                logger.info(f"用户 {user.id} 上传身份证正面: {front_url}")
            
            if back_image:
                # 上传身份证背面
                back_url, _ = await cos_uploader.upload_image(
                    back_image,
                    prefix="id_cards/back/"
                )
                result.back_image = back_url
                logger.info(f"用户 {user.id} 上传身份证背面: {back_url}")
            
            if not front_image and not back_image:
                return ResponseHelper.error("至少需要上传一张图片", 400)
            
            return ResponseHelper.success(result, "图片上传成功")
            
        except Exception as e:
            logger.error(f"身份证图片上传失败: {e}")
            return ResponseHelper.server_error(f"图片上传失败: {str(e)}")

    @staticmethod
    async def submit_realname_auth(
        user: User,
        auth_data: RealnameAuthSubmitSchema,
        front_image_url: str,
        back_image_url: str
    ) -> ApiResponse[RealnameAuthResponseSchema]:
        """提交实名认证"""
        try:
            # 检查用户是否已经提交过认证
            existing_auth = await RealnameAuth.get_or_none(user_id=user.id)
            if existing_auth:
                if existing_auth.status == RealnameAuthStatus.PENDING:
                    return ResponseHelper.error("您已提交实名认证，请等待审核", 400)
                elif existing_auth.status == RealnameAuthStatus.APPROVED:
                    return ResponseHelper.error("您已通过实名认证", 400)
                # 如果之前被拒绝，可以重新提交
                elif existing_auth.status == RealnameAuthStatus.REJECTED:
                    # 更新现有记录
                    existing_auth.real_name = auth_data.real_name
                    existing_auth.id_card = auth_data.id_card
                    existing_auth.front_image = front_image_url
                    existing_auth.back_image = back_image_url
                    existing_auth.status = RealnameAuthStatus.PENDING
                    existing_auth.reject_reason = None
                    await existing_auth.save()
                    
                    # 更新用户状态
                    user.realname_status = RealnameStatus.PENDING
                    await user.save()
                    
                    auth_response = RealnameAuthResponseSchema.from_orm(existing_auth)
                    return ResponseHelper.success(auth_response, "实名认证重新提交成功")
            
            # 检查身份证号是否已被使用
            existing_id_card = await RealnameAuth.get_or_none(
                id_card=auth_data.id_card,
                status=RealnameAuthStatus.APPROVED
            )
            if existing_id_card:
                return ResponseHelper.error("该身份证号已被使用", 400)
            
            # 创建新的认证记录
            realname_auth = await RealnameAuth.create(
                user_id=user.id,
                real_name=auth_data.real_name,
                id_card=auth_data.id_card,
                front_image=front_image_url,
                back_image=back_image_url,
                status=RealnameAuthStatus.PENDING
            )
            
            # 更新用户状态
            user.realname_status = RealnameStatus.PENDING
            await user.save()
            
            auth_response = RealnameAuthResponseSchema.from_orm(realname_auth)
            return ResponseHelper.success(auth_response, "实名认证提交成功")
            
        except IntegrityError as e:
            if "id_card" in str(e):
                return ResponseHelper.error("该身份证号已被使用", 400)
            return ResponseHelper.error("数据完整性错误", 400)
        except Exception as e:
            logger.error(f"提交实名认证失败: {e}")
            return ResponseHelper.server_error(f"提交实名认证失败: {str(e)}")

    @staticmethod
    async def get_user_realname_auth(user: User) -> ApiResponse[RealnameAuthResponseSchema]:
        """获取用户的实名认证信息"""
        try:
            realname_auth = await RealnameAuth.get_or_none(user_id=user.id)
            if not realname_auth:
                return ResponseHelper.not_found("未找到实名认证记录")
            
            auth_response = RealnameAuthResponseSchema.from_orm(realname_auth)
            return ResponseHelper.success(auth_response, "获取实名认证信息成功")
            
        except Exception as e:
            logger.error(f"获取实名认证信息失败: {e}")
            return ResponseHelper.server_error(f"获取实名认证信息失败: {str(e)}")

    @staticmethod
    async def update_user_realname_auth(
        user: User,
        update_data: RealnameAuthUpdateSchema,
        front_image: Optional[UploadFile] = None,
        back_image: Optional[UploadFile] = None
    ) -> ApiResponse[RealnameAuthResponseSchema]:
        """用户更新实名认证信息"""
        try:
            # 获取用户的实名认证记录
            realname_auth = await RealnameAuth.get_or_none(user_id=user.id)
            if not realname_auth:
                return ResponseHelper.not_found("未找到实名认证记录，请先提交实名认证")
            
            # 检查认证状态，只有待审核或已拒绝的可以更新
            if realname_auth.status == RealnameAuthStatus.APPROVED:
                return ResponseHelper.error("已通过实名认证，无法修改", 400)
            
            # 如果没有任何更新内容，返回错误
            if (not update_data.real_name and not update_data.id_card and 
                not front_image and not back_image):
                return ResponseHelper.error("请提供要更新的信息", 400)
            
            # 更新文本信息
            updated_fields = []
            if update_data.real_name:
                realname_auth.real_name = update_data.real_name
                updated_fields.append("真实姓名")
            
            if update_data.id_card:
                # 检查新的身份证号是否已被使用（排除当前用户）
                existing_id_card = await RealnameAuth.get_or_none(
                    id_card=update_data.id_card,
                    status=RealnameAuthStatus.APPROVED
                )
                if existing_id_card and existing_id_card.user_id != user.id:
                    return ResponseHelper.error("该身份证号已被使用", 400)
                
                realname_auth.id_card = update_data.id_card
                updated_fields.append("身份证号")
            
            # 上传新的图片
            if front_image or back_image:
                upload_result = await RealnameAuthService.upload_id_card_images(
                    user, front_image, back_image
                )
                if not upload_result.success:
                    return upload_result
                
                if upload_result.data.front_image:
                    realname_auth.front_image = upload_result.data.front_image
                    updated_fields.append("身份证正面照片")
                
                if upload_result.data.back_image:
                    realname_auth.back_image = upload_result.data.back_image
                    updated_fields.append("身份证背面照片")
            
            # 如果状态是已拒绝，更新为待审核
            if realname_auth.status == RealnameAuthStatus.REJECTED:
                realname_auth.status = RealnameAuthStatus.PENDING
                realname_auth.reject_reason = None
                
                # 更新用户状态
                user.realname_status = RealnameStatus.PENDING
                await user.save()
                
                updated_fields.append("认证状态")
            
            # 保存更新
            await realname_auth.save()
            
            auth_response = RealnameAuthResponseSchema.from_orm(realname_auth)
            
            update_message = f"更新成功，已更新: {', '.join(updated_fields)}"
            if realname_auth.status == RealnameAuthStatus.PENDING:
                update_message += "，请等待审核"
            
            return ResponseHelper.success(auth_response, update_message)
            
        except IntegrityError as e:
            if "id_card" in str(e):
                return ResponseHelper.error("该身份证号已被使用", 400)
            return ResponseHelper.error("数据完整性错误", 400)
        except Exception as e:
            logger.error(f"更新实名认证失败: {e}")
            return ResponseHelper.server_error(f"更新实名认证失败: {str(e)}")

    @staticmethod
    async def get_realname_auth_list(
        page: int = 1,
        page_size: int = 10,
        status: Optional[RealnameAuthStatus] = None
    ) -> ApiResponse[PaginatedData[RealnameAuthListItemSchema]]:
        """获取实名认证列表（管理员）"""
        try:
            # 构建查询条件
            query = RealnameAuth.all()
            if status:
                query = query.filter(status=status)
            
            # 分页查询
            total = await query.count()
            auth_list = await query.order_by('-created_at').offset((page - 1) * page_size).limit(page_size)
            
            # 转换为响应格式
            auth_items = [RealnameAuthListItemSchema.from_orm(auth) for auth in auth_list]
            
            # 构建分页数据
            paginated_data = PaginatedData(
                items=auth_items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
            
            return ResponseHelper.success(paginated_data, "获取实名认证列表成功")
            
        except Exception as e:
            logger.error(f"获取实名认证列表失败: {e}")
            return ResponseHelper.server_error(f"获取实名认证列表失败: {str(e)}")

    @staticmethod
    async def get_realname_auth_detail(auth_id: int) -> ApiResponse[RealnameAuthResponseSchema]:
        """获取实名认证详情（管理员）"""
        try:
            realname_auth = await RealnameAuth.get_or_none(id=auth_id)
            if not realname_auth:
                return ResponseHelper.not_found("实名认证记录不存在")
            
            auth_response = RealnameAuthResponseSchema.from_orm(realname_auth)
            return ResponseHelper.success(auth_response, "获取实名认证详情成功")
            
        except Exception as e:
            logger.error(f"获取实名认证详情失败: {e}")
            return ResponseHelper.server_error(f"获取实名认证详情失败: {str(e)}")

    @staticmethod
    async def update_realname_auth_status(
        auth_id: int,
        update_data: RealnameAuthUpdateStatusSchema
    ) -> ApiResponse[RealnameAuthResponseSchema]:
        """更新实名认证状态（管理员）"""
        try:
            realname_auth = await RealnameAuth.get_or_none(id=auth_id)
            if not realname_auth:
                return ResponseHelper.not_found("实名认证记录不存在")
            
            # 更新认证状态
            realname_auth.status = update_data.status
            if update_data.reject_reason:
                realname_auth.reject_reason = update_data.reject_reason
            await realname_auth.save()
            
            # 更新用户的实名认证状态
            user = await User.get(id=realname_auth.user_id)
            if update_data.status == RealnameAuthStatus.APPROVED:
                user.realname_status = RealnameStatus.VERIFIED
            elif update_data.status == RealnameAuthStatus.REJECTED:
                user.realname_status = RealnameStatus.UNVERIFIED
            else:
                user.realname_status = RealnameStatus.PENDING
            await user.save()
            
            # 发送通知给用户
            from app.services.notification_service import NotificationService
            from app.models.notification import NotificationType
            if update_data.status == RealnameAuthStatus.APPROVED:
                await NotificationService.send_realname_auth_notification(
                    user_id=realname_auth.user_id,
                    auth_id=auth_id,
                    notification_type=NotificationType.REALNAME_AUTH_APPROVED
                )
            elif update_data.status == RealnameAuthStatus.REJECTED:
                await NotificationService.send_realname_auth_notification(
                    user_id=realname_auth.user_id,
                    auth_id=auth_id,
                    notification_type=NotificationType.REALNAME_AUTH_REJECTED,
                    extra_info={"reject_reason": update_data.reject_reason} if update_data.reject_reason else None
                )
            
            auth_response = RealnameAuthResponseSchema.from_orm(realname_auth)
            
            status_text = {
                RealnameAuthStatus.APPROVED: "通过",
                RealnameAuthStatus.REJECTED: "拒绝",
                RealnameAuthStatus.PENDING: "待审核"
            }
            
            return ResponseHelper.success(
                auth_response,
                f"实名认证状态更新为：{status_text[update_data.status]}"
            )
            
        except Exception as e:
            logger.error(f"更新实名认证状态失败: {e}")
            return ResponseHelper.server_error(f"更新实名认证状态失败: {str(e)}")

    @staticmethod
    async def delete_realname_auth(auth_id: int) -> ApiResponse[dict]:
        """删除实名认证记录（管理员）"""
        try:
            realname_auth = await RealnameAuth.get_or_none(id=auth_id)
            if not realname_auth:
                return ResponseHelper.not_found("实名认证记录不存在")
            
            # 删除相关图片文件
            try:
                if realname_auth.front_image:
                    filename = realname_auth.front_image.split('/')[-1]
                    cos_uploader.delete_file(f"id_cards/front/{filename}")
                
                if realname_auth.back_image:
                    filename = realname_auth.back_image.split('/')[-1]
                    cos_uploader.delete_file(f"id_cards/back/{filename}")
            except Exception as e:
                logger.warning(f"删除相关图片文件失败: {e}")
            
            # 更新用户状态
            user = await User.get(id=realname_auth.user_id)
            user.realname_status = RealnameStatus.UNVERIFIED
            await user.save()
            
            # 删除认证记录
            await realname_auth.delete()
            
            return ResponseHelper.success({}, "实名认证记录删除成功")
            
        except Exception as e:
            logger.error(f"删除实名认证记录失败: {e}")
            return ResponseHelper.server_error(f"删除实名认证记录失败: {str(e)}")
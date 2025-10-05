from typing import Optional, List
from datetime import datetime

from app.models.notification import Notification, NotificationType, NotificationStatus
from app.models.user import User
from app.schemas.notification import (
    NotificationCreateSchema,
    NotificationResponseSchema,
    NotificationListItemSchema,
    NotificationQuerySchema,
    NotificationStatsSchema,
    NotificationMarkReadSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData


class NotificationService:
    """通知服务类"""

    @staticmethod
    async def create_notification(notification_data: NotificationCreateSchema) -> ApiResponse:
        """创建通知"""
        try:
            notification = await Notification.create(
                user_id=notification_data.user_id,
                notification_type=notification_data.notification_type,
                title=notification_data.title,
                content=notification_data.content,
                related_id=notification_data.related_id,
                extra_data=notification_data.extra_data
            )

            # 通过WebSocket发送实时通知
            from app.utils.websocket_manager import websocket_manager
            await websocket_manager.send_notification(
                user_id=notification_data.user_id,
                notification=await notification.to_dict()
            )

            notification_dict = await notification.to_dict()
            notification_response = NotificationResponseSchema(**notification_dict)
            return ResponseHelper.created(notification_response, "通知创建成功")

        except Exception as e:
            return ResponseHelper.server_error(f"创建通知失败: {str(e)}")

    @staticmethod
    async def send_booking_notification(user_id: int, booking_id: int, notification_type: NotificationType, extra_info: dict = None) -> None:
        """发送预约相关通知"""
        try:
            notification_templates = {
                NotificationType.BOOKING_CREATED: {
                    "title": "预约创建成功",
                    "content": "您的船艇预约已创建，请等待商家确认"
                },
                NotificationType.BOOKING_CONFIRMED: {
                    "title": "预约已确认",
                    "content": "商家已确认您的预约，请准时到达"
                },
                NotificationType.BOOKING_CANCELLED: {
                    "title": "预约已取消",
                    "content": "您的预约已被取消"
                },
                NotificationType.BOOKING_COMPLETED: {
                    "title": "服务已完成",
                    "content": "服务已完成，期待您的评价"
                },
                NotificationType.CREW_ASSIGNED: {
                    "title": "船员已指派",
                    "content": "您的预约已安排船员服务"
                }
            }

            template = notification_templates.get(notification_type)
            if template:
                notification_data = NotificationCreateSchema(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=template["title"],
                    content=template["content"],
                    related_id=booking_id,
                    extra_data=extra_info
                )
                await NotificationService.create_notification(notification_data)
        except Exception:
            pass  # 通知失败不影响主流程

    @staticmethod
    async def send_order_notification(user_id: int, order_id: int, notification_type: NotificationType, extra_info: dict = None) -> None:
        """发送订单相关通知"""
        try:
            notification_templates = {
                NotificationType.ORDER_CREATED: {
                    "title": "订单创建成功",
                    "content": "您的订单已创建，请尽快完成支付"
                },
                NotificationType.ORDER_PAID: {
                    "title": "支付成功",
                    "content": "您的订单已支付成功，商家将尽快发货"
                },
                NotificationType.ORDER_SHIPPED: {
                    "title": "商品已发货",
                    "content": "您的订单已发货，请注意查收"
                },
                NotificationType.ORDER_DELIVERED: {
                    "title": "商品已送达",
                    "content": "您的订单已送达，请确认收货"
                }
            }

            template = notification_templates.get(notification_type)
            if template:
                notification_data = NotificationCreateSchema(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=template["title"],
                    content=template["content"],
                    related_id=order_id,
                    extra_data=extra_info
                )
                await NotificationService.create_notification(notification_data)
        except Exception:
            pass  # 通知失败不影响主流程

    @staticmethod
    async def send_realname_auth_notification(user_id: int, auth_id: int, notification_type: NotificationType, extra_info: dict = None) -> None:
        """发送实名认证相关通知"""
        try:
            notification_templates = {
                NotificationType.REALNAME_AUTH_APPROVED: {
                    "title": "实名认证已通过",
                    "content": "恭喜您，您的实名认证已通过审核"
                },
                NotificationType.REALNAME_AUTH_REJECTED: {
                    "title": "实名认证未通过",
                    "content": "很抱歉，您的实名认证未通过审核"
                }
            }

            template = notification_templates.get(notification_type)
            if template:
                # 如果有拒绝原因，添加到内容中
                content = template["content"]
                if extra_info and extra_info.get("reject_reason"):
                    content += f"，原因：{extra_info['reject_reason']}"
                
                notification_data = NotificationCreateSchema(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=template["title"],
                    content=content,
                    related_id=auth_id,
                    extra_data=extra_info
                )
                await NotificationService.create_notification(notification_data)
        except Exception:
            pass  # 通知失败不影响主流程

    @staticmethod
    async def send_merchant_audit_notification(user_id: int, merchant_id: int, notification_type: NotificationType, extra_info: dict = None) -> None:
        """发送商家审核相关通知"""
        try:
            notification_templates = {
                NotificationType.MERCHANT_APPROVED: {
                    "title": "商家审核已通过",
                    "content": "恭喜您，您的商家申请已通过审核，现在可以开始经营了"
                },
                NotificationType.MERCHANT_REJECTED: {
                    "title": "商家审核未通过",
                    "content": "很抱歉，您的商家申请未通过审核"
                }
            }

            template = notification_templates.get(notification_type)
            if template:
                # 如果有审核意见，添加到内容中
                content = template["content"]
                if extra_info and extra_info.get("comment"):
                    content += f"，审核意见：{extra_info['comment']}"
                
                notification_data = NotificationCreateSchema(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=template["title"],
                    content=content,
                    related_id=merchant_id,
                    extra_data=extra_info
                )
                await NotificationService.create_notification(notification_data)
        except Exception:
            pass  # 通知失败不影响主流程

    @staticmethod
    async def send_crew_application_notification(user_id: int, application_id: int, notification_type: NotificationType, extra_info: dict = None) -> None:
        """发送船员申请相关通知"""
        try:
            notification_templates = {
                NotificationType.CREW_APPLICATION_APPROVED: {
                    "title": "船员申请已通过",
                    "content": "恭喜您，您的船员申请已通过审核，现在可以开始工作了"
                },
                NotificationType.CREW_APPLICATION_REJECTED: {
                    "title": "船员申请未通过",
                    "content": "很抱歉，您的船员申请未通过审核"
                }
            }

            template = notification_templates.get(notification_type)
            if template:
                notification_data = NotificationCreateSchema(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=template["title"],
                    content=template["content"],
                    related_id=application_id,
                    extra_data=extra_info
                )
                await NotificationService.create_notification(notification_data)
        except Exception:
            pass  # 通知失败不影响主流程

    @staticmethod
    async def get_user_notifications(current_user: User, query_params: NotificationQuerySchema) -> ApiResponse:
        """获取用户通知列表"""
        try:
            # 构建查询
            query = Notification.filter(user=current_user)

            if query_params.notification_type:
                query = query.filter(notification_type=query_params.notification_type)
            if query_params.status:
                query = query.filter(status=query_params.status)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            notifications = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            notification_list = []
            for notification in notifications:
                notification_item = NotificationListItemSchema(
                    id=notification.id,
                    notification_type=notification.notification_type,
                    title=notification.title,
                    content=notification.content,
                    status=notification.status,
                    created_at=notification.created_at
                )
                notification_list.append(notification_item)

            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=notification_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取通知列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取通知列表失败: {str(e)}")

    @staticmethod
    async def mark_as_read(current_user: User, mark_data: NotificationMarkReadSchema) -> ApiResponse:
        """标记通知为已读"""
        try:
            # 更新通知状态
            updated_count = await Notification.filter(
                id__in=mark_data.notification_ids,
                user=current_user,
                status=NotificationStatus.UNREAD
            ).update(
                status=NotificationStatus.READ,
                read_at=datetime.now()
            )

            return ResponseHelper.success(
                {"updated_count": updated_count},
                f"已标记{updated_count}条通知为已读"
            )

        except Exception as e:
            return ResponseHelper.server_error(f"标记已读失败: {str(e)}")

    @staticmethod
    async def mark_all_as_read(current_user: User) -> ApiResponse:
        """标记所有通知为已读"""
        try:
            updated_count = await Notification.filter(
                user=current_user,
                status=NotificationStatus.UNREAD
            ).update(
                status=NotificationStatus.READ,
                read_at=datetime.now()
            )

            return ResponseHelper.success(
                {"updated_count": updated_count},
                f"已标记{updated_count}条通知为已读"
            )

        except Exception as e:
            return ResponseHelper.server_error(f"标记全部已读失败: {str(e)}")

    @staticmethod
    async def get_notification_stats(current_user: User) -> ApiResponse:
        """获取通知统计"""
        try:
            total_count = await Notification.filter(user=current_user).count()
            unread_count = await Notification.filter(
                user=current_user,
                status=NotificationStatus.UNREAD
            ).count()
            read_count = total_count - unread_count

            stats = NotificationStatsSchema(
                total_count=total_count,
                unread_count=unread_count,
                read_count=read_count
            )

            return ResponseHelper.success(stats, "获取通知统计成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取通知统计失败: {str(e)}")

    @staticmethod
    async def delete_notification(current_user: User, notification_id: int) -> ApiResponse:
        """删除通知"""
        try:
            notification = await Notification.filter(
                id=notification_id,
                user=current_user
            ).first()

            if not notification:
                return ResponseHelper.not_found("通知不存在")

            notification.status = NotificationStatus.DELETED
            await notification.save()

            return ResponseHelper.success(None, "通知已删除")

        except Exception as e:
            return ResponseHelper.server_error(f"删除通知失败: {str(e)}")


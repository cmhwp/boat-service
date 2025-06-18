from typing import Optional, List, Dict, Any
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.queryset import QuerySet
from tortoise import transactions
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import asyncio

from app.models.booking import BoatBooking, CrewRating, BookingStatus, PaymentStatus
from app.models.boat import Boat, BoatStatus
from app.models.user import User, UserRole
from app.models.merchant import Merchant, MerchantStatus
from app.models.crew import Crew, CrewStatus
from app.schemas.booking import (
    BookingCreateSchema,
    BookingStatusUpdateSchema,
    CrewAssignmentSchema,
    CrewRatingCreateSchema,
    BookingResponseSchema,
    BookingDetailSchema,
    BookingListItemSchema,
    BookingQuerySchema,
    BookingStatsSchema,
    BookingAvailabilityQuerySchema,
    BookingAvailabilityResponseSchema,
    CrewRatingResponseSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData


class BookingService:
    """预约服务类"""

    @staticmethod
    def _generate_booking_number() -> str:
        """生成预约单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"BK{timestamp}{random_suffix}"

    @staticmethod
    async def create_booking(current_user: User, booking_data: BookingCreateSchema) -> ApiResponse:
        """创建预约"""
        try:
            async with transactions.in_transaction():
                # 1. 验证船只存在且可用
                boat = await Boat.filter(
                    id=booking_data.boat_id,
                    status=BoatStatus.AVAILABLE
                ).select_related('merchant').first()
                
                if not boat:
                    return ResponseHelper.not_found("船只不存在或不可用")

                # 2. 验证商家状态
                if boat.merchant.status != MerchantStatus.ACTIVE:
                    return ResponseHelper.error("该船只所属商家未通过审核", 400)

                # 3. 验证载客量
                if booking_data.passenger_count > boat.capacity:
                    return ResponseHelper.error(f"乘客人数超过船只载客量限制（最多{boat.capacity}人）", 400)

                # 4. 检查时间冲突
                availability_check = await BookingService._check_boat_availability(
                    booking_data.boat_id,
                    booking_data.start_time,
                    booking_data.end_time
                )
                
                if not availability_check["available"]:
                    return ResponseHelper.error(availability_check["reason"], 400)

                # 5. 计算费用
                duration = (booking_data.end_time - booking_data.start_time).total_seconds() / 3600
                duration_hours = Decimal(str(round(duration, 1)))
                total_amount = boat.hourly_rate * duration_hours

                # 6. 创建预约
                booking = await BoatBooking.create(
                    booking_number=BookingService._generate_booking_number(),
                    user=current_user,
                    boat=boat,
                    merchant=boat.merchant,
                    start_time=booking_data.start_time,
                    end_time=booking_data.end_time,
                    duration_hours=duration_hours,
                    passenger_count=booking_data.passenger_count,
                    hourly_rate=boat.hourly_rate,
                    total_amount=total_amount,
                    contact_name=booking_data.contact_name,
                    contact_phone=booking_data.contact_phone,
                    user_notes=booking_data.user_notes,
                    status=BookingStatus.PENDING,
                    payment_status=PaymentStatus.UNPAID
                )

                booking_dict = await booking.to_dict()
                booking_response = BookingResponseSchema(**booking_dict)
                return ResponseHelper.created(booking_response, "预约创建成功，请等待商家确认")

        except IntegrityError:
            return ResponseHelper.error("预约创建失败，请稍后重试", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"创建预约失败: {str(e)}")

    @staticmethod
    async def _check_boat_availability(boat_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: Optional[int] = None) -> Dict[str, Any]:
        """检查船只可用性"""
        try:
            # 检查船只状态
            boat = await Boat.get_or_none(id=boat_id)
            if not boat:
                return {"available": False, "reason": "船只不存在"}
            
            if boat.status != BoatStatus.AVAILABLE:
                return {"available": False, "reason": f"船只当前状态为{boat.status}，不可预约"}

            # 检查时间冲突
            conflict_query = BoatBooking.filter(
                boat_id=boat_id,
                status__in=[BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS],
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            if exclude_booking_id:
                conflict_query = conflict_query.exclude(id=exclude_booking_id)
            
            conflicting_bookings = await conflict_query.all()
            
            if conflicting_bookings:
                return {
                    "available": False,
                    "reason": "该时间段已有其他预约",
                    "conflicting_bookings": [
                        {
                            "id": booking.id,
                            "booking_number": booking.booking_number,
                            "start_time": booking.start_time,
                            "end_time": booking.end_time
                        } for booking in conflicting_bookings
                    ]
                }

            return {"available": True, "reason": None, "conflicting_bookings": []}

        except Exception as e:
            return {"available": False, "reason": f"检查可用性失败: {str(e)}"}

    @staticmethod
    async def check_boat_availability(query_data: BookingAvailabilityQuerySchema) -> ApiResponse:
        """检查船只可用性（API接口）"""
        try:
            result = await BookingService._check_boat_availability(
                query_data.boat_id,
                query_data.start_time,
                query_data.end_time
            )
            
            response = BookingAvailabilityResponseSchema(**result)
            return ResponseHelper.success(response, "可用性检查完成")

        except Exception as e:
            return ResponseHelper.server_error(f"检查可用性失败: {str(e)}")

    @staticmethod
    async def get_user_bookings(current_user: User, query_params: BookingQuerySchema) -> ApiResponse:
        """获取用户预约列表"""
        try:
            # 构建查询
            query = BoatBooking.filter(user=current_user).select_related('boat')
            
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.start_date:
                query = query.filter(start_time__gte=query_params.start_date)
            if query_params.end_date:
                query = query.filter(end_time__lte=query_params.end_date)
            if query_params.boat_id:
                query = query.filter(boat_id=query_params.boat_id)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            bookings = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            booking_list = []
            for booking in bookings:
                await booking.fetch_related('boat')
                booking_item = BookingListItemSchema(
                    id=booking.id,
                    booking_number=booking.booking_number,
                    boat_name=booking.boat.name,
                    start_time=booking.start_time,
                    end_time=booking.end_time,
                    passenger_count=booking.passenger_count,
                    total_amount=float(booking.total_amount),
                    status=booking.status,
                    payment_status=booking.payment_status,
                    contact_name=booking.contact_name,
                    contact_phone=booking.contact_phone,
                    created_at=booking.created_at
                )
                booking_list.append(booking_item)
            
            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=booking_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取预约列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取预约列表失败: {str(e)}")

    @staticmethod
    async def get_merchant_bookings(current_user: User, query_params: BookingQuerySchema) -> ApiResponse:
        """获取商家预约列表"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user=current_user).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 构建查询
            query = BoatBooking.filter(merchant=merchant).select_related('boat', 'user', 'assigned_crew__user')
            
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.start_date:
                query = query.filter(start_time__gte=query_params.start_date)
            if query_params.end_date:
                query = query.filter(end_time__lte=query_params.end_date)
            if query_params.boat_id:
                query = query.filter(boat_id=query_params.boat_id)
            if query_params.user_id:
                query = query.filter(user_id=query_params.user_id)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            bookings = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            booking_list = []
            for booking in bookings:
                booking_dict = await booking.to_dict()
                booking_detail = BookingDetailSchema(**booking_dict)
                booking_list.append(booking_detail)
            
            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=booking_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取预约列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取预约列表失败: {str(e)}")

    @staticmethod
    async def get_booking_detail(current_user: User, booking_id: int) -> ApiResponse:
        """获取预约详情"""
        try:
            # 查询预约
            booking = await BoatBooking.filter(id=booking_id).select_related(
                'user', 'boat', 'merchant', 'assigned_crew__user'
            ).first()
            
            if not booking:
                return ResponseHelper.not_found("预约不存在")

            # 权限检查：只有预约用户或商家能查看详情
            if booking.user_id != current_user.id and booking.merchant.user_id != current_user.id:
                return ResponseHelper.forbidden("无权限查看此预约")

            # 获取评价信息
            crew_rating = None
            if booking.status == BookingStatus.COMPLETED:
                rating = await CrewRating.filter(booking=booking).first()
                if rating:
                    crew_rating = await rating.to_dict()

            booking_dict = await booking.to_dict()
            booking_dict["crew_rating"] = crew_rating
            
            booking_detail = BookingDetailSchema(**booking_dict)
            return ResponseHelper.success(booking_detail, "获取预约详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取预约详情失败: {str(e)}")

    @staticmethod
    async def update_booking_status(current_user: User, booking_id: int, status_data: BookingStatusUpdateSchema) -> ApiResponse:
        """更新预约状态（商家操作）"""
        try:
            async with transactions.in_transaction():
                # 检查用户是否是商家
                merchant = await Merchant.filter(user=current_user).first()
                if not merchant:
                    return ResponseHelper.forbidden("只有商家可以更新预约状态")

                # 获取预约
                booking = await BoatBooking.filter(id=booking_id, merchant=merchant).first()
                if not booking:
                    return ResponseHelper.not_found("预约不存在")

                # 状态转换验证
                current_status = booking.status
                new_status = status_data.status

                # 定义允许的状态转换
                allowed_transitions = {
                    BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.REJECTED],
                    BookingStatus.CONFIRMED: [BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED],
                    BookingStatus.IN_PROGRESS: [BookingStatus.COMPLETED],
                }

                if new_status not in allowed_transitions.get(current_status, []):
                    return ResponseHelper.error(f"不能从{current_status}状态转换为{new_status}状态", 400)

                # 更新状态
                booking.status = new_status
                booking.merchant_notes = status_data.merchant_notes
                
                now = datetime.now()
                if new_status == BookingStatus.CONFIRMED:
                    booking.confirmed_at = now
                elif new_status == BookingStatus.COMPLETED:
                    booking.completed_at = now
                    # 释放船只资源
                    await Boat.filter(id=booking.boat_id).update(status=BoatStatus.AVAILABLE)
                elif new_status in [BookingStatus.CANCELLED, BookingStatus.REJECTED]:
                    booking.cancelled_at = now
                    booking.cancel_reason = status_data.cancel_reason

                await booking.save()

                booking_dict = await booking.to_dict()
                booking_response = BookingResponseSchema(**booking_dict)
                return ResponseHelper.success(booking_response, f"预约状态已更新为{new_status}")

        except Exception as e:
            return ResponseHelper.server_error(f"更新预约状态失败: {str(e)}")

    @staticmethod
    async def assign_crew(current_user: User, assignment_data: CrewAssignmentSchema) -> ApiResponse:
        """派单给船员"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user=current_user).first()
            if not merchant:
                return ResponseHelper.forbidden("只有商家可以派单")

            # 获取预约
            booking = await BoatBooking.filter(id=assignment_data.booking_id, merchant=merchant).first()
            if not booking:
                return ResponseHelper.not_found("预约不存在")

            # 检查预约状态
            if booking.status != BookingStatus.CONFIRMED:
                return ResponseHelper.error("只有已确认的预约才能派单", 400)

            # 检查船员
            crew = await Crew.filter(
                id=assignment_data.crew_id,
                merchant=merchant,
                status=CrewStatus.ACTIVE
            ).first()
            
            if not crew:
                return ResponseHelper.not_found("船员不存在或不可用")

            # 检查船员时间冲突
            conflicting_assignments = await BoatBooking.filter(
                assigned_crew=crew,
                status__in=[BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS],
                start_time__lt=booking.end_time,
                end_time__gt=booking.start_time
            ).exclude(id=booking.id)

            if await conflicting_assignments.exists():
                return ResponseHelper.error("该船员在此时间段已有其他任务", 400)

            # 分配船员
            booking.assigned_crew = crew
            if assignment_data.notes:
                booking.merchant_notes = assignment_data.notes
            await booking.save()

            booking_dict = await booking.to_dict()
            booking_response = BookingResponseSchema(**booking_dict)
            return ResponseHelper.success(booking_response, "船员派单成功")

        except Exception as e:
            return ResponseHelper.server_error(f"船员派单失败: {str(e)}")

    @staticmethod
    async def create_crew_rating(current_user: User, rating_data: CrewRatingCreateSchema) -> ApiResponse:
        """创建船员评价"""
        try:
            # 获取预约
            booking = await BoatBooking.filter(
                id=rating_data.booking_id,
                user=current_user,
                status=BookingStatus.COMPLETED
            ).select_related('assigned_crew').first()
            
            if not booking:
                return ResponseHelper.not_found("预约不存在或未完成")

            if not booking.assigned_crew:
                return ResponseHelper.error("该预约没有指派船员", 400)

            # 检查是否已评价
            existing_rating = await CrewRating.filter(booking=booking).first()
            if existing_rating:
                return ResponseHelper.error("您已经评价过此次服务", 400)

            # 创建评价
            rating = await CrewRating.create(
                booking=booking,
                user=current_user,
                crew=booking.assigned_crew,
                rating=rating_data.rating,
                comment=rating_data.comment
            )

            # 更新船员平均评分
            await BookingService._update_crew_rating(booking.assigned_crew.id)

            rating_dict = await rating.to_dict()
            rating_response = CrewRatingResponseSchema(**rating_dict)
            return ResponseHelper.created(rating_response, "评价提交成功")

        except Exception as e:
            return ResponseHelper.server_error(f"提交评价失败: {str(e)}")

    @staticmethod
    async def _update_crew_rating(crew_id: int):
        """更新船员平均评分"""
        try:
            ratings = await CrewRating.filter(crew_id=crew_id).all()
            if ratings:
                total_rating = sum(rating.rating for rating in ratings)
                average_rating = Decimal(str(total_rating / len(ratings)))
                await Crew.filter(id=crew_id).update(rating=average_rating)
        except Exception:
            pass  # 忽略评分更新错误

    @staticmethod
    async def get_booking_stats(current_user: User) -> ApiResponse:
        """获取预约统计数据（商家）"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user=current_user).first()
            if not merchant:
                return ResponseHelper.forbidden("只有商家可以查看统计数据")

            # 统计各状态预约数量
            total_bookings = await BoatBooking.filter(merchant=merchant).count()
            pending_bookings = await BoatBooking.filter(merchant=merchant, status=BookingStatus.PENDING).count()
            confirmed_bookings = await BoatBooking.filter(merchant=merchant, status=BookingStatus.CONFIRMED).count()
            completed_bookings = await BoatBooking.filter(merchant=merchant, status=BookingStatus.COMPLETED).count()
            cancelled_bookings = await BoatBooking.filter(
                merchant=merchant,
                status__in=[BookingStatus.CANCELLED, BookingStatus.REJECTED]
            ).count()

            # 计算总收入（已完成的预约）
            completed_booking_objects = await BoatBooking.filter(
                merchant=merchant,
                status=BookingStatus.COMPLETED
            ).all()
            total_revenue = sum(float(booking.total_amount) for booking in completed_booking_objects)

            # 计算平均评分
            ratings = await CrewRating.filter(crew__merchant=merchant).all()
            average_rating = 0.0
            if ratings:
                total_rating = sum(rating.rating for rating in ratings)
                average_rating = round(total_rating / len(ratings), 2)

            stats = BookingStatsSchema(
                total_bookings=total_bookings,
                pending_bookings=pending_bookings,
                confirmed_bookings=confirmed_bookings,
                completed_bookings=completed_bookings,
                cancelled_bookings=cancelled_bookings,
                total_revenue=total_revenue,
                average_rating=average_rating
            )

            return ResponseHelper.success(stats, "获取统计数据成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取统计数据失败: {str(e)}")

    @staticmethod
    async def cancel_booking(current_user: User, booking_id: int, cancel_reason: Optional[str] = None) -> ApiResponse:
        """取消预约（用户操作）"""
        try:
            # 获取预约
            booking = await BoatBooking.filter(id=booking_id, user=current_user).first()
            if not booking:
                return ResponseHelper.not_found("预约不存在")

            # 检查预约状态
            if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
                return ResponseHelper.error("当前状态的预约不能取消", 400)

            # 检查取消时间限制（开始前2小时内不能取消）
            if booking.start_time <= datetime.now() + timedelta(hours=2):
                return ResponseHelper.error("距离预约开始时间不足2小时，无法取消", 400)

            # 取消预约
            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = datetime.now()
            booking.cancel_reason = cancel_reason or "用户主动取消"
            await booking.save()

            booking_dict = await booking.to_dict()
            booking_response = BookingResponseSchema(**booking_dict)
            return ResponseHelper.success(booking_response, "预约已取消")

        except Exception as e:
            return ResponseHelper.server_error(f"取消预约失败: {str(e)}")

    @staticmethod
    async def auto_cancel_expired_bookings() -> ApiResponse:
        """自动取消20分钟内未确认的预约"""
        try:
            current_time = datetime.now()
            # 计算20分钟前的时间
            twenty_minutes_ago = current_time - timedelta(minutes=20)
            
            # 查找状态为待确认且创建时间超过20分钟的预约
            expired_bookings = await BoatBooking.filter(
                status=BookingStatus.PENDING,
                created_at__lte=twenty_minutes_ago
            ).select_related('user', 'boat', 'merchant')
            
            if not expired_bookings:
                return ResponseHelper.success({"cancelled_count": 0}, "没有需要取消的预约")
            
            cancelled_count = 0
            cancelled_bookings = []
            
            for booking in expired_bookings:
                try:
                    # 更新预约状态
                    booking.status = BookingStatus.CANCELLED
                    booking.cancelled_at = current_time
                    booking.cancel_reason = "商家超过20分钟未确认，系统自动取消"
                    await booking.save()
                    
                    cancelled_count += 1
                    wait_minutes = int((current_time - booking.created_at).total_seconds() / 60)
                    cancelled_bookings.append({
                        "booking_id": booking.id,
                        "booking_number": booking.booking_number,
                        "user_name": booking.user.username if booking.user else None,
                        "boat_name": booking.boat.name if booking.boat else None,
                        "merchant_name": booking.merchant.merchant_name if booking.merchant else None,
                        "created_at": booking.created_at,
                        "start_time": booking.start_time,
                        "cancelled_at": booking.cancelled_at,
                        "wait_minutes": wait_minutes
                    })
                    
                except Exception as e:
                    # 记录单个预约取消失败，但继续处理其他预约
                    continue
            
            result = {
                "cancelled_count": cancelled_count,
                "cancelled_bookings": cancelled_bookings,
                "total_expired": len(expired_bookings)
            }
            
            return ResponseHelper.success(result, f"成功自动取消 {cancelled_count} 个超过20分钟未确认的预约")

        except Exception as e:
            return ResponseHelper.server_error(f"自动取消预约失败: {str(e)}") 
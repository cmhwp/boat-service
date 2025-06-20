from typing import Optional, List
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.queryset import QuerySet
from datetime import datetime
from app.models.boat import Boat, BoatStatus, BoatType
from app.models.merchant import Merchant, MerchantStatus
from app.models.user import User, UserRole
from app.schemas.boat import (
    BoatCreateSchema,
    BoatUpdateSchema,
    BoatResponseSchema,
    BoatDetailSchema,
    BoatListItemSchema,
    BoatStatusUpdateSchema,
    AdminBoatQuerySchema,
    AdminBoatOperationSchema,
    AdminBoatListItemSchema,
    AdminBoatDetailSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData


class BoatService:
    """船只服务类"""

    @staticmethod
    async def create_boat(current_user: User, boat_data: BoatCreateSchema) -> ApiResponse:
        """创建船只"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id, status=MerchantStatus.ACTIVE).first()
            if not merchant:
                return ResponseHelper.forbidden("只有审核通过的商家才能添加船只")

            # 检查船只证书号是否已存在
            existing_boat = await Boat.filter(license_number=boat_data.license_number).first()
            if existing_boat:
                return ResponseHelper.error("船只证书号已存在", 400)

            # 创建船只
            boat = await Boat.create(
                merchant_id=merchant.id,
                name=boat_data.name,
                license_number=boat_data.license_number,
                boat_type=boat_data.boat_type,
                capacity=boat_data.capacity,
                hourly_rate=boat_data.hourly_rate,
                description=boat_data.description,
                images=boat_data.images or [],
                current_location=boat_data.current_location
            )

            boat_response = BoatResponseSchema.from_orm(boat)
            return ResponseHelper.created(boat_response, "船只添加成功")

        except IntegrityError:
            return ResponseHelper.error("数据完整性错误，船只证书号可能已存在", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"添加船只失败: {str(e)}")

    @staticmethod
    async def get_my_boats(current_user: User, page: int = 1, page_size: int = 10, 
                          status: Optional[BoatStatus] = None) -> ApiResponse:
        """获取我的船只列表"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 构建查询
            query = Boat.filter(merchant_id=merchant.id)
            if status:
                query = query.filter(status=status)

            # 分页查询
            offset = (page - 1) * page_size
            boats = await query.offset(offset).limit(page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            boat_list = [BoatListItemSchema.from_orm(boat) for boat in boats]
            
            total_pages = (total + page_size - 1) // page_size
            paginated_data = PaginatedData(
                items=boat_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取船只列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取船只列表失败: {str(e)}")

    @staticmethod
    async def get_boat_detail(current_user: User, boat_id: int) -> ApiResponse:
        """获取船只详情"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取船只详情
            boat = await Boat.filter(id=boat_id, merchant_id=merchant.id).select_related('merchant').first()
            if not boat:
                return ResponseHelper.not_found("船只不存在")

            # 使用 to_dict 方法正确转换数据
            boat_dict = await boat.to_dict()
            boat_detail = BoatDetailSchema(**boat_dict)
            return ResponseHelper.success(boat_detail, "获取船只详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取船只详情失败: {str(e)}")

    @staticmethod
    async def update_boat(current_user: User, boat_id: int, boat_data: BoatUpdateSchema) -> ApiResponse:
        """更新船只信息"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取船只
            boat = await Boat.filter(id=boat_id, merchant_id=merchant.id).first()
            if not boat:
                return ResponseHelper.not_found("船只不存在")

            # 更新字段
            update_data = boat_data.dict(exclude_unset=True)
            if update_data:
                await boat.update_from_dict(update_data)
                await boat.save()

            boat_response = BoatResponseSchema.from_orm(boat)
            return ResponseHelper.success(boat_response, "船只信息更新成功")

        except IntegrityError:
            return ResponseHelper.error("数据完整性错误", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"更新船只信息失败: {str(e)}")

    @staticmethod
    async def delete_boat(current_user: User, boat_id: int) -> ApiResponse:
        """删除船只"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取船只
            boat = await Boat.filter(id=boat_id, merchant_id=merchant.id).first()
            if not boat:
                return ResponseHelper.not_found("船只不存在")

            # 检查船只是否在使用中
            if boat.status == BoatStatus.IN_USE:
                return ResponseHelper.error("船只使用中，无法删除", 400)

            await boat.delete()
            return ResponseHelper.success({"deleted": True}, "船只删除成功")

        except Exception as e:
            return ResponseHelper.server_error(f"删除船只失败: {str(e)}")

    @staticmethod
    async def update_boat_status(current_user: User, boat_id: int, status_data: BoatStatusUpdateSchema) -> ApiResponse:
        """更新船只状态"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取船只
            boat = await Boat.filter(id=boat_id, merchant_id=merchant.id).first()
            if not boat:
                return ResponseHelper.not_found("船只不存在")

            # 更新状态
            boat.status = status_data.status
            if status_data.current_location:
                boat.current_location = status_data.current_location
            await boat.save()

            boat_response = BoatResponseSchema.from_orm(boat)
            return ResponseHelper.success(boat_response, "船只状态更新成功")

        except Exception as e:
            return ResponseHelper.server_error(f"更新船只状态失败: {str(e)}")

    @staticmethod
    async def get_available_boats(page: int = 1, page_size: int = 10, 
                                 boat_type: Optional[BoatType] = None,
                                 min_capacity: Optional[int] = None,
                                 max_hourly_rate: Optional[float] = None) -> ApiResponse:
        """获取可用船只列表（用户端）"""
        try:
            # 构建查询条件
            query = Boat.filter(status=BoatStatus.AVAILABLE).select_related('merchant')
            
            if boat_type:
                query = query.filter(boat_type=boat_type)
            if min_capacity:
                query = query.filter(capacity__gte=min_capacity)
            if max_hourly_rate:
                query = query.filter(hourly_rate__lte=max_hourly_rate)

            # 只显示审核通过的商家的船只
            query = query.filter(merchant__status=MerchantStatus.ACTIVE)

            # 分页查询
            offset = (page - 1) * page_size
            boats = await query.offset(offset).limit(page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            boat_list = []
            for boat in boats:
                boat_dict = await boat.to_dict()
                boat_list.append(BoatListItemSchema(**boat_dict))
            
            total_pages = (total + page_size - 1) // page_size
            paginated_data = PaginatedData(
                items=boat_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取可用船只列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取可用船只列表失败: {str(e)}")

    @staticmethod
    async def get_public_boat_detail(boat_id: int) -> ApiResponse:
        """获取船只公开详情（用户端）"""
        try:
            # 获取船只详情
            boat = await Boat.filter(
                id=boat_id,
                status=BoatStatus.AVAILABLE
            ).select_related('merchant').first()
            
            if not boat:
                return ResponseHelper.not_found("船只不存在或不可用")

            # 使用 to_dict 方法正确转换数据
            boat_dict = await boat.to_dict()
            boat_detail = BoatDetailSchema(**boat_dict)
            return ResponseHelper.success(boat_detail, "获取船只详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取船只详情失败: {str(e)}")

    # =================== 管理员相关方法 ===================

    @staticmethod
    async def admin_get_all_boats(current_user: User, query_params: AdminBoatQuerySchema) -> ApiResponse:
        """管理员获取所有船只列表"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            # 构建查询
            query = Boat.all().select_related('merchant')
            
            if query_params.merchant_id:
                query = query.filter(merchant_id=query_params.merchant_id)
            if query_params.boat_type:
                query = query.filter(boat_type=query_params.boat_type)
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.name:
                query = query.filter(name__icontains=query_params.name)
            if query_params.license_number:
                query = query.filter(license_number__icontains=query_params.license_number)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            boats = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            boat_list = []
            for boat in boats:
                # 获取商家名称
                merchant_name = boat.merchant.merchant_name if boat.merchant else "未知商家"
                
                # 统计预约数据
                from app.models.booking import BoatBooking
                booking_count = await BoatBooking.filter(boat_id=boat.id).count()
                total_income_data = await BoatBooking.filter(
                    boat_id=boat.id,
                    status__in=['completed']
                ).values('total_amount')
                total_income = sum(float(booking['total_amount']) for booking in total_income_data)
                
                boat_data = {
                    "id": boat.id,
                    "merchant_id": boat.merchant_id,
                    "name": boat.name,
                    "boat_type": boat.boat_type,
                    "capacity": boat.capacity,
                    "hourly_rate": float(boat.hourly_rate),
                    "status": boat.status,
                    "current_location": boat.current_location,
                    "images": boat.images,
                    "created_at": boat.created_at,
                    "merchant_name": merchant_name,
                    "booking_count": booking_count,
                    "total_income": total_income
                }
                
                boat_list.append(boat_data)
            
            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=boat_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取船只列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取船只列表失败: {str(e)}")

    @staticmethod
    async def admin_get_boat_detail(current_user: User, boat_id: int) -> ApiResponse:
        """管理员获取船只详情"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            # 获取船只详情
            boat = await Boat.filter(id=boat_id).select_related('merchant').first()
            if not boat:
                return ResponseHelper.not_found("船只不存在")

            # 获取预约统计数据
            from app.models.booking import BoatBooking
            booking_count = await BoatBooking.filter(boat_id=boat.id).count()
            total_income_data = await BoatBooking.filter(
                boat_id=boat.id,
                status__in=['completed']
            ).values('total_amount')
            total_income = sum(float(booking['total_amount']) for booking in total_income_data)
            
            # 获取最近的预约记录
            recent_bookings = await BoatBooking.filter(
                boat_id=boat.id
            ).select_related('user').order_by('-created_at').limit(5)
            
            recent_booking_data = []
            for booking in recent_bookings:
                booking_data = {
                    "id": booking.id,
                    "user_name": booking.user.nickname or booking.user.username if booking.user else "未知用户",
                    "start_time": booking.start_time,
                    "end_time": booking.end_time,
                    "status": booking.status,
                    "total_amount": float(booking.total_amount)
                }
                recent_booking_data.append(booking_data)
            
            # 转换为详情数据
            boat_dict = await boat.to_dict()
            boat_dict.update({
                "booking_count": booking_count,
                "total_income": total_income,
                "recent_bookings": recent_booking_data
            })
            
            boat_detail = AdminBoatDetailSchema(**boat_dict)
            return ResponseHelper.success(boat_detail, "获取船只详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取船只详情失败: {str(e)}")

    @staticmethod
    async def admin_operate_boat(current_user: User, boat_id: int, operation_data: AdminBoatOperationSchema) -> ApiResponse:
        """管理员操作船只"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            boat = await Boat.get(id=boat_id)
            
            if operation_data.operation == "suspend":
                # 暂停船只
                if boat.status == BoatStatus.INACTIVE:
                    return ResponseHelper.error("船只已被暂停", 400)
                
                boat.status = BoatStatus.INACTIVE
                
            elif operation_data.operation == "activate":
                # 激活船只
                if boat.status == BoatStatus.AVAILABLE:
                    return ResponseHelper.error("船只已是可用状态", 400)
                
                boat.status = BoatStatus.AVAILABLE
                
            elif operation_data.operation == "maintenance":
                # 设置维护状态
                boat.status = BoatStatus.MAINTENANCE
            
            # 记录操作日志（这里简化处理，实际应该有专门的日志表）
            # 可以在船只描述中添加管理员操作记录
            operation_log = f"\n[管理员操作 {datetime.now().strftime('%Y-%m-%d %H:%M')}] {operation_data.operation}: {operation_data.reason}"
            if operation_data.notes:
                operation_log += f" 备注：{operation_data.notes}"
            
            boat.description = (boat.description or "") + operation_log
            await boat.save()
            
            boat_response = BoatResponseSchema.from_orm(boat)
            return ResponseHelper.success(boat_response, f"船只操作成功")

        except DoesNotExist:
            return ResponseHelper.not_found("船只不存在")
        except Exception as e:
            return ResponseHelper.server_error(f"船只操作失败: {str(e)}")

    @staticmethod
    async def admin_get_boat_statistics(current_user: User) -> ApiResponse:
        """管理员获取船只统计"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")

            # 获取所有船只
            all_boats = await Boat.all()
            
            stats = {
                "total_boats": len(all_boats),
                "available_boats": 0,
                "in_use_boats": 0,
                "maintenance_boats": 0,
                "inactive_boats": 0,
                "total_bookings": 0,
                "total_revenue": 0.0
            }
            
            # 统计各状态船只数量
            for boat in all_boats:
                if boat.status == BoatStatus.AVAILABLE:
                    stats["available_boats"] += 1
                elif boat.status == BoatStatus.IN_USE:
                    stats["in_use_boats"] += 1
                elif boat.status == BoatStatus.MAINTENANCE:
                    stats["maintenance_boats"] += 1
                elif boat.status == BoatStatus.INACTIVE:
                    stats["inactive_boats"] += 1
            
            # 统计预约和收入数据
            from app.models.booking import BoatBooking
            all_bookings = await BoatBooking.filter(status='completed')
            stats["total_bookings"] = len(all_bookings)
            stats["total_revenue"] = sum(float(booking.total_amount) for booking in all_bookings)
            
            return ResponseHelper.success(stats, "获取船只统计成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取船只统计失败: {str(e)}") 
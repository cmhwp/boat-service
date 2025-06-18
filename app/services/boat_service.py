from typing import Optional, List
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.queryset import QuerySet
from app.models.boat import Boat, BoatStatus, BoatType
from app.models.merchant import Merchant, MerchantStatus
from app.models.user import User, UserRole
from app.schemas.boat import (
    BoatCreateSchema,
    BoatUpdateSchema,
    BoatResponseSchema,
    BoatDetailSchema,
    BoatListItemSchema,
    BoatStatusUpdateSchema
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
        """获取公开船只详情（用户端）"""
        try:
            boat = await Boat.filter(
                id=boat_id, 
                status=BoatStatus.AVAILABLE,
                merchant__status=MerchantStatus.ACTIVE
            ).select_related('merchant').first()
            
            if not boat:
                return ResponseHelper.not_found("船只不存在或不可用")

            boat_dict = await boat.to_dict()
            boat_detail = BoatDetailSchema(**boat_dict)
            return ResponseHelper.success(boat_detail, "获取船只详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取船只详情失败: {str(e)}") 
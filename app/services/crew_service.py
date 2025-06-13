from fastapi import HTTPException, status
from tortoise.exceptions import IntegrityError
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.crew import CrewApplication, Crew, CrewApplicationStatus, CrewStatus
from app.models.merchant import Merchant, MerchantStatus
from app.models.user import User, UserRole
from app.schemas.crew import (
    CrewApplicationSchema,
    CrewApplicationResponseSchema,
    CrewApplicationDetailSchema,
    CrewApplicationHandleSchema,
    CrewResponseSchema,
    CrewDetailSchema,
    CrewUpdateSchema,
    CrewListItemSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData


class CrewService:
    """船员服务类"""

    @staticmethod
    async def apply_crew(user: User, apply_data: CrewApplicationSchema) -> ApiResponse[CrewApplicationResponseSchema]:
        """申请加入商家成为船员"""
        try:
            # 检查商家是否存在且状态为active
            merchant = await Merchant.get_or_none(id=apply_data.merchant_id)
            if not merchant:
                return ResponseHelper.not_found("商家不存在")
            
            if merchant.status != MerchantStatus.ACTIVE:
                return ResponseHelper.error("该商家未通过审核，无法申请加入", 400)
            
            # 检查用户是否已经是船员
            existing_crew = await Crew.get_or_none(user=user)
            if existing_crew:
                return ResponseHelper.error("您已经是船员，无法重复申请", 400)
            
            # 检查是否已经向该商家申请过
            existing_application = await CrewApplication.get_or_none(
                user=user, 
                merchant=merchant
            )
            if existing_application:
                if existing_application.status == CrewApplicationStatus.PENDING:
                    return ResponseHelper.error("您已经向该商家申请过，请等待处理", 400)
                elif existing_application.status == CrewApplicationStatus.APPROVED:
                    return ResponseHelper.error("您的申请已通过，请勿重复申请", 400)
            
            # 创建或更新申请
            if existing_application and existing_application.status == CrewApplicationStatus.REJECTED:
                existing_application.status = CrewApplicationStatus.PENDING
                existing_application.apply_time = datetime.now()
                existing_application.handle_time = None
                await existing_application.save()
                application = existing_application
            else:
                application = await CrewApplication.create(
                    user=user,
                    merchant=merchant,
                    status=CrewApplicationStatus.PENDING
                )
            
            application_response = CrewApplicationResponseSchema.from_orm(application)
            return ResponseHelper.created(application_response, "船员申请提交成功，等待商家处理")
            
        except IntegrityError as e:
            return ResponseHelper.error("申请失败，可能已经存在相同申请", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"申请船员失败: {str(e)}")

    @staticmethod
    async def handle_crew_application(merchant_user: User, handle_data: CrewApplicationHandleSchema) -> ApiResponse[CrewApplicationResponseSchema]:
        """处理船员申请（商家操作）"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.get_or_none(user=merchant_user)
            if not merchant:
                return ResponseHelper.forbidden("您不是商家，无权限执行此操作")
            
            if merchant.status != MerchantStatus.ACTIVE:
                return ResponseHelper.error("您的商家账户未通过审核", 400)
            
            # 获取申请记录
            application = await CrewApplication.get_or_none(
                id=handle_data.application_id,
                merchant=merchant
            )
            if not application:
                return ResponseHelper.not_found("申请记录不存在")
            
            if application.status != CrewApplicationStatus.PENDING:
                return ResponseHelper.error("该申请已经处理过了", 400)
            
            # 更新申请状态
            application.status = handle_data.status
            application.handle_time = datetime.now()
            await application.save()
            
            # 如果同意申请，创建船员记录
            if handle_data.status == CrewApplicationStatus.APPROVED:
                # 检查船员证号是否已存在
                if handle_data.boat_license:
                    existing_crew = await Crew.get_or_none(boat_license=handle_data.boat_license)
                    if existing_crew:
                        return ResponseHelper.error("船员证号已存在", 400)
                
                # 创建船员记录
                crew = await Crew.create(
                    user=await application.user,
                    merchant=merchant,
                    boat_license=handle_data.boat_license,
                    status=CrewStatus.ACTIVE
                )
                
                # 更新用户角色
                user = await application.user
                # 如果用户当前不是商家，则设置为船员
                if user.role not in [UserRole.MERCHANT, UserRole.ADMIN]:
                    user.role = UserRole.CREW
                    await user.save()
            
            application_response = CrewApplicationResponseSchema.from_orm(application)
            message = "申请已同意，船员已成功加入" if handle_data.status == CrewApplicationStatus.APPROVED else "申请已拒绝"
            return ResponseHelper.success(application_response, message)
            
        except IntegrityError as e:
            return ResponseHelper.error("处理申请失败，船员证号可能已存在", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"处理船员申请失败: {str(e)}")

    @staticmethod
    async def get_crew_applications(merchant_user: User, page: int = 1, page_size: int = 10) -> ApiResponse[PaginatedData[CrewApplicationDetailSchema]]:
        """获取商家的船员申请列表"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.get_or_none(user=merchant_user)
            if not merchant:
                return ResponseHelper.forbidden("您不是商家，无权限执行此操作")
            
            # 查询申请列表
            query = CrewApplication.filter(merchant=merchant).prefetch_related('user', 'merchant')
            
            # 计算总数
            total = await query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            applications = await query.offset(offset).limit(page_size).order_by('-apply_time')
            
            # 转换为响应格式
            application_list = []
            for app in applications:
                app_dict = await app.to_dict()
                application_list.append(CrewApplicationDetailSchema(**app_dict))
            
            paginated_data = PaginatedData(
                items=application_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
            
            return ResponseHelper.success(paginated_data, "获取申请列表成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取申请列表失败: {str(e)}")

    @staticmethod
    async def get_my_crew_applications(user: User, page: int = 1, page_size: int = 10) -> ApiResponse[PaginatedData[CrewApplicationDetailSchema]]:
        """获取我的船员申请列表"""
        try:
            # 查询申请列表
            query = CrewApplication.filter(user=user).prefetch_related('user', 'merchant')
            
            # 计算总数
            total = await query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            applications = await query.offset(offset).limit(page_size).order_by('-apply_time')
            
            # 转换为响应格式
            application_list = []
            for app in applications:
                app_dict = await app.to_dict()
                application_list.append(CrewApplicationDetailSchema(**app_dict))
            
            paginated_data = PaginatedData(
                items=application_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
            
            return ResponseHelper.success(paginated_data, "获取我的申请列表成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取申请列表失败: {str(e)}")

    @staticmethod
    async def get_crew_list(merchant_user: User, page: int = 1, page_size: int = 10) -> ApiResponse[PaginatedData[CrewListItemSchema]]:
        """获取商家的船员列表"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.get_or_none(user=merchant_user)
            if not merchant:
                return ResponseHelper.forbidden("您不是商家，无权限执行此操作")
            
            # 查询船员列表
            query = Crew.filter(merchant=merchant).prefetch_related('user', 'merchant')
            
            # 计算总数
            total = await query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            crews = await query.offset(offset).limit(page_size).order_by('-join_time')
            
            # 转换为响应格式
            crew_list = [CrewListItemSchema.from_orm(crew) for crew in crews]
            
            paginated_data = PaginatedData(
                items=crew_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
            
            return ResponseHelper.success(paginated_data, "获取船员列表成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取船员列表失败: {str(e)}")

    @staticmethod
    async def get_crew_detail(crew_id: int) -> ApiResponse[CrewDetailSchema]:
        """获取船员详情"""
        try:
            crew = await Crew.get_or_none(id=crew_id).prefetch_related('user', 'merchant')
            if not crew:
                return ResponseHelper.not_found("船员不存在")
            
            crew_dict = await crew.to_dict()
            crew_detail = CrewDetailSchema(**crew_dict)
            return ResponseHelper.success(crew_detail, "获取船员详情成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取船员详情失败: {str(e)}")

    @staticmethod
    async def update_crew(merchant_user: User, crew_id: int, update_data: CrewUpdateSchema) -> ApiResponse[CrewResponseSchema]:
        """更新船员信息（商家操作）"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.get_or_none(user=merchant_user)
            if not merchant:
                return ResponseHelper.forbidden("您不是商家，无权限执行此操作")
            
            # 获取船员信息
            crew = await Crew.get_or_none(id=crew_id, merchant=merchant)
            if not crew:
                return ResponseHelper.not_found("船员不存在或不属于您的商家")
            
            # 更新船员信息
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(crew, field, value)
            
            await crew.save()
            crew_response = CrewResponseSchema.from_orm(crew)
            return ResponseHelper.success(crew_response, "船员信息更新成功")
            
        except IntegrityError as e:
            return ResponseHelper.error("更新失败，船员证号可能已存在", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"更新船员信息失败: {str(e)}")

    @staticmethod
    async def get_my_crew_info(user: User) -> ApiResponse[CrewDetailSchema]:
        """获取我的船员信息"""
        try:
            crew = await Crew.get_or_none(user=user).prefetch_related('user', 'merchant')
            if not crew:
                return ResponseHelper.not_found("您不是船员，请先申请成为船员")
            
            crew_dict = await crew.to_dict()
            crew_detail = CrewDetailSchema(**crew_dict)
            return ResponseHelper.success(crew_detail, "获取船员信息成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取船员信息失败: {str(e)}")

    @staticmethod
    async def resign_crew(user: User) -> ApiResponse[dict]:
        """船员离职"""
        try:
            crew = await Crew.get_or_none(user=user)
            if not crew:
                return ResponseHelper.not_found("您不是船员")
            
            # 更新船员状态为不活跃
            crew.status = CrewStatus.INACTIVE
            await crew.save()
            
            # 如果用户只是船员（不是商家），则将角色改回普通用户
            if user.role == UserRole.CREW:
                user.role = UserRole.USER
                await user.save()
            
            return ResponseHelper.success({"status": "resigned"}, "离职成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"离职失败: {str(e)}")
from fastapi import HTTPException, status
from tortoise.exceptions import IntegrityError
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.merchant import Merchant, MerchantAudit, MerchantStatus, AuditResult
from app.models.user import User, UserRole
from app.schemas.merchant import (
    MerchantApplySchema,
    MerchantUpdateSchema,
    MerchantResponseSchema,
    MerchantAuditSchema,
    MerchantAuditResponseSchema,
    MerchantListItemSchema,
    MerchantDetailSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData


class MerchantService:
    """商家服务类"""

    @staticmethod
    async def apply_merchant(user: User, apply_data: MerchantApplySchema) -> ApiResponse[MerchantResponseSchema]:
        """申请成为商家"""
        try:
            # 检查用户是否已经申请过商家
            existing_merchant = await Merchant.get_or_none(user=user)
            if existing_merchant:
                return ResponseHelper.error("您已经申请过商家，请勿重复申请", 400)
            
            # 检查商家名称和营业执照号是否已存在
            name_exists = await Merchant.get_or_none(merchant_name=apply_data.merchant_name)
            if name_exists:
                return ResponseHelper.error("商家名称已存在", 400)
            
            license_exists = await Merchant.get_or_none(license_number=apply_data.license_number)
            if license_exists:
                return ResponseHelper.error("营业执照号已存在", 400)
            
            # 创建商家申请
            merchant = await Merchant.create(
                user=user,
                merchant_name=apply_data.merchant_name,
                license_number=apply_data.license_number,
                license_image=apply_data.license_image,
                contact_phone=apply_data.contact_phone,
                address=apply_data.address,
                description=apply_data.description,
                status=MerchantStatus.PENDING
            )
            
            merchant_response = MerchantResponseSchema.from_orm(merchant)
            return ResponseHelper.created(merchant_response, "商家申请提交成功，等待审核")
            
        except IntegrityError as e:
            return ResponseHelper.error("数据完整性错误，商家名称或营业执照号已存在", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"申请商家失败: {str(e)}")

    @staticmethod
    async def audit_merchant(admin: User, audit_data: MerchantAuditSchema) -> ApiResponse[MerchantAuditResponseSchema]:
        """审核商家申请"""
        try:
            # 检查管理员权限
            if admin.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("无权限执行此操作")
            
            # 获取商家信息
            merchant = await Merchant.get_or_none(id=audit_data.merchant_id)
            if not merchant:
                return ResponseHelper.not_found("商家不存在")
            
            # 检查商家状态
            if merchant.status != MerchantStatus.PENDING:
                return ResponseHelper.error("该商家已经审核过了", 400)
            
            # 创建审核记录
            audit_record = await MerchantAudit.create(
                merchant=merchant,
                admin=admin,
                audit_result=audit_data.audit_result,
                comment=audit_data.comment
            )
            
            # 更新商家状态
            if audit_data.audit_result == AuditResult.APPROVED:
                merchant.status = MerchantStatus.ACTIVE
                # 更新用户角色为商家
                user = await merchant.user
                user.role = UserRole.MERCHANT
                await user.save()
            else:
                merchant.status = MerchantStatus.SUSPENDED
            
            await merchant.save()
            
            audit_response = MerchantAuditResponseSchema.from_orm(audit_record)
            return ResponseHelper.success(audit_response, "审核完成")
            
        except Exception as e:
            return ResponseHelper.server_error(f"审核失败: {str(e)}")

    @staticmethod
    async def get_merchant_by_id(merchant_id: int) -> ApiResponse[MerchantDetailSchema]:
        """根据ID获取商家详情"""
        try:
            merchant = await Merchant.get_or_none(id=merchant_id).prefetch_related('user', 'audits__admin')
            if not merchant:
                return ResponseHelper.not_found("商家不存在")
            
            merchant_dict = await merchant.to_dict()
            merchant_detail = MerchantDetailSchema(**merchant_dict)
            return ResponseHelper.success(merchant_detail, "获取商家详情成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取商家详情失败: {str(e)}")

    @staticmethod
    async def get_merchant_by_user_id(user_id: int) -> ApiResponse[MerchantDetailSchema]:
        """根据用户ID获取商家信息"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return ResponseHelper.not_found("用户不存在")
                
            merchant = await Merchant.get_or_none(user=user).prefetch_related('user', 'audits__admin')
            if not merchant:
                return ResponseHelper.not_found("用户不是商家")
            
            merchant_dict = await merchant.to_dict()
            merchant_detail = MerchantDetailSchema(**merchant_dict)
            return ResponseHelper.success(merchant_detail, "获取商家信息成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取商家信息失败: {str(e)}")

    @staticmethod
    async def update_merchant(user: User, update_data: MerchantUpdateSchema) -> ApiResponse[MerchantResponseSchema]:
        """更新商家信息"""
        try:
            # 获取用户的商家信息
            merchant = await Merchant.get_or_none(user=user)
            if not merchant:
                return ResponseHelper.not_found("您不是商家")
            
            # 只有状态为active的商家才能更新信息
            if merchant.status != MerchantStatus.ACTIVE:
                return ResponseHelper.error("只有审核通过的商家才能更新信息", 400)
            
            # 更新商家信息
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(merchant, field, value)
            
            await merchant.save()
            merchant_response = MerchantResponseSchema.from_orm(merchant)
            return ResponseHelper.success(merchant_response, "商家信息更新成功")
            
        except IntegrityError as e:
            return ResponseHelper.error("数据完整性错误，商家名称可能已存在", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"更新商家信息失败: {str(e)}")

    @staticmethod
    async def get_merchants_list(
        page: int = 1, 
        page_size: int = 10, 
        status: Optional[MerchantStatus] = None
    ) -> ApiResponse[PaginatedData[MerchantListItemSchema]]:
        """获取商家列表"""
        try:
            query = Merchant.all()
            
            # 状态过滤
            if status:
                query = query.filter(status=status)
            
            # 计算总数
            total = await query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            merchants = await query.offset(offset).limit(page_size)
            
            # 转换为响应格式
            merchant_list = [MerchantListItemSchema.from_orm(merchant) for merchant in merchants]
            
            paginated_data = PaginatedData(
                items=merchant_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
            
            return ResponseHelper.success(paginated_data, "获取商家列表成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取商家列表失败: {str(e)}")

    @staticmethod
    async def get_pending_merchants(page: int = 1, page_size: int = 10) -> ApiResponse[PaginatedData[MerchantListItemSchema]]:
        """获取待审核商家列表"""
        return await MerchantService.get_merchants_list(page, page_size, MerchantStatus.PENDING)

    @staticmethod
    async def get_my_merchant_info(user: User) -> ApiResponse[MerchantDetailSchema]:
        """获取当前用户的商家信息"""
        return await MerchantService.get_merchant_by_user_id(user.id)

    @staticmethod
    async def get_audit_history(merchant_id: int) -> ApiResponse[list]:
        """获取商家审核历史"""
        try:
            merchant = await Merchant.get_or_none(id=merchant_id)
            if not merchant:
                return ResponseHelper.not_found("商家不存在")
            
            audits = await MerchantAudit.filter(merchant=merchant).prefetch_related('admin').order_by('-created_at')
            
            audit_list = []
            for audit in audits:
                audit_dict = await audit.to_dict()
                audit_list.append(MerchantAuditResponseSchema(**audit_dict))
            
            return ResponseHelper.success(audit_list, "获取审核历史成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取审核历史失败: {str(e)}") 
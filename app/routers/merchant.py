from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from typing import Optional
from app.schemas.merchant import (
    MerchantApplySchema,
    MerchantUpdateSchema,
    MerchantResponseSchema,
    MerchantAuditSchema,
    MerchantAuditResponseSchema,
    MerchantListItemSchema,
    MerchantDetailSchema
)
from app.schemas.response import ApiResponse, PaginatedData
from app.schemas.user import UploadResponseSchema
from app.services.merchant_service import MerchantService
from app.utils.auth import get_current_user, require_admin
from app.utils.cos_utils import cos_uploader
from app.models.user import User
from app.models.merchant import MerchantStatus

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("/upload-license", response_model=ApiResponse[UploadResponseSchema], summary="上传营业执照")
async def upload_merchant_license(
    file: UploadFile = File(..., description="营业执照图片文件"),
    current_user: User = Depends(get_current_user)
):
    """
    上传商家营业执照
    
    - **file**: 营业执照图片文件（支持jpg、jpeg、png、gif、webp格式，最大10MB）
    
    返回上传后的图片URL，用于申请商家时填写license_image字段
    """
    try:
        file_url, upload_info = await cos_uploader.upload_merchant_license(file, current_user.id)
        
        response_data = UploadResponseSchema(
            url=upload_info['url'],
            filename=upload_info['filename'],
            size=upload_info['size'],
            content_type=upload_info['content_type']
        )
        
        return ApiResponse.success(response_data, "营业执照上传成功")
    except Exception as e:
        return ApiResponse.error(f"上传失败: {str(e)}", 500)


@router.post("/apply", response_model=ApiResponse[MerchantResponseSchema], summary="申请成为商家")
async def apply_merchant(
    apply_data: MerchantApplySchema,
    current_user: User = Depends(get_current_user)
):
    """
    申请成为商家
    
    - **merchant_name**: 商家名称（必填，最大100字符）
    - **license_number**: 营业执照号（必填，最大50字符）
    - **license_image**: 营业执照图片URL（必填，通过上传接口获得）
    - **contact_phone**: 联系电话（必填，最大20字符）
    - **address**: 地址（可选，最大255字符）
    - **description**: 描述（可选）
    
    申请提交后需要等待管理员审核
    """
    return await MerchantService.apply_merchant(current_user, apply_data)


@router.post("/audit", response_model=ApiResponse[MerchantAuditResponseSchema], summary="审核商家申请")
async def audit_merchant(
    audit_data: MerchantAuditSchema,
    current_user: User = Depends(require_admin)
):
    """
    审核商家申请（仅管理员）
    
    - **merchant_id**: 商家ID
    - **audit_result**: 审核结果（approved/rejected）
    - **comment**: 审核意见（可选，最大1000字符）
    
    审核通过后商家状态变为active，用户角色变为merchant
    """
    return await MerchantService.audit_merchant(current_user, audit_data)


@router.get("/me", response_model=ApiResponse[MerchantDetailSchema], summary="获取我的商家信息")
async def get_my_merchant_info(current_user: User = Depends(get_current_user)):
    """获取当前用户的商家信息"""
    return await MerchantService.get_my_merchant_info(current_user)


@router.put("/me", response_model=ApiResponse[MerchantResponseSchema], summary="更新我的商家信息")
async def update_my_merchant(
    update_data: MerchantUpdateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户的商家信息
    
    - **merchant_name**: 商家名称（可选）
    - **contact_phone**: 联系电话（可选）
    - **address**: 地址（可选）
    - **description**: 描述（可选）
    
    只有审核通过的商家才能更新信息
    """
    return await MerchantService.update_merchant(current_user, update_data)


@router.get("/", response_model=ApiResponse[PaginatedData[MerchantListItemSchema]], summary="获取商家列表")
async def get_merchants_list(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[MerchantStatus] = Query(None, description="状态过滤"),
    current_user: User = Depends(require_admin)
):
    """获取商家列表（仅管理员）"""
    return await MerchantService.get_merchants_list(page, page_size, status)


@router.get("/pending", response_model=ApiResponse[PaginatedData[MerchantListItemSchema]], summary="获取待审核商家列表")
async def get_pending_merchants(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    current_user: User = Depends(require_admin)
):
    """获取待审核商家列表（仅管理员）"""
    return await MerchantService.get_pending_merchants(page, page_size)


@router.get("/{merchant_id}", response_model=ApiResponse[MerchantDetailSchema], summary="根据ID获取商家详情")
async def get_merchant_by_id(
    merchant_id: int,
    current_user: User = Depends(require_admin)
):
    """根据商家ID获取商家详情（仅管理员）"""
    return await MerchantService.get_merchant_by_id(merchant_id)


@router.get("/{merchant_id}/audit-history", response_model=ApiResponse[list], summary="获取商家审核历史")
async def get_merchant_audit_history(
    merchant_id: int,
    current_user: User = Depends(require_admin)
):
    """获取商家审核历史（仅管理员）"""
    return await MerchantService.get_audit_history(merchant_id) 
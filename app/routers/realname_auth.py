from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import Optional
from app.schemas.realname_auth import (
    RealnameAuthSubmitSchema,
    RealnameAuthResponseSchema,
    RealnameAuthUpdateStatusSchema,
    RealnameAuthUpdateSchema,
    RealnameAuthListItemSchema,
    IdCardUploadResponseSchema
)
from app.schemas.response import ApiResponse, ResponseHelper, PaginatedData
from app.services.realname_auth_service import RealnameAuthService
from app.utils.auth import get_current_user, require_admin
from app.models.user import User
from app.models.realname_auth import RealnameAuthStatus

router = APIRouter(prefix="/realname-auth", tags=["realname-auth"])


@router.post("/upload-images", response_model=ApiResponse[IdCardUploadResponseSchema], summary="上传身份证图片")
async def upload_id_card_images(
    front_image: Optional[UploadFile] = File(None, description="身份证正面照片"),
    back_image: Optional[UploadFile] = File(None, description="身份证背面照片"),
    current_user: User = Depends(get_current_user)
):
    """
    上传身份证图片
    
    - **front_image**: 身份证正面照片（可选）
    - **back_image**: 身份证背面照片（可选）
    
    至少需要上传一张图片，支持jpg、jpeg、png格式，最大10MB
    """
    return await RealnameAuthService.upload_id_card_images(current_user, front_image, back_image)


@router.post("/submit", response_model=ApiResponse[RealnameAuthResponseSchema], summary="提交实名认证")
async def submit_realname_auth(
    real_name: str = Form(..., description="真实姓名"),
    id_card: str = Form(..., description="身份证号"),
    front_image: UploadFile = File(..., description="身份证正面照片"),
    back_image: UploadFile = File(..., description="身份证背面照片"),
    current_user: User = Depends(get_current_user)
):
    """
    提交实名认证
    
    - **real_name**: 真实姓名（2-50个字符，仅支持中文和·）
    - **id_card**: 身份证号（18位）
    - **front_image**: 身份证正面照片
    - **back_image**: 身份证背面照片
    
    需要同时上传身份证正反面照片和填写个人信息
    """
    # 验证提交数据
    auth_data = RealnameAuthSubmitSchema(real_name=real_name, id_card=id_card)
    
    # 上传图片
    upload_result = await RealnameAuthService.upload_id_card_images(current_user, front_image, back_image)
    if not upload_result.success:
        return upload_result
    
    # 获取上传的图片URL
    front_image_url = upload_result.data.front_image
    back_image_url = upload_result.data.back_image
    
    if not front_image_url or not back_image_url:
        return ResponseHelper.error("身份证正反面照片都必须上传", 400)
    
    # 提交认证
    return await RealnameAuthService.submit_realname_auth(
        current_user, auth_data, front_image_url, back_image_url
    )


@router.get("/me", response_model=ApiResponse[RealnameAuthResponseSchema], summary="获取我的实名认证信息")
async def get_my_realname_auth(current_user: User = Depends(get_current_user)):
    """获取当前用户的实名认证信息"""
    return await RealnameAuthService.get_user_realname_auth(current_user)


@router.put("/me", response_model=ApiResponse[RealnameAuthResponseSchema], summary="更新我的实名认证信息")
async def update_my_realname_auth(
    real_name: Optional[str] = Form(None, description="真实姓名"),
    id_card: Optional[str] = Form(None, description="身份证号"),
    front_image: Optional[UploadFile] = File(None, description="身份证正面照片"),
    back_image: Optional[UploadFile] = File(None, description="身份证背面照片"),
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户的实名认证信息
    
    - **real_name**: 真实姓名（2-50个字符，仅支持中文和·）
    - **id_card**: 身份证号（18位）
    - **front_image**: 身份证正面照片
    - **back_image**: 身份证背面照片
    
    只有认证状态为待审核或已拒绝的用户可以更新认证信息
    已通过认证的用户无法修改认证信息
    """
    # 创建更新数据对象
    update_data = RealnameAuthUpdateSchema(
        real_name=real_name,
        id_card=id_card
    )
    
    return await RealnameAuthService.update_user_realname_auth(
        current_user, update_data, front_image, back_image
    )


@router.get("/list", response_model=ApiResponse[PaginatedData[RealnameAuthListItemSchema]], summary="获取实名认证列表")
async def get_realname_auth_list(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[RealnameAuthStatus] = Query(None, description="认证状态筛选"),
    current_user: User = Depends(require_admin)
):
    """获取实名认证列表（仅管理员）"""
    return await RealnameAuthService.get_realname_auth_list(page, page_size, status)


@router.get("/{auth_id}", response_model=ApiResponse[RealnameAuthResponseSchema], summary="获取实名认证详情")
async def get_realname_auth_detail(
    auth_id: int,
    current_user: User = Depends(require_admin)
):
    """获取实名认证详情（仅管理员）"""
    return await RealnameAuthService.get_realname_auth_detail(auth_id)


@router.put("/{auth_id}/status", response_model=ApiResponse[RealnameAuthResponseSchema], summary="更新实名认证状态")
async def update_realname_auth_status(
    auth_id: int,
    update_data: RealnameAuthUpdateStatusSchema,
    current_user: User = Depends(require_admin)
):
    """
    更新实名认证状态（仅管理员）
    
    - **status**: 认证状态（pending、approved、rejected）
    - **reject_reason**: 拒绝原因（status为rejected时必填）
    """
    return await RealnameAuthService.update_realname_auth_status(auth_id, update_data)


@router.delete("/{auth_id}", response_model=ApiResponse[dict], summary="删除实名认证记录")
async def delete_realname_auth(
    auth_id: int,
    current_user: User = Depends(require_admin)
):
    """删除实名认证记录（仅管理员）"""
    return await RealnameAuthService.delete_realname_auth(auth_id)
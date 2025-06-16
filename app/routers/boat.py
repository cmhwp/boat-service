from fastapi import APIRouter, Depends, Query, Path, UploadFile, File
from typing import Optional
from app.schemas.boat import (
    BoatCreateSchema,
    BoatUpdateSchema,
    BoatResponseSchema,
    BoatDetailSchema,
    BoatListItemSchema,
    BoatStatusUpdateSchema
)
from app.schemas.response import ApiResponse, PaginatedData, ResponseHelper
from app.schemas.user import UploadResponseSchema
from app.services.boat_service import BoatService
from app.utils.auth import get_current_user
from app.utils.cos_utils import cos_uploader
from app.config.cos_config import cos_config
from app.models.user import User
from app.models.boat import BoatType, BoatStatus

router = APIRouter(prefix="/boats", tags=["boats"])


# 图片上传API
@router.post("/upload-image", response_model=ApiResponse[UploadResponseSchema], summary="上传船只图片")
async def upload_boat_image(
    file: UploadFile = File(..., description="船只图片文件"),
    current_user: User = Depends(get_current_user)
):
    """
    上传船只图片
    
    - **file**: 船只图片文件（支持jpg、jpeg、png、gif、webp格式，最大10MB）
    
    返回上传后的图片URL，用于添加或更新船只时填写images字段
    """
    try:
        file_url, upload_info = await cos_uploader.upload_image(file, cos_config.BOAT_PREFIX)
        
        response_data = UploadResponseSchema(
            url=upload_info['url'],
            filename=upload_info['filename'],
            size=upload_info['size'],
            content_type=upload_info['content_type']
        )
        
        return ResponseHelper.success(response_data, "船只图片上传成功")
    except Exception as e:
        return ResponseHelper.error(f"上传失败: {str(e)}", 500)


# 商家端API
@router.post("/", response_model=ApiResponse[BoatResponseSchema], summary="添加船只")
async def create_boat(
    boat_data: BoatCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    添加船只（商家端）
    
    - **name**: 船只名称（必填，最大100字符）
    - **license_number**: 船只证书号（必填，最大50字符，唯一）
    - **boat_type**: 船只类型（默认观光船）
    - **capacity**: 载客量（必填，1-100人）
    - **hourly_rate**: 小时费率（必填，大于0）
    - **description**: 船只描述（可选）
    - **images**: 船只图片列表（可选，最多10张）
    - **current_location**: 当前位置（可选）
    
    只有审核通过的商家才能添加船只
    """
    return await BoatService.create_boat(current_user, boat_data)


@router.get("/my", response_model=ApiResponse[PaginatedData[BoatListItemSchema]], summary="获取我的船只列表")
async def get_my_boats(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[BoatStatus] = Query(None, description="状态过滤"),
    current_user: User = Depends(get_current_user)
):
    """获取我的船只列表（商家端）"""
    return await BoatService.get_my_boats(current_user, page, page_size, status)


@router.get("/my/{boat_id}", response_model=ApiResponse[BoatDetailSchema], summary="获取我的船只详情")
async def get_my_boat_detail(
    boat_id: int = Path(..., description="船只ID"),
    current_user: User = Depends(get_current_user)
):
    """获取我的船只详情（商家端）"""
    return await BoatService.get_boat_detail(current_user, boat_id)


@router.put("/my/{boat_id}", response_model=ApiResponse[BoatResponseSchema], summary="更新我的船只信息")
async def update_my_boat(
    boat_id: int = Path(..., description="船只ID"),
    boat_data: BoatUpdateSchema = ...,
    current_user: User = Depends(get_current_user)
):
    """
    更新我的船只信息（商家端）
    
    - **name**: 船只名称（可选）
    - **boat_type**: 船只类型（可选）
    - **capacity**: 载客量（可选）
    - **hourly_rate**: 小时费率（可选）
    - **description**: 船只描述（可选）
    - **images**: 船只图片列表（可选）
    - **current_location**: 当前位置（可选）
    - **status**: 状态（可选）
    """
    return await BoatService.update_boat(current_user, boat_id, boat_data)


@router.delete("/my/{boat_id}", response_model=ApiResponse[dict], summary="删除我的船只")
async def delete_my_boat(
    boat_id: int = Path(..., description="船只ID"),
    current_user: User = Depends(get_current_user)
):
    """删除我的船只（商家端）"""
    return await BoatService.delete_boat(current_user, boat_id)


@router.patch("/my/{boat_id}/status", response_model=ApiResponse[BoatResponseSchema], summary="更新船只状态")
async def update_boat_status(
    boat_id: int = Path(..., description="船只ID"),
    status_data: BoatStatusUpdateSchema = ...,
    current_user: User = Depends(get_current_user)
):
    """
    更新船只状态（商家端）
    
    - **status**: 状态（必填）
    - **current_location**: 当前位置（可选）
    
    可用状态：available（可用）、in_use（使用中）、maintenance（维护中）、inactive（停用）
    """
    return await BoatService.update_boat_status(current_user, boat_id, status_data)


# 用户端API
@router.get("/available", response_model=ApiResponse[PaginatedData[BoatListItemSchema]], summary="获取可用船只列表")
async def get_available_boats(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    boat_type: Optional[BoatType] = Query(None, description="船只类型过滤"),
    min_capacity: Optional[int] = Query(None, description="最小载客量", ge=1),
    max_hourly_rate: Optional[float] = Query(None, description="最大小时费率", ge=0)
):
    """
    获取可用船只列表（用户端）
    
    - **boat_type**: 船只类型过滤（可选）
    - **min_capacity**: 最小载客量（可选）
    - **max_hourly_rate**: 最大小时费率（可选）
    
    只显示状态为可用且所属商家已审核通过的船只
    """
    return await BoatService.get_available_boats(page, page_size, boat_type, min_capacity, max_hourly_rate)


@router.get("/{boat_id}", response_model=ApiResponse[BoatDetailSchema], summary="获取船只详情")
async def get_boat_detail(
    boat_id: int = Path(..., description="船只ID")
):
    """获取船只详情（用户端）"""
    return await BoatService.get_public_boat_detail(boat_id)
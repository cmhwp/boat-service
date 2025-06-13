from fastapi import APIRouter, Depends, Query, status
from typing import Optional
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
from app.schemas.response import ApiResponse, PaginatedData
from app.services.crew_service import CrewService
from app.utils.auth import get_current_user, require_merchant
from app.models.user import User

router = APIRouter(prefix="/crew", tags=["crew"])


@router.post("/apply", response_model=ApiResponse[CrewApplicationResponseSchema], summary="申请成为船员")
async def apply_crew(
    apply_data: CrewApplicationSchema,
    current_user: User = Depends(get_current_user)
):
    """
    申请加入商家成为船员
    
    - **merchant_id**: 商家ID（必填）
    
    用户向指定商家申请加入成为船员，需要等待商家处理
    同一用户不能重复申请同一商家，如果之前被拒绝可以重新申请
    """
    return await CrewService.apply_crew(current_user, apply_data)


@router.post("/handle-application", response_model=ApiResponse[CrewApplicationResponseSchema], summary="处理船员申请")
async def handle_crew_application(
    handle_data: CrewApplicationHandleSchema,
    current_user: User = Depends(require_merchant)
):
    """
    处理船员申请（仅商家）
    
    - **application_id**: 申请ID
    - **status**: 处理结果（approved/rejected）
    - **boat_license**: 船员证号（同意申请时必填）
    
    只有商家可以处理向自己提交的船员申请
    同意申请时需要提供船员证号，用户角色会自动更新为crew
    """
    return await CrewService.handle_crew_application(current_user, handle_data)


@router.get("/applications", response_model=ApiResponse[PaginatedData[CrewApplicationDetailSchema]], summary="获取船员申请列表")
async def get_crew_applications(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    current_user: User = Depends(require_merchant)
):
    """获取商家的船员申请列表（仅商家）"""
    return await CrewService.get_crew_applications(current_user, page, page_size)


@router.get("/my-applications", response_model=ApiResponse[PaginatedData[CrewApplicationDetailSchema]], summary="获取我的申请列表")
async def get_my_crew_applications(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """获取我的船员申请列表"""
    return await CrewService.get_my_crew_applications(current_user, page, page_size)


@router.get("/list", response_model=ApiResponse[PaginatedData[CrewListItemSchema]], summary="获取船员列表")
async def get_crew_list(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    current_user: User = Depends(require_merchant)
):
    """获取商家的船员列表（仅商家）"""
    return await CrewService.get_crew_list(current_user, page, page_size)


@router.get("/me", response_model=ApiResponse[CrewDetailSchema], summary="获取我的船员信息")
async def get_my_crew_info(current_user: User = Depends(get_current_user)):
    """获取当前用户的船员信息"""
    return await CrewService.get_my_crew_info(current_user)


@router.put("/{crew_id}", response_model=ApiResponse[CrewResponseSchema], summary="更新船员信息")
async def update_crew(
    crew_id: int,
    update_data: CrewUpdateSchema,
    current_user: User = Depends(require_merchant)
):
    """
    更新船员信息（仅商家）
    
    - **boat_license**: 船员证号（可选）
    - **status**: 状态（可选，active/inactive）
    - **rating**: 评分（可选，0-5分）
    
    只有商家可以更新自己旗下的船员信息
    """
    return await CrewService.update_crew(current_user, crew_id, update_data)


@router.get("/{crew_id}", response_model=ApiResponse[CrewDetailSchema], summary="获取船员详情")
async def get_crew_detail(
    crew_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取船员详情"""
    return await CrewService.get_crew_detail(crew_id)


@router.post("/resign", response_model=ApiResponse[dict], summary="船员离职")
async def resign_crew(current_user: User = Depends(get_current_user)):
    """
    船员离职
    
    船员主动离职，状态变为inactive
    如果用户只是船员角色，用户角色会变回普通用户
    """
    return await CrewService.resign_crew(current_user) 
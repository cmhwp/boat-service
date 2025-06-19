from fastapi import APIRouter, Depends, Query, Path, Body
from typing import Optional, List
from datetime import datetime

from app.models.user import User
from app.models.booking import BookingStatus
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
    CrewRatingResponseSchema,
    CrewTaskListItemSchema,
    CrewTaskDetailSchema,
    CrewTaskStatusUpdateSchema,
    CrewTaskQuerySchema,
    CrewTaskStatsSchema
)
from app.schemas.response import ApiResponse, PaginatedData
from app.services.booking_service import BookingService
from app.utils.auth import get_current_user, require_merchant, require_admin, require_crew

router = APIRouter(prefix="/bookings", tags=["bookings"])


# =================== 用户端预约接口 ===================

@router.post("/", response_model=ApiResponse[BookingResponseSchema], summary="创建船艇预约")
async def create_booking(
    booking_data: BookingCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    创建船艇预约（用户端）
    
    - **boat_id**: 船只ID（必填）
    - **start_time**: 开始时间（必填）
    - **end_time**: 结束时间（必填）
    - **passenger_count**: 乘客人数（必填）
    - **contact_name**: 联系人姓名（必填）
    - **contact_phone**: 联系电话（必填）
    - **user_notes**: 用户备注（可选）
    
    系统会自动验证：
    - 船只可用性和载客量限制
    - 时间冲突检测
    - 商家审核状态
    - 自动计算费用
    """
    return await BookingService.create_booking(current_user, booking_data)


@router.get("/availability", response_model=ApiResponse[BookingAvailabilityResponseSchema], summary="检查船只可用性")
async def check_boat_availability(
    boat_id: int = Query(..., description="船只ID"),
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间")
):
    """
    检查船只在指定时间段的可用性
    
    返回信息包括：
    - 是否可用
    - 不可用原因
    - 冲突预约列表
    """
    query_data = BookingAvailabilityQuerySchema(
        boat_id=boat_id,
        start_time=start_time,
        end_time=end_time
    )
    return await BookingService.check_boat_availability(query_data)


@router.get("/my", response_model=ApiResponse[PaginatedData[BookingListItemSchema]], summary="获取我的预约列表")
async def get_my_bookings(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[BookingStatus] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    boat_id: Optional[int] = Query(None, description="船只ID过滤"),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的预约列表
    
    支持按状态、日期、船只等条件过滤
    """
    query_params = BookingQuerySchema(
        status=status,
        start_date=start_date,
        end_date=end_date,
        boat_id=boat_id,
        page=page,
        page_size=page_size
    )
    return await BookingService.get_user_bookings(current_user, query_params)


@router.get("/{booking_id}", response_model=ApiResponse[BookingDetailSchema], summary="获取预约详情")
async def get_booking_detail(
    booking_id: int = Path(..., description="预约ID"),
    current_user: User = Depends(get_current_user)
):
    """
    获取预约详情
    
    只有预约用户和所属商家可以查看详情
    """
    return await BookingService.get_booking_detail(current_user, booking_id)


@router.patch("/{booking_id}/cancel", response_model=ApiResponse[BookingResponseSchema], summary="取消预约")
async def cancel_booking(
    booking_id: int = Path(..., description="预约ID"),
    cancel_reason: Optional[str] = Body(None, description="取消原因"),
    current_user: User = Depends(get_current_user)
):
    """
    取消预约（用户端）
    
    限制条件：
    - 只能取消待确认或已确认状态的预约
    - 开始前2小时内无法取消
    """
    return await BookingService.cancel_booking(current_user, booking_id, cancel_reason)


# =================== 商家端预约管理接口 ===================

@router.get("/merchant/list", response_model=ApiResponse[PaginatedData[BookingDetailSchema]], summary="获取商家预约列表")
async def get_merchant_bookings(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[BookingStatus] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    boat_id: Optional[int] = Query(None, description="船只ID过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    current_user: User = Depends(require_merchant)
):
    """
    获取商家预约列表（商家端）
    
    包含完整的预约信息和关联数据
    """
    query_params = BookingQuerySchema(
        status=status,
        start_date=start_date,
        end_date=end_date,
        boat_id=boat_id,
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    return await BookingService.get_merchant_bookings(current_user, query_params)


@router.patch("/{booking_id}/status", response_model=ApiResponse[BookingResponseSchema], summary="更新预约状态")
async def update_booking_status(
    booking_id: int = Path(..., description="预约ID"),
    status_data: BookingStatusUpdateSchema = ...,
    current_user: User = Depends(require_merchant)
):
    """
    更新预约状态（商家端）
    
    - **status**: 预约状态（必填）
    - **merchant_notes**: 商家备注（可选）
    - **cancel_reason**: 取消原因（取消时必填）
    
    状态转换规则：
    - pending -> confirmed/rejected
    - confirmed -> in_progress/cancelled  
    - in_progress -> completed
    """
    return await BookingService.update_booking_status(current_user, booking_id, status_data)


@router.post("/assign-crew", response_model=ApiResponse[BookingResponseSchema], summary="派单给船员")
async def assign_crew(
    assignment_data: CrewAssignmentSchema,
    current_user: User = Depends(require_merchant)
):
    """
    将预约派单给船员（商家端）
    
    - **booking_id**: 预约ID（必填）
    - **crew_id**: 船员ID（必填）
    - **notes**: 派单备注（可选）
    
    限制条件：
    - 只能派单给已确认的预约
    - 船员必须属于当前商家
    - 船员在该时间段不能有冲突任务
    """
    return await BookingService.assign_crew(current_user, assignment_data)


@router.get("/merchant/stats", response_model=ApiResponse[BookingStatsSchema], summary="获取预约统计数据")
async def get_booking_stats(
    current_user: User = Depends(require_merchant)
):
    """
    获取商家预约统计数据
    
    包括：
    - 各状态预约数量
    - 总收入统计
    - 平均评分
    """
    return await BookingService.get_booking_stats(current_user)


# =================== 船员评价接口 ===================

@router.post("/ratings", response_model=ApiResponse[CrewRatingResponseSchema], summary="创建船员评价")
async def create_crew_rating(
    rating_data: CrewRatingCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    对船员进行评价（用户端）
    
    - **booking_id**: 预约ID（必填）
    - **rating**: 评分1-5（必填）
    - **comment**: 评价内容（可选）
    
    限制条件：
    - 只能评价已完成的预约
    - 预约必须有指派船员
    - 每个预约只能评价一次
    """
    return await BookingService.create_crew_rating(current_user, rating_data)


@router.get("/ratings/{booking_id}", response_model=ApiResponse[CrewRatingResponseSchema], summary="获取预约评价")
async def get_booking_rating(
    booking_id: int = Path(..., description="预约ID"),
    current_user: User = Depends(get_current_user)
):
    """获取指定预约的评价信息"""
    try:
        from app.models.booking import CrewRating, BoatBooking
        from app.schemas.response import ResponseHelper
        
        # 获取预约
        booking = await BoatBooking.filter(id=booking_id).select_related('merchant').first()
        if not booking:
            return ResponseHelper.not_found("预约不存在")
        
        # 权限检查
        if booking.user_id != current_user.id and booking.merchant.user_id != current_user.id:
            return ResponseHelper.forbidden("无权限查看此评价")
        
        # 获取评价
        rating = await CrewRating.filter(booking_id=booking_id).first()
        if not rating:
            return ResponseHelper.not_found("该预约暂无评价")
        
        rating_dict = await rating.to_dict()
        rating_response = CrewRatingResponseSchema(**rating_dict)
        return ResponseHelper.success(rating_response, "获取评价成功")
        
    except Exception as e:
        return ResponseHelper.server_error(f"获取评价失败: {str(e)}")


# =================== 管理员接口 ===================

@router.get("/admin/all", response_model=ApiResponse[PaginatedData[BookingDetailSchema]], summary="获取所有预约列表")
async def get_all_bookings(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[BookingStatus] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    merchant_id: Optional[int] = Query(None, description="商家ID过滤"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有预约列表（管理员端）
    
    管理员可以查看所有商家的预约数据
    """
    # 检查管理员权限
    if current_user.role != 'admin':
        from app.schemas.response import ResponseHelper
        return ResponseHelper.forbidden("需要管理员权限")
    
    try:
        # 构建查询
        from app.models.booking import BoatBooking
        from app.schemas.response import ResponseHelper
        
        query = BoatBooking.all().select_related('user', 'boat', 'merchant', 'assigned_crew__user')
        
        if status:
            query = query.filter(status=status)
        if start_date:
            query = query.filter(start_time__gte=start_date)
        if end_date:
            query = query.filter(end_time__lte=end_date)
        if merchant_id:
            query = query.filter(merchant_id=merchant_id)
        if user_id:
            query = query.filter(user_id=user_id)

        # 分页查询
        offset = (page - 1) * page_size
        bookings = await query.offset(offset).limit(page_size).order_by('-created_at')
        total = await query.count()

        # 转换为响应数据
        booking_list = []
        for booking in bookings:
            booking_dict = await booking.to_dict()
            booking_detail = BookingDetailSchema(**booking_dict)
            booking_list.append(booking_detail)
        
        total_pages = (total + page_size - 1) // page_size
        paginated_data = PaginatedData(
            items=booking_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

        return ResponseHelper.success(paginated_data, "获取预约列表成功")

    except Exception as e:
        from app.schemas.response import ResponseHelper
        return ResponseHelper.server_error(f"获取预约列表失败: {str(e)}")


@router.post("/admin/auto-cancel", response_model=ApiResponse, summary="手动触发自动取消超时预约")
async def manual_auto_cancel_expired_bookings(
    current_user: User = Depends(get_current_user)
):
    """
    手动触发自动取消超时预约任务（管理员端）
    
    将所有状态为待确认且创建时间超过20分钟的预约自动取消。
    
    系统每5分钟会自动执行一次此任务，此接口用于手动立即执行。
    
    返回信息：
    - cancelled_count: 取消的预约数量
    - cancelled_bookings: 被取消的预约详情列表（包含等待时间）
    - total_expired: 总共找到的超时预约数量
    """
    # 检查管理员权限
    if current_user.role != 'admin':
        from app.schemas.response import ResponseHelper
        return ResponseHelper.forbidden("需要管理员权限")
    
    return await BookingService.auto_cancel_expired_bookings()


# =================== 船员端预约管理接口 ===================

@router.get("/crew/tasks", response_model=ApiResponse[PaginatedData[CrewTaskListItemSchema]], summary="获取船员任务列表")
async def get_crew_tasks(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[BookingStatus] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(require_crew)
):
    """
    获取船员任务列表（船员端）
    
    支持按状态、日期等条件过滤
    """
    query_params = CrewTaskQuerySchema(
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    return await BookingService.get_crew_tasks(current_user, query_params)


@router.get("/crew/tasks/today", response_model=ApiResponse[List[CrewTaskListItemSchema]], summary="获取船员今日任务")
async def get_crew_today_tasks(
    current_user: User = Depends(require_crew)
):
    """
    获取船员今日任务列表
    
    返回今天需要执行的所有已确认和进行中的任务
    """
    return await BookingService.get_crew_today_tasks(current_user)


@router.get("/crew/tasks/{booking_id}", response_model=ApiResponse[CrewTaskDetailSchema], summary="获取船员任务详情")
async def get_crew_task_detail(
    booking_id: int = Path(..., description="预约任务ID"),
    current_user: User = Depends(require_crew)
):
    """
    获取船员任务详情
    
    包含完整的任务信息、客户信息、船只信息等
    """
    return await BookingService.get_crew_task_detail(current_user, booking_id)


@router.patch("/crew/tasks/{booking_id}/status", response_model=ApiResponse[BookingResponseSchema], summary="更新任务状态")
async def update_crew_task_status(
    booking_id: int = Path(..., description="预约任务ID"),
    status_data: CrewTaskStatusUpdateSchema = ...,
    current_user: User = Depends(require_crew)
):
    """
    更新船员任务状态（船员端）
    
    - **status**: 任务状态（必填，只能是in_progress或completed）
    - **notes**: 船员备注（可选）
    
    状态转换规则：
    - confirmed -> in_progress（开始服务）
    - in_progress -> completed（完成服务）
    
    限制条件：
    - 开始服务：需要在预约时间前30分钟内
    - 完成服务：只能完成进行中的任务
    """
    return await BookingService.update_crew_task_status(current_user, booking_id, status_data)


@router.get("/crew/stats", response_model=ApiResponse[CrewTaskStatsSchema], summary="获取船员任务统计")
async def get_crew_task_stats(
    current_user: User = Depends(require_crew)
):
    """
    获取船员任务统计数据
    
    包括：
    - 各状态任务数量统计
    - 总收入和本月收入
    - 平均评分
    - 服务完成情况
    
    注：收入按60%分成计算
    """
    return await BookingService.get_crew_task_stats(current_user) 
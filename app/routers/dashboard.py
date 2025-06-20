# 管理员仪表盘路由

from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewSchema, DashboardChartsSchema
from app.schemas.response import ApiResponse
from app.services.dashboard_service import DashboardService
from app.utils.auth import require_admin

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("/overview", response_model=ApiResponse[DashboardOverviewSchema], summary="获取仪表盘总览")
async def get_dashboard_overview(
    current_user: User = Depends(require_admin)
):
    """
    获取管理员仪表盘总览数据
    
    包含以下统计信息：
    - **用户统计**: 总用户数、活跃用户、角色分布、实名认证状态等
    - **商家统计**: 总商家数、各状态商家数量、近期申请等
    - **商品统计**: 总商品数、各状态商品数量、分类分布、销售额等
    - **船舶统计**: 总船舶数、各状态船舶数量、类型分布、平均费率等
    - **订单统计**: 总订单数、各状态订单数量、金额统计、平台抽成等
    - **预约统计**: 总预约数、各状态预约数量、金额统计、平均时长等
    - **船员统计**: 总船员数、活跃状态、评分统计等
    - **财务统计**: 总收入、各类收入、平台抽成、分成统计等
    - **近期活动**: 近7天各类数据增长情况
    
    权限要求：管理员
    """
    return await DashboardService.get_dashboard_overview(current_user)


@router.get("/charts", response_model=ApiResponse[DashboardChartsSchema], summary="获取仪表盘图表数据")
async def get_dashboard_charts(
    current_user: User = Depends(require_admin)
):
    """
    获取管理员仪表盘图表数据
    
    包含以下图表：
    - **用户增长图表**: 近30天用户注册趋势
    - **订单趋势图表**: 近30天订单创建趋势
    - **预约趋势图表**: 近30天预约创建趋势
    - **收入图表**: 近30天收入变化趋势
    - **商品分类饼图**: 各类商品数量分布
    - **船舶类型饼图**: 各类船舶数量分布
    
    图表数据格式：
    - labels: 标签数组（日期、分类名称等）
    - data: 数据数组（数量、金额等）
    - title: 图表标题
    
    权限要求：管理员
    """
    return await DashboardService.get_dashboard_charts(current_user) 
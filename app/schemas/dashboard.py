# 管理员仪表盘数据模式

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class UserStatsSchema(BaseModel):
    """用户统计数据"""
    total_users: int = Field(..., description="用户总数")
    active_users: int = Field(..., description="活跃用户数")
    inactive_users: int = Field(..., description="非活跃用户数")
    verified_users: int = Field(..., description="实名认证用户数")
    pending_verification: int = Field(..., description="待认证用户数")
    role_distribution: Dict[str, int] = Field(..., description="角色分布")
    recent_registrations: int = Field(..., description="近7天注册用户数")


class MerchantStatsSchema(BaseModel):
    """商家统计数据"""
    total_merchants: int = Field(..., description="商家总数")
    active_merchants: int = Field(..., description="活跃商家数")
    pending_merchants: int = Field(..., description="待审核商家数")
    suspended_merchants: int = Field(..., description="暂停商家数")
    recent_applications: int = Field(..., description="近7天申请数")


class ProductStatsSchema(BaseModel):
    """商品统计数据"""
    total_products: int = Field(..., description="商品总数")
    available_products: int = Field(..., description="可售商品数")
    sold_out_products: int = Field(..., description="售罄商品数")
    inactive_products: int = Field(..., description="下架商品数")
    low_stock_products: int = Field(..., description="低库存商品数(<=10)")
    category_distribution: Dict[str, int] = Field(..., description="分类分布")
    total_sales_amount: float = Field(..., description="总销售额")


class BoatStatsSchema(BaseModel):
    """船舶统计数据"""
    total_boats: int = Field(..., description="船舶总数")
    available_boats: int = Field(..., description="可用船舶数")
    in_use_boats: int = Field(..., description="使用中船舶数")
    maintenance_boats: int = Field(..., description="维护中船舶数")
    inactive_boats: int = Field(..., description="停用船舶数")
    type_distribution: Dict[str, int] = Field(..., description="类型分布")
    average_hourly_rate: float = Field(..., description="平均小时费率")


class OrderStatsSchema(BaseModel):
    """订单统计数据"""
    total_orders: int = Field(..., description="订单总数")
    pending_orders: int = Field(..., description="待支付订单数")
    paid_orders: int = Field(..., description="已支付订单数")
    completed_orders: int = Field(..., description="已完成订单数")
    cancelled_orders: int = Field(..., description="已取消订单数")
    total_order_amount: float = Field(..., description="订单总金额")
    paid_amount: float = Field(..., description="已支付金额")
    platform_commission: float = Field(..., description="平台抽成(5%)")
    recent_orders: int = Field(..., description="近7天订单数")


class BookingStatsSchema(BaseModel):
    """预约统计数据"""
    total_bookings: int = Field(..., description="预约总数")
    pending_bookings: int = Field(..., description="待确认预约数")
    confirmed_bookings: int = Field(..., description="已确认预约数")
    completed_bookings: int = Field(..., description="已完成预约数")
    cancelled_bookings: int = Field(..., description="已取消预约数")
    total_booking_amount: float = Field(..., description="预约总金额")
    paid_booking_amount: float = Field(..., description="已支付预约金额")
    average_booking_duration: float = Field(..., description="平均预约时长(小时)")
    recent_bookings: int = Field(..., description="近7天预约数")


class CrewStatsSchema(BaseModel):
    """船员统计数据"""
    total_crews: int = Field(..., description="船员总数")
    active_crews: int = Field(..., description="活跃船员数")
    inactive_crews: int = Field(..., description="非活跃船员数")
    average_rating: float = Field(..., description="平均评分")
    total_ratings: int = Field(..., description="评价总数")


class FinancialStatsSchema(BaseModel):
    """财务统计数据"""
    total_revenue: float = Field(..., description="总收入")
    order_revenue: float = Field(..., description="订单收入")
    booking_revenue: float = Field(..., description="预约收入")
    platform_commission: float = Field(..., description="平台抽成")
    merchant_earnings: float = Field(..., description="商家收入")
    crew_earnings: float = Field(..., description="船员收入")


class RecentActivitySchema(BaseModel):
    """近期活动统计"""
    recent_users: int = Field(..., description="近7天新用户")
    recent_merchants: int = Field(..., description="近7天新商家")
    recent_orders: int = Field(..., description="近7天新订单")
    recent_bookings: int = Field(..., description="近7天新预约")
    recent_products: int = Field(..., description="近7天新商品")


class DashboardOverviewSchema(BaseModel):
    """仪表盘总览数据"""
    user_stats: UserStatsSchema = Field(..., description="用户统计")
    merchant_stats: MerchantStatsSchema = Field(..., description="商家统计")
    product_stats: ProductStatsSchema = Field(..., description="商品统计")
    boat_stats: BoatStatsSchema = Field(..., description="船舶统计")
    order_stats: OrderStatsSchema = Field(..., description="订单统计")
    booking_stats: BookingStatsSchema = Field(..., description="预约统计")
    crew_stats: CrewStatsSchema = Field(..., description="船员统计")
    financial_stats: FinancialStatsSchema = Field(..., description="财务统计")
    recent_activity: RecentActivitySchema = Field(..., description="近期活动")
    last_updated: datetime = Field(..., description="最后更新时间")


class ChartDataSchema(BaseModel):
    """图表数据"""
    labels: List[str] = Field(..., description="标签列表")
    data: List[float] = Field(..., description="数据列表")
    title: str = Field(..., description="图表标题")


class DashboardChartsSchema(BaseModel):
    """仪表盘图表数据"""
    user_growth_chart: ChartDataSchema = Field(..., description="用户增长图表")
    order_trend_chart: ChartDataSchema = Field(..., description="订单趋势图表")
    booking_trend_chart: ChartDataSchema = Field(..., description="预约趋势图表")
    revenue_chart: ChartDataSchema = Field(..., description="收入图表")
    category_pie_chart: ChartDataSchema = Field(..., description="商品分类饼图")
    boat_type_pie_chart: ChartDataSchema = Field(..., description="船舶类型饼图") 
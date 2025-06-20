# 管理员仪表盘服务

from typing import Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from tortoise.functions import Count, Sum, Avg
from tortoise.expressions import Q

from app.models.user import User, UserRole, RealnameStatus
from app.models.merchant import Merchant, MerchantStatus
from app.models.product import Product, ProductStatus, ProductCategory
from app.models.boat import Boat, BoatStatus, BoatType
from app.models.order import Order, OrderStatus
from app.models.booking import BoatBooking, BookingStatus, PaymentStatus
from app.models.crew import Crew, CrewStatus
from app.schemas.dashboard import (
    UserStatsSchema,
    MerchantStatsSchema,
    ProductStatsSchema,
    BoatStatsSchema,
    OrderStatsSchema,
    BookingStatsSchema,
    CrewStatsSchema,
    FinancialStatsSchema,
    RecentActivitySchema,
    DashboardOverviewSchema,
    ChartDataSchema,
    DashboardChartsSchema
)
from app.schemas.response import ResponseHelper, ApiResponse


class DashboardService:
    """仪表盘服务类"""

    @staticmethod
    async def get_user_stats() -> UserStatsSchema:
        """获取用户统计数据"""
        try:
            # 基础统计
            total_users = await User.all().count()
            active_users = await User.filter(is_active=True).count()
            inactive_users = total_users - active_users
            
            # 实名认证统计
            verified_users = await User.filter(realname_status=RealnameStatus.VERIFIED).count()
            pending_verification = await User.filter(realname_status=RealnameStatus.PENDING).count()
            
            # 角色分布
            role_counts = {}
            for role in UserRole:
                count = await User.filter(role=role).count()
                role_counts[role.value] = count
            
            # 近7天注册用户
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_registrations = await User.filter(created_at__gte=seven_days_ago).count()
            
            return UserStatsSchema(
                total_users=total_users,
                active_users=active_users,
                inactive_users=inactive_users,
                verified_users=verified_users,
                pending_verification=pending_verification,
                role_distribution=role_counts,
                recent_registrations=recent_registrations
            )
        except Exception as e:
            # 返回默认值
            return UserStatsSchema(
                total_users=0,
                active_users=0,
                inactive_users=0,
                verified_users=0,
                pending_verification=0,
                role_distribution={},
                recent_registrations=0
            )

    @staticmethod
    async def get_merchant_stats() -> MerchantStatsSchema:
        """获取商家统计数据"""
        try:
            total_merchants = await Merchant.all().count()
            active_merchants = await Merchant.filter(status=MerchantStatus.ACTIVE).count()
            pending_merchants = await Merchant.filter(status=MerchantStatus.PENDING).count()
            suspended_merchants = await Merchant.filter(status=MerchantStatus.SUSPENDED).count()
            
            # 近7天申请
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_applications = await Merchant.filter(created_at__gte=seven_days_ago).count()
            
            return MerchantStatsSchema(
                total_merchants=total_merchants,
                active_merchants=active_merchants,
                pending_merchants=pending_merchants,
                suspended_merchants=suspended_merchants,
                recent_applications=recent_applications
            )
        except Exception as e:
            return MerchantStatsSchema(
                total_merchants=0,
                active_merchants=0,
                pending_merchants=0,
                suspended_merchants=0,
                recent_applications=0
            )

    @staticmethod
    async def get_product_stats() -> ProductStatsSchema:
        """获取商品统计数据"""
        try:
            total_products = await Product.all().count()
            available_products = await Product.filter(status=ProductStatus.AVAILABLE).count()
            sold_out_products = await Product.filter(status=ProductStatus.SOLD_OUT).count()
            inactive_products = await Product.filter(status=ProductStatus.INACTIVE).count()
            low_stock_products = await Product.filter(stock__lte=10, status=ProductStatus.AVAILABLE).count()
            
            # 分类分布
            category_counts = {}
            for category in ProductCategory:
                count = await Product.filter(category=category).count()
                category_counts[category.value] = count
            
            # 总销售额（简化计算）
            products = await Product.all()
            total_sales_amount = 0.0
            for product in products:
                total_sales_amount += float(product.price) * product.sales_count
            
            return ProductStatsSchema(
                total_products=total_products,
                available_products=available_products,
                sold_out_products=sold_out_products,
                inactive_products=inactive_products,
                low_stock_products=low_stock_products,
                category_distribution=category_counts,
                total_sales_amount=total_sales_amount
            )
        except Exception as e:
            return ProductStatsSchema(
                total_products=0,
                available_products=0,
                sold_out_products=0,
                inactive_products=0,
                low_stock_products=0,
                category_distribution={},
                total_sales_amount=0.0
            )

    @staticmethod
    async def get_boat_stats() -> BoatStatsSchema:
        """获取船舶统计数据"""
        try:
            total_boats = await Boat.all().count()
            available_boats = await Boat.filter(status=BoatStatus.AVAILABLE).count()
            in_use_boats = await Boat.filter(status=BoatStatus.IN_USE).count()
            maintenance_boats = await Boat.filter(status=BoatStatus.MAINTENANCE).count()
            inactive_boats = await Boat.filter(status=BoatStatus.INACTIVE).count()
            
            # 类型分布
            type_counts = {}
            for boat_type in BoatType:
                count = await Boat.filter(boat_type=boat_type).count()
                type_counts[boat_type.value] = count
            
            # 平均小时费率
            boats = await Boat.all()
            if boats:
                total_rate = sum(float(boat.hourly_rate) for boat in boats)
                average_hourly_rate = total_rate / len(boats)
            else:
                average_hourly_rate = 0.0
            
            return BoatStatsSchema(
                total_boats=total_boats,
                available_boats=available_boats,
                in_use_boats=in_use_boats,
                maintenance_boats=maintenance_boats,
                inactive_boats=inactive_boats,
                type_distribution=type_counts,
                average_hourly_rate=average_hourly_rate
            )
        except Exception as e:
            return BoatStatsSchema(
                total_boats=0,
                available_boats=0,
                in_use_boats=0,
                maintenance_boats=0,
                inactive_boats=0,
                type_distribution={},
                average_hourly_rate=0.0
            )

    @staticmethod
    async def get_order_stats() -> OrderStatsSchema:
        """获取订单统计数据"""
        try:
            total_orders = await Order.all().count()
            pending_orders = await Order.filter(status=OrderStatus.PENDING).count()
            paid_orders = await Order.filter(status=OrderStatus.PAID).count()
            completed_orders = await Order.filter(status=OrderStatus.COMPLETED).count()
            cancelled_orders = await Order.filter(status=OrderStatus.CANCELLED).count()
            
            # 金额统计
            orders = await Order.all()
            total_order_amount = sum(float(order.final_amount) for order in orders)
            
            paid_orders_list = await Order.filter(
                status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED]
            )
            paid_amount = sum(float(order.final_amount) for order in paid_orders_list)
            
            # 平台抽成 5%
            platform_commission = paid_amount * 0.05
            
            # 近7天订单
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_orders = await Order.filter(created_at__gte=seven_days_ago).count()
            
            return OrderStatsSchema(
                total_orders=total_orders,
                pending_orders=pending_orders,
                paid_orders=paid_orders,
                completed_orders=completed_orders,
                cancelled_orders=cancelled_orders,
                total_order_amount=total_order_amount,
                paid_amount=paid_amount,
                platform_commission=platform_commission,
                recent_orders=recent_orders
            )
        except Exception as e:
            return OrderStatsSchema(
                total_orders=0,
                pending_orders=0,
                paid_orders=0,
                completed_orders=0,
                cancelled_orders=0,
                total_order_amount=0.0,
                paid_amount=0.0,
                platform_commission=0.0,
                recent_orders=0
            )

    @staticmethod
    async def get_booking_stats() -> BookingStatsSchema:
        """获取预约统计数据"""
        try:
            total_bookings = await BoatBooking.all().count()
            pending_bookings = await BoatBooking.filter(status=BookingStatus.PENDING).count()
            confirmed_bookings = await BoatBooking.filter(status=BookingStatus.CONFIRMED).count()
            completed_bookings = await BoatBooking.filter(status=BookingStatus.COMPLETED).count()
            cancelled_bookings = await BoatBooking.filter(status=BookingStatus.CANCELLED).count()
            
            # 金额统计
            bookings = await BoatBooking.all()
            total_booking_amount = sum(float(booking.total_amount) for booking in bookings)
            
            paid_bookings = await BoatBooking.filter(payment_status=PaymentStatus.PAID)
            paid_booking_amount = sum(float(booking.total_amount) for booking in paid_bookings)
            
            # 平均预约时长
            if bookings:
                total_duration = sum(float(booking.duration_hours) for booking in bookings)
                average_booking_duration = total_duration / len(bookings)
            else:
                average_booking_duration = 0.0
            
            # 近7天预约
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_bookings = await BoatBooking.filter(created_at__gte=seven_days_ago).count()
            
            return BookingStatsSchema(
                total_bookings=total_bookings,
                pending_bookings=pending_bookings,
                confirmed_bookings=confirmed_bookings,
                completed_bookings=completed_bookings,
                cancelled_bookings=cancelled_bookings,
                total_booking_amount=total_booking_amount,
                paid_booking_amount=paid_booking_amount,
                average_booking_duration=average_booking_duration,
                recent_bookings=recent_bookings
            )
        except Exception as e:
            return BookingStatsSchema(
                total_bookings=0,
                pending_bookings=0,
                confirmed_bookings=0,
                completed_bookings=0,
                cancelled_bookings=0,
                total_booking_amount=0.0,
                paid_booking_amount=0.0,
                average_booking_duration=0.0,
                recent_bookings=0
            )

    @staticmethod
    async def get_crew_stats() -> CrewStatsSchema:
        """获取船员统计数据"""
        try:
            total_crews = await Crew.all().count()
            active_crews = await Crew.filter(status=CrewStatus.ACTIVE).count()
            inactive_crews = await Crew.filter(status=CrewStatus.INACTIVE).count()
            
            # 评分统计
            crews = await Crew.all()
            if crews:
                total_rating = sum(float(crew.rating) for crew in crews)
                average_rating = total_rating / len(crews)
                # 统计有评分的船员数量（评分大于0）
                total_ratings = len([crew for crew in crews if float(crew.rating) > 0])
            else:
                average_rating = 0.0
                total_ratings = 0
            
            return CrewStatsSchema(
                total_crews=total_crews,
                active_crews=active_crews,
                inactive_crews=inactive_crews,
                average_rating=average_rating,
                total_ratings=total_ratings
            )
        except Exception as e:
            return CrewStatsSchema(
                total_crews=0,
                active_crews=0,
                inactive_crews=0,
                average_rating=0.0,
                total_ratings=0
            )

    @staticmethod
    async def get_financial_stats() -> FinancialStatsSchema:
        """获取财务统计数据"""
        try:
            # 订单收入
            paid_orders = await Order.filter(
                status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED]
            )
            order_revenue = sum(float(order.final_amount) for order in paid_orders)
            
            # 预约收入
            paid_bookings = await BoatBooking.filter(payment_status=PaymentStatus.PAID)
            booking_revenue = sum(float(booking.total_amount) for booking in paid_bookings)
            
            # 总收入
            total_revenue = order_revenue + booking_revenue
            
            # 平台抽成 5%
            platform_commission = total_revenue * 0.05
            
            # 商家收入 (订单95% + 预约40%)
            merchant_earnings = order_revenue * 0.95 + booking_revenue * 0.40
            
            # 船员收入 (预约60%)
            crew_earnings = booking_revenue * 0.60
            
            return FinancialStatsSchema(
                total_revenue=total_revenue,
                order_revenue=order_revenue,
                booking_revenue=booking_revenue,
                platform_commission=platform_commission,
                merchant_earnings=merchant_earnings,
                crew_earnings=crew_earnings
            )
        except Exception as e:
            return FinancialStatsSchema(
                total_revenue=0.0,
                order_revenue=0.0,
                booking_revenue=0.0,
                platform_commission=0.0,
                merchant_earnings=0.0,
                crew_earnings=0.0
            )

    @staticmethod
    async def get_recent_activity() -> RecentActivitySchema:
        """获取近期活动统计"""
        try:
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            recent_users = await User.filter(created_at__gte=seven_days_ago).count()
            recent_merchants = await Merchant.filter(created_at__gte=seven_days_ago).count()
            recent_orders = await Order.filter(created_at__gte=seven_days_ago).count()
            recent_bookings = await BoatBooking.filter(created_at__gte=seven_days_ago).count()
            recent_products = await Product.filter(created_at__gte=seven_days_ago).count()
            
            return RecentActivitySchema(
                recent_users=recent_users,
                recent_merchants=recent_merchants,
                recent_orders=recent_orders,
                recent_bookings=recent_bookings,
                recent_products=recent_products
            )
        except Exception as e:
            return RecentActivitySchema(
                recent_users=0,
                recent_merchants=0,
                recent_orders=0,
                recent_bookings=0,
                recent_products=0
            )

    @staticmethod
    async def get_dashboard_overview(current_user: User) -> ApiResponse[DashboardOverviewSchema]:
        """获取仪表盘总览数据"""
        try:
            # 检查管理员权限
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("需要管理员权限")
            
            # 获取所有统计数据
            user_stats = await DashboardService.get_user_stats()
            merchant_stats = await DashboardService.get_merchant_stats()
            product_stats = await DashboardService.get_product_stats()
            boat_stats = await DashboardService.get_boat_stats()
            order_stats = await DashboardService.get_order_stats()
            booking_stats = await DashboardService.get_booking_stats()
            crew_stats = await DashboardService.get_crew_stats()
            financial_stats = await DashboardService.get_financial_stats()
            recent_activity = await DashboardService.get_recent_activity()
            
            dashboard_data = DashboardOverviewSchema(
                user_stats=user_stats,
                merchant_stats=merchant_stats,
                product_stats=product_stats,
                boat_stats=boat_stats,
                order_stats=order_stats,
                booking_stats=booking_stats,
                crew_stats=crew_stats,
                financial_stats=financial_stats,
                recent_activity=recent_activity,
                last_updated=datetime.now()
            )
            
            return ResponseHelper.success(dashboard_data, "获取仪表盘数据成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取仪表盘数据失败: {str(e)}")

    @staticmethod
    async def get_dashboard_charts(current_user: User) -> ApiResponse[DashboardChartsSchema]:
        """获取仪表盘图表数据"""
        try:
            # 检查管理员权限
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("需要管理员权限")
            
            # 用户增长图表（近30天）
            user_growth_data = await DashboardService._get_user_growth_chart()
            
            # 订单趋势图表（近30天）
            order_trend_data = await DashboardService._get_order_trend_chart()
            
            # 预约趋势图表（近30天）
            booking_trend_data = await DashboardService._get_booking_trend_chart()
            
            # 收入图表（近30天）
            revenue_data = await DashboardService._get_revenue_chart()
            
            # 商品分类饼图
            category_pie_data = await DashboardService._get_category_pie_chart()
            
            # 船舶类型饼图
            boat_type_pie_data = await DashboardService._get_boat_type_pie_chart()
            
            charts_data = DashboardChartsSchema(
                user_growth_chart=user_growth_data,
                order_trend_chart=order_trend_data,
                booking_trend_chart=booking_trend_data,
                revenue_chart=revenue_data,
                category_pie_chart=category_pie_data,
                boat_type_pie_chart=boat_type_pie_data
            )
            
            return ResponseHelper.success(charts_data, "获取图表数据成功")
            
        except Exception as e:
            return ResponseHelper.server_error(f"获取图表数据失败: {str(e)}")

    @staticmethod
    async def _get_user_growth_chart() -> ChartDataSchema:
        """获取用户增长图表数据"""
        try:
            labels = []
            data = []
            
            # 近30天数据
            for i in range(29, -1, -1):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%m-%d")
                labels.append(date_str)
                
                # 统计该日新增用户数
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                count = await User.filter(
                    created_at__gte=start_of_day,
                    created_at__lt=end_of_day
                ).count()
                data.append(float(count))
            
            return ChartDataSchema(
                labels=labels,
                data=data,
                title="用户增长趋势（近30天）"
            )
        except Exception:
            return ChartDataSchema(labels=[], data=[], title="用户增长趋势")

    @staticmethod
    async def _get_order_trend_chart() -> ChartDataSchema:
        """获取订单趋势图表数据"""
        try:
            labels = []
            data = []
            
            for i in range(29, -1, -1):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%m-%d")
                labels.append(date_str)
                
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                count = await Order.filter(
                    created_at__gte=start_of_day,
                    created_at__lt=end_of_day
                ).count()
                data.append(float(count))
            
            return ChartDataSchema(
                labels=labels,
                data=data,
                title="订单趋势（近30天）"
            )
        except Exception:
            return ChartDataSchema(labels=[], data=[], title="订单趋势")

    @staticmethod
    async def _get_booking_trend_chart() -> ChartDataSchema:
        """获取预约趋势图表数据"""
        try:
            labels = []
            data = []
            
            for i in range(29, -1, -1):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%m-%d")
                labels.append(date_str)
                
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                count = await BoatBooking.filter(
                    created_at__gte=start_of_day,
                    created_at__lt=end_of_day
                ).count()
                data.append(float(count))
            
            return ChartDataSchema(
                labels=labels,
                data=data,
                title="预约趋势（近30天）"
            )
        except Exception:
            return ChartDataSchema(labels=[], data=[], title="预约趋势")

    @staticmethod
    async def _get_revenue_chart() -> ChartDataSchema:
        """获取收入图表数据"""
        try:
            labels = []
            data = []
            
            for i in range(29, -1, -1):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%m-%d")
                labels.append(date_str)
                
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                # 订单收入
                order_revenue = 0.0
                daily_orders = await Order.filter(
                    created_at__gte=start_of_day,
                    created_at__lt=end_of_day,
                    status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED]
                )
                for order in daily_orders:
                    order_revenue += float(order.final_amount)
                
                # 预约收入
                booking_revenue = 0.0
                daily_bookings = await BoatBooking.filter(
                    created_at__gte=start_of_day,
                    created_at__lt=end_of_day,
                    payment_status=PaymentStatus.PAID
                )
                for booking in daily_bookings:
                    booking_revenue += float(booking.total_amount)
                
                total_revenue = order_revenue + booking_revenue
                data.append(total_revenue)
            
            return ChartDataSchema(
                labels=labels,
                data=data,
                title="收入趋势（近30天）"
            )
        except Exception:
            return ChartDataSchema(labels=[], data=[], title="收入趋势")

    @staticmethod
    async def _get_category_pie_chart() -> ChartDataSchema:
        """获取商品分类饼图数据"""
        try:
            labels = []
            data = []
            
            for category in ProductCategory:
                count = await Product.filter(category=category).count()
                if count > 0:
                    labels.append(category.value)
                    data.append(float(count))
            
            return ChartDataSchema(
                labels=labels,
                data=data,
                title="商品分类分布"
            )
        except Exception:
            return ChartDataSchema(labels=[], data=[], title="商品分类分布")

    @staticmethod
    async def _get_boat_type_pie_chart() -> ChartDataSchema:
        """获取船舶类型饼图数据"""
        try:
            labels = []
            data = []
            
            for boat_type in BoatType:
                count = await Boat.filter(boat_type=boat_type).count()
                if count > 0:
                    labels.append(boat_type.value)
                    data.append(float(count))
            
            return ChartDataSchema(
                labels=labels,
                data=data,
                title="船舶类型分布"
            )
        except Exception:
            return ChartDataSchema(labels=[], data=[], title="船舶类型分布") 
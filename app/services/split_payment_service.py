from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.split_payment import SplitPayment, SplitRule, SplitType, SplitStatus
from app.models.booking import BoatBooking
from app.models.order import Order
from app.models.merchant import Merchant
from app.models.crew import Crew
from app.schemas.split_payment import (
    SplitRuleCreateSchema,
    SplitRuleResponseSchema,
    SplitPaymentResponseSchema,
    SplitPaymentDetailSchema,
    SplitPaymentQuerySchema,
    SplitPaymentStatsSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData


class SplitPaymentService:
    """分账服务类"""

    @staticmethod
    def _generate_split_number() -> str:
        """生成分账单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"SP{timestamp}{random_suffix}"

    @staticmethod
    async def create_split_rule(rule_data: SplitRuleCreateSchema) -> ApiResponse:
        """创建分账规则"""
        try:
            # 验证比例总和
            total_ratio = rule_data.platform_ratio + rule_data.merchant_ratio + rule_data.crew_ratio
            if total_ratio != 100:
                return ResponseHelper.error(f"分账比例总和必须为100%，当前为{total_ratio}%", 400)

            # 创建规则
            rule = await SplitRule.create(
                split_type=rule_data.split_type,
                platform_ratio=rule_data.platform_ratio,
                merchant_ratio=rule_data.merchant_ratio,
                crew_ratio=rule_data.crew_ratio,
                description=rule_data.description
            )

            rule_dict = await rule.to_dict()
            rule_response = SplitRuleResponseSchema(**rule_dict)
            return ResponseHelper.created(rule_response, "分账规则创建成功")

        except Exception as e:
            return ResponseHelper.server_error(f"创建分账规则失败: {str(e)}")

    @staticmethod
    async def get_active_split_rule(split_type: SplitType) -> Optional[SplitRule]:
        """获取激活的分账规则"""
        return await SplitRule.filter(
            split_type=split_type,
            is_active=True
        ).first()

    @staticmethod
    async def create_booking_split(booking: BoatBooking) -> ApiResponse:
        """创建预约分账"""
        try:
            # 获取分账规则
            split_rule = await SplitPaymentService.get_active_split_rule(SplitType.BOOKING)
            if not split_rule:
                return ResponseHelper.error("未找到预约分账规则", 404)

            # 计算分账金额
            total_amount = booking.total_amount
            platform_amount = total_amount * split_rule.platform_ratio / 100
            merchant_amount = total_amount * split_rule.merchant_ratio / 100
            crew_amount = total_amount * split_rule.crew_ratio / 100 if booking.assigned_crew_id else Decimal(0)

            # 如果没有船员，船员的部分归商家
            if not booking.assigned_crew_id:
                merchant_amount += crew_amount
                crew_amount = Decimal(0)

            # 创建分账记录
            split_payment = await SplitPayment.create(
                split_number=SplitPaymentService._generate_split_number(),
                split_type=SplitType.BOOKING,
                booking_id=booking.id,
                total_amount=total_amount,
                platform_amount=platform_amount,
                merchant_amount=merchant_amount,
                crew_amount=crew_amount,
                merchant_id=booking.merchant_id,
                crew_id=booking.assigned_crew_id,
                split_rule_id=split_rule.id,
                status=SplitStatus.PENDING,
                notes=f"预约单号: {booking.booking_number}"
            )

            # 模拟分账完成
            split_payment.status = SplitStatus.COMPLETED
            split_payment.completed_at = datetime.now()
            await split_payment.save()

            split_dict = await split_payment.to_dict()
            split_response = SplitPaymentResponseSchema(**split_dict)
            return ResponseHelper.success(split_response, "预约分账创建成功")

        except Exception as e:
            return ResponseHelper.server_error(f"创建预约分账失败: {str(e)}")

    @staticmethod
    async def create_order_split(order: Order) -> ApiResponse:
        """创建订单分账"""
        try:
            # 获取分账规则
            split_rule = await SplitPaymentService.get_active_split_rule(SplitType.ORDER)
            if not split_rule:
                return ResponseHelper.error("未找到订单分账规则", 404)

            # 计算分账金额
            total_amount = order.final_amount
            platform_amount = total_amount * split_rule.platform_ratio / 100
            merchant_amount = total_amount * split_rule.merchant_ratio / 100

            # 订单分账没有船员
            crew_amount = Decimal(0)

            # 创建分账记录
            split_payment = await SplitPayment.create(
                split_number=SplitPaymentService._generate_split_number(),
                split_type=SplitType.ORDER,
                order_id=order.id,
                total_amount=total_amount,
                platform_amount=platform_amount,
                merchant_amount=merchant_amount,
                crew_amount=crew_amount,
                merchant_id=order.merchant_id,
                split_rule_id=split_rule.id,
                status=SplitStatus.PENDING,
                notes=f"订单号: {order.order_number}"
            )

            # 模拟分账完成
            split_payment.status = SplitStatus.COMPLETED
            split_payment.completed_at = datetime.now()
            await split_payment.save()

            split_dict = await split_payment.to_dict()
            split_response = SplitPaymentResponseSchema(**split_dict)
            return ResponseHelper.success(split_response, "订单分账创建成功")

        except Exception as e:
            return ResponseHelper.server_error(f"创建订单分账失败: {str(e)}")

    @staticmethod
    async def get_split_payments(query_params: SplitPaymentQuerySchema) -> ApiResponse:
        """获取分账记录列表"""
        try:
            # 构建查询
            query = SplitPayment.all()

            if query_params.split_type:
                query = query.filter(split_type=query_params.split_type)
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.merchant_id:
                query = query.filter(merchant_id=query_params.merchant_id)
            if query_params.crew_id:
                query = query.filter(crew_id=query_params.crew_id)
            if query_params.start_date and query_params.start_date.strip():
                try:
                    # 尝试解析日期字符串，支持多种格式
                    start_date = datetime.fromisoformat(query_params.start_date.replace('Z', '+00:00'))
                    query = query.filter(created_at__gte=start_date)
                except (ValueError, TypeError):
                    try:
                        # 尝试其他常见格式
                        start_date = datetime.strptime(query_params.start_date, '%Y-%m-%d')
                        query = query.filter(created_at__gte=start_date)
                    except (ValueError, TypeError):
                        pass  # 忽略无效的日期格式
            if query_params.end_date and query_params.end_date.strip():
                try:
                    # 尝试解析日期字符串，支持多种格式
                    end_date = datetime.fromisoformat(query_params.end_date.replace('Z', '+00:00'))
                    query = query.filter(created_at__lte=end_date)
                except (ValueError, TypeError):
                    try:
                        # 尝试其他常见格式
                        end_date = datetime.strptime(query_params.end_date, '%Y-%m-%d')
                        query = query.filter(created_at__lte=end_date)
                    except (ValueError, TypeError):
                        pass  # 忽略无效的日期格式

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            split_payments = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            split_list = []
            for split in split_payments:
                split_dict = await split.to_dict()
                split_detail = SplitPaymentDetailSchema(**split_dict)
                split_list.append(split_detail)

            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=split_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取分账记录成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取分账记录失败: {str(e)}")

    @staticmethod
    async def get_split_stats(merchant_id: Optional[int] = None, crew_id: Optional[int] = None) -> ApiResponse:
        """获取分账统计"""
        try:
            query = SplitPayment.all()
            
            if merchant_id:
                query = query.filter(merchant_id=merchant_id)
            if crew_id:
                query = query.filter(crew_id=crew_id)

            # 统计各状态数量
            total_count = await query.count()
            pending_count = await query.filter(status=SplitStatus.PENDING).count()
            completed_count = await query.filter(status=SplitStatus.COMPLETED).count()
            failed_count = await query.filter(status=SplitStatus.FAILED).count()

            # 统计金额
            completed_splits = await query.filter(status=SplitStatus.COMPLETED).all()
            total_platform_amount = sum(float(s.platform_amount) for s in completed_splits)
            total_merchant_amount = sum(float(s.merchant_amount) for s in completed_splits)
            total_crew_amount = sum(float(s.crew_amount) for s in completed_splits)

            stats = SplitPaymentStatsSchema(
                total_count=total_count,
                pending_count=pending_count,
                completed_count=completed_count,
                failed_count=failed_count,
                total_platform_amount=total_platform_amount,
                total_merchant_amount=total_merchant_amount,
                total_crew_amount=total_crew_amount
            )

            return ResponseHelper.success(stats, "获取分账统计成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取分账统计失败: {str(e)}")


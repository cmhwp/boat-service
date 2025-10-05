from typing import Optional
from datetime import datetime
from decimal import Decimal

from app.models.review import BoatServiceReview, ProductReview, ReviewHelpful, ReviewStatus
from app.models.booking import BoatBooking, BookingStatus
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.models.merchant import Merchant
from app.schemas.review import (
    BoatServiceReviewCreateSchema,
    BoatServiceReviewResponseSchema,
    ProductReviewCreateSchema,
    ProductReviewResponseSchema,
    MerchantReplySchema,
    ReviewQuerySchema,
    ReviewStatsSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType


class ReviewService:
    """评价服务类"""

    @staticmethod
    async def create_boat_service_review(current_user: User, review_data: BoatServiceReviewCreateSchema) -> ApiResponse:
        """创建船艇服务评价"""
        try:
            # 获取预约
            booking = await BoatBooking.filter(
                id=review_data.booking_id,
                user=current_user,
                status=BookingStatus.COMPLETED
            ).select_related('boat', 'merchant').first()

            if not booking:
                return ResponseHelper.not_found("预约不存在或未完成")

            # 检查是否已评价
            existing_review = await BoatServiceReview.filter(booking=booking).first()
            if existing_review:
                return ResponseHelper.error("您已经评价过此次服务", 400)

            # 计算总体评分
            overall_rating = (
                review_data.service_rating + 
                review_data.boat_rating + 
                review_data.value_rating
            ) / 3.0

            # 创建评价
            review = await BoatServiceReview.create(
                booking=booking,
                user=current_user,
                boat=booking.boat,
                merchant=booking.merchant,
                service_rating=review_data.service_rating,
                boat_rating=review_data.boat_rating,
                value_rating=review_data.value_rating,
                overall_rating=Decimal(str(round(overall_rating, 2))),
                comment=review_data.comment,
                tags=review_data.tags
            )

            # 更新船艇平均评分
            await ReviewService._update_boat_rating(booking.boat_id)

            # 发送通知给商家
            await NotificationService.send_order_notification(
                user_id=booking.merchant.user_id,
                order_id=booking.id,
                notification_type=NotificationType.REVIEW_RECEIVED,
                extra_info={"review_id": review.id, "rating": float(overall_rating)}
            )

            review_dict = await review.to_dict()
            review_response = BoatServiceReviewResponseSchema(**review_dict)
            return ResponseHelper.created(review_response, "评价提交成功")

        except Exception as e:
            return ResponseHelper.server_error(f"提交评价失败: {str(e)}")

    @staticmethod
    async def create_product_review(current_user: User, review_data: ProductReviewCreateSchema) -> ApiResponse:
        """创建农产品评价"""
        try:
            # 获取订单项
            order_item = await OrderItem.filter(
                id=review_data.order_item_id
            ).select_related('order', 'product', 'order__merchant').first()

            if not order_item:
                return ResponseHelper.not_found("订单项不存在")

            # 验证订单归属
            if order_item.order.user_id != current_user.id:
                return ResponseHelper.forbidden("无权评价此订单")

            # 检查订单状态
            if order_item.order.status not in [OrderStatus.DELIVERED, OrderStatus.COMPLETED]:
                return ResponseHelper.error("订单未完成，无法评价", 400)

            # 检查是否已评价
            existing_review = await ProductReview.filter(order_item=order_item).first()
            if existing_review:
                return ResponseHelper.error("您已经评价过此商品", 400)

            # 计算总体评分
            overall_rating = (
                review_data.quality_rating + 
                review_data.freshness_rating + 
                review_data.packaging_rating
            ) / 3.0

            # 创建评价
            review = await ProductReview.create(
                order=order_item.order,
                order_item=order_item,
                user=current_user,
                product=order_item.product,
                merchant=order_item.order.merchant,
                quality_rating=review_data.quality_rating,
                freshness_rating=review_data.freshness_rating,
                packaging_rating=review_data.packaging_rating,
                overall_rating=Decimal(str(round(overall_rating, 2))),
                comment=review_data.comment,
                tags=review_data.tags,
                is_anonymous=review_data.is_anonymous
            )

            # 更新产品平均评分和销量
            await ReviewService._update_product_rating(order_item.product_id)

            # 发送通知给商家
            await NotificationService.send_order_notification(
                user_id=order_item.order.merchant.user_id,
                order_id=order_item.order.id,
                notification_type=NotificationType.REVIEW_RECEIVED,
                extra_info={"review_id": review.id, "rating": float(overall_rating)}
            )

            review_dict = await review.to_dict()
            review_response = ProductReviewResponseSchema(**review_dict)
            return ResponseHelper.created(review_response, "评价提交成功")

        except Exception as e:
            return ResponseHelper.server_error(f"提交评价失败: {str(e)}")

    @staticmethod
    async def _update_boat_rating(boat_id: int):
        """更新船艇平均评分"""
        try:
            from app.models.boat import Boat
            reviews = await BoatServiceReview.filter(
                boat_id=boat_id,
                status=ReviewStatus.PUBLISHED
            ).all()
            if reviews:
                total_rating = sum(float(review.overall_rating) for review in reviews)
                average_rating = Decimal(str(total_rating / len(reviews)))
                await Boat.filter(id=boat_id).update(rating=average_rating)
        except Exception:
            pass

    @staticmethod
    async def _update_product_rating(product_id: int):
        """更新产品平均评分"""
        try:
            from app.models.product import Product
            reviews = await ProductReview.filter(
                product_id=product_id,
                status=ReviewStatus.PUBLISHED
            ).all()
            if reviews:
                total_rating = sum(float(review.overall_rating) for review in reviews)
                average_rating = Decimal(str(total_rating / len(reviews)))
                await Product.filter(id=product_id).update(rating=average_rating)
        except Exception:
            pass

    @staticmethod
    async def get_boat_reviews(query_params: ReviewQuerySchema) -> ApiResponse:
        """获取船艇服务评价列表"""
        try:
            # 构建查询
            query = BoatServiceReview.filter(status=ReviewStatus.PUBLISHED).select_related('user', 'boat')

            if query_params.boat_id:
                query = query.filter(boat_id=query_params.boat_id)
            if query_params.merchant_id:
                query = query.filter(merchant_id=query_params.merchant_id)
            if query_params.rating_min:
                query = query.filter(overall_rating__gte=query_params.rating_min)
            if query_params.rating_max:
                query = query.filter(overall_rating__lte=query_params.rating_max)
            if query_params.has_images:
                query = query.exclude(images=[])
            if query_params.has_comment:
                query = query.exclude(comment__isnull=True)

            # 排序
            order_field = f"{'-' if query_params.sort_order == 'desc' else ''}{query_params.sort_by}"
            query = query.order_by(order_field)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            reviews = await query.offset(offset).limit(query_params.page_size)
            total = await query.count()

            # 转换为响应数据
            review_list = []
            for review in reviews:
                review_dict = await review.to_dict()
                review_response = BoatServiceReviewResponseSchema(**review_dict)
                review_list.append(review_response)

            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=review_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取评价列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取评价列表失败: {str(e)}")

    @staticmethod
    async def get_product_reviews(query_params: ReviewQuerySchema) -> ApiResponse:
        """获取农产品评价列表"""
        try:
            # 构建查询
            query = ProductReview.filter(status=ReviewStatus.PUBLISHED).select_related('user', 'product')

            if query_params.product_id:
                query = query.filter(product_id=query_params.product_id)
            if query_params.merchant_id:
                query = query.filter(merchant_id=query_params.merchant_id)
            if query_params.rating_min:
                query = query.filter(overall_rating__gte=query_params.rating_min)
            if query_params.rating_max:
                query = query.filter(overall_rating__lte=query_params.rating_max)
            if query_params.has_images:
                query = query.exclude(images=[])
            if query_params.has_comment:
                query = query.exclude(comment__isnull=True)

            # 排序
            order_field = f"{'-' if query_params.sort_order == 'desc' else ''}{query_params.sort_by}"
            query = query.order_by(order_field)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            reviews = await query.offset(offset).limit(query_params.page_size)
            total = await query.count()

            # 转换为响应数据
            review_list = []
            for review in reviews:
                review_dict = await review.to_dict()
                review_response = ProductReviewResponseSchema(**review_dict)
                review_list.append(review_response)

            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=review_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取评价列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取评价列表失败: {str(e)}")

    @staticmethod
    async def reply_boat_review(current_user: User, review_id: int, reply_data: MerchantReplySchema) -> ApiResponse:
        """商家回复船艇服务评价"""
        try:
            # 检查是否是商家
            merchant = await Merchant.filter(user=current_user).first()
            if not merchant:
                return ResponseHelper.forbidden("只有商家可以回复评价")

            # 获取评价
            review = await BoatServiceReview.filter(
                id=review_id,
                merchant=merchant
            ).first()

            if not review:
                return ResponseHelper.not_found("评价不存在")

            # 更新回复
            review.merchant_reply = reply_data.reply_content
            review.replied_at = datetime.now()
            await review.save()

            review_dict = await review.to_dict()
            review_response = BoatServiceReviewResponseSchema(**review_dict)
            return ResponseHelper.success(review_response, "回复成功")

        except Exception as e:
            return ResponseHelper.server_error(f"回复失败: {str(e)}")

    @staticmethod
    async def reply_product_review(current_user: User, review_id: int, reply_data: MerchantReplySchema) -> ApiResponse:
        """商家回复农产品评价"""
        try:
            # 检查是否是商家
            merchant = await Merchant.filter(user=current_user).first()
            if not merchant:
                return ResponseHelper.forbidden("只有商家可以回复评价")

            # 获取评价
            review = await ProductReview.filter(
                id=review_id,
                merchant=merchant
            ).first()

            if not review:
                return ResponseHelper.not_found("评价不存在")

            # 更新回复
            review.merchant_reply = reply_data.reply_content
            review.replied_at = datetime.now()
            await review.save()

            review_dict = await review.to_dict()
            review_response = ProductReviewResponseSchema(**review_dict)
            return ResponseHelper.success(review_response, "回复成功")

        except Exception as e:
            return ResponseHelper.server_error(f"回复失败: {str(e)}")

    @staticmethod
    async def mark_review_helpful(current_user: User, review_type: str, review_id: int) -> ApiResponse:
        """标记评价有帮助"""
        try:
            # 检查是否已点赞
            existing_helpful = await ReviewHelpful.filter(
                user=current_user,
                review_type=review_type,
                review_id=review_id
            ).first()

            if existing_helpful:
                return ResponseHelper.error("您已经点赞过此评价", 400)

            # 创建点赞记录
            await ReviewHelpful.create(
                user=current_user,
                review_type=review_type,
                review_id=review_id
            )

            # 更新评价点赞数
            if review_type == "boat_service":
                await BoatServiceReview.filter(id=review_id).update(
                    helpful_count=BoatServiceReview.filter(id=review_id).first().helpful_count + 1
                )
            elif review_type == "product":
                await ProductReview.filter(id=review_id).update(
                    helpful_count=ProductReview.filter(id=review_id).first().helpful_count + 1
                )

            return ResponseHelper.success(None, "点赞成功")

        except Exception as e:
            return ResponseHelper.server_error(f"点赞失败: {str(e)}")


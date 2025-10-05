from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.review_service import ReviewService
from app.schemas.review import (
    BoatServiceReviewCreateSchema,
    ProductReviewCreateSchema,
    MerchantReplySchema,
    ReviewQuerySchema
)
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/reviews", tags=["评价管理"])


# ============= 船艇服务评价 =============

@router.post("/boat-service", response_model=ApiResponse, summary="创建船艇服务评价")
async def create_boat_service_review(
    review_data: BoatServiceReviewCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """创建船艇服务评价（用户完成预约后）"""
    return await ReviewService.create_boat_service_review(current_user, review_data)


@router.get("/boat-service", response_model=ApiResponse, summary="获取船艇服务评价列表")
async def get_boat_service_reviews(
    query: ReviewQuerySchema = Depends()
):
    """获取船艇服务评价列表（公开）"""
    return await ReviewService.get_boat_reviews(query)


@router.post("/boat-service/{review_id}/reply", response_model=ApiResponse, summary="回复船艇服务评价")
async def reply_boat_service_review(
    review_id: int,
    reply_data: MerchantReplySchema,
    current_user: User = Depends(require_role([UserRole.MERCHANT]))
):
    """商家回复船艇服务评价"""
    return await ReviewService.reply_boat_review(current_user, review_id, reply_data)


# ============= 农产品评价 =============

@router.post("/product", response_model=ApiResponse, summary="创建农产品评价")
async def create_product_review(
    review_data: ProductReviewCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """创建农产品评价（用户收货后）"""
    return await ReviewService.create_product_review(current_user, review_data)


@router.get("/product", response_model=ApiResponse, summary="获取农产品评价列表")
async def get_product_reviews(
    query: ReviewQuerySchema = Depends()
):
    """获取农产品评价列表（公开）"""
    return await ReviewService.get_product_reviews(query)


@router.post("/product/{review_id}/reply", response_model=ApiResponse, summary="回复农产品评价")
async def reply_product_review(
    review_id: int,
    reply_data: MerchantReplySchema,
    current_user: User = Depends(require_role([UserRole.MERCHANT]))
):
    """商家回复农产品评价"""
    return await ReviewService.reply_product_review(current_user, review_id, reply_data)


# ============= 评价互动 =============

@router.post("/{review_type}/{review_id}/helpful", response_model=ApiResponse, summary="标记评价有帮助")
async def mark_review_helpful(
    review_type: str,  # boat_service / product
    review_id: int,
    current_user: User = Depends(get_current_user)
):
    """标记评价有帮助"""
    return await ReviewService.mark_review_helpful(current_user, review_type, review_id)


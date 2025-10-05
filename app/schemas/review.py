from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class BoatServiceReviewCreateSchema(BaseModel):
    """船艇服务评价创建"""
    booking_id: int = Field(..., description="预约ID")
    service_rating: int = Field(..., ge=1, le=5, description="服务质量评分")
    boat_rating: int = Field(..., ge=1, le=5, description="船艇状况评分")
    value_rating: int = Field(..., ge=1, le=5, description="性价比评分")
    comment: Optional[str] = Field(None, description="评价内容")
    tags: List[str] = Field(default_factory=list, description="评价标签")


class BoatServiceReviewResponseSchema(BaseModel):
    """船艇服务评价响应"""
    id: int
    booking_id: int
    user_id: int
    boat_id: int
    merchant_id: int
    service_rating: int
    boat_rating: int
    value_rating: int
    overall_rating: float
    comment: Optional[str]
    images: List[str]
    tags: List[str]
    status: str
    merchant_reply: Optional[str]
    replied_at: Optional[datetime]
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    user: Optional[dict]
    boat: Optional[dict]


class ProductReviewCreateSchema(BaseModel):
    """农产品评价创建"""
    order_id: int = Field(..., description="订单ID")
    order_item_id: int = Field(..., description="订单项ID")
    quality_rating: int = Field(..., ge=1, le=5, description="质量评分")
    freshness_rating: int = Field(..., ge=1, le=5, description="新鲜度评分")
    packaging_rating: int = Field(..., ge=1, le=5, description="包装评分")
    comment: Optional[str] = Field(None, description="评价内容")
    tags: List[str] = Field(default_factory=list, description="评价标签")
    is_anonymous: bool = Field(False, description="是否匿名")


class ProductReviewResponseSchema(BaseModel):
    """农产品评价响应"""
    id: int
    order_id: int
    order_item_id: int
    user_id: Optional[int]
    product_id: int
    merchant_id: int
    quality_rating: int
    freshness_rating: int
    packaging_rating: int
    overall_rating: float
    comment: Optional[str]
    images: List[str]
    tags: List[str]
    status: str
    merchant_reply: Optional[str]
    replied_at: Optional[datetime]
    helpful_count: int
    is_anonymous: bool
    created_at: datetime
    updated_at: datetime
    user: Optional[dict]
    product: Optional[dict]


class ReviewImageUploadSchema(BaseModel):
    """评价图片上传"""
    review_type: str = Field(..., description="评价类型: boat_service/product")
    review_id: int = Field(..., description="评价ID")


class MerchantReplySchema(BaseModel):
    """商家回复"""
    reply_content: str = Field(..., min_length=1, max_length=500, description="回复内容")


class ReviewQuerySchema(BaseModel):
    """评价查询"""
    boat_id: Optional[int] = None
    product_id: Optional[int] = None
    merchant_id: Optional[int] = None
    rating_min: Optional[int] = Field(None, ge=1, le=5)
    rating_max: Optional[int] = Field(None, ge=1, le=5)
    has_images: Optional[bool] = None
    has_comment: Optional[bool] = None
    sort_by: str = Field("created_at", description="排序字段: created_at/overall_rating/helpful_count")
    sort_order: str = Field("desc", description="排序方向: asc/desc")
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=50)


class ReviewStatsSchema(BaseModel):
    """评价统计"""
    total_count: int
    average_rating: float
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int
    has_images_count: int
    has_comment_count: int


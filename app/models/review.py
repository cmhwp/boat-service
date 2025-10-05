from tortoise import fields
from tortoise.models import Model
from enum import Enum


class ReviewStatus(str, Enum):
    """评价状态枚举"""
    PUBLISHED = "published"  # 已发布
    HIDDEN = "hidden"        # 已隐藏
    DELETED = "deleted"      # 已删除


class BoatServiceReview(Model):
    """船艇服务评价模型"""
    
    id = fields.BigIntField(pk=True, description="评价ID")
    
    # 评分（1-5星）
    service_rating = fields.IntField(description="服务质量评分")
    boat_rating = fields.IntField(description="船艇状况评分")
    value_rating = fields.IntField(description="性价比评分")
    overall_rating = fields.DecimalField(max_digits=3, decimal_places=2, description="总体评分")
    
    # 评价内容
    comment = fields.TextField(null=True, description="评价内容")
    images = fields.JSONField(default=list, description="评价图片")
    
    # 标签
    tags = fields.JSONField(default=list, description="评价标签")
    
    # 状态
    status = fields.CharEnumField(ReviewStatus, default=ReviewStatus.PUBLISHED, description="评价状态")
    
    # 商家回复
    merchant_reply = fields.TextField(null=True, description="商家回复")
    replied_at = fields.DatetimeField(null=True, description="回复时间")
    
    # 点赞数
    helpful_count = fields.IntField(default=0, description="有帮助数")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    booking = fields.ForeignKeyField('models.BoatBooking', related_name='service_reviews', description="关联预约")
    user = fields.ForeignKeyField('models.User', related_name='boat_service_reviews', description="评价用户")
    boat = fields.ForeignKeyField('models.Boat', related_name='service_reviews', description="评价船艇")
    merchant = fields.ForeignKeyField('models.Merchant', related_name='service_reviews', description="商家")

    class Meta:
        table = "boat_service_review"
        table_description = "船艇服务评价表"

    def __str__(self):
        return f"BoatServiceReview(id={self.id}, overall_rating={self.overall_rating})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('booking', 'user', 'boat', 'merchant')
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "boat_id": self.boat_id,
            "merchant_id": self.merchant_id,
            "service_rating": self.service_rating,
            "boat_rating": self.boat_rating,
            "value_rating": self.value_rating,
            "overall_rating": float(self.overall_rating),
            "comment": self.comment,
            "images": self.images,
            "tags": self.tags,
            "status": self.status,
            "merchant_reply": self.merchant_reply,
            "replied_at": self.replied_at,
            "helpful_count": self.helpful_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user": await self.user.to_dict() if self.user else None,
            "boat": await self.boat.to_dict() if self.boat else None,
        }


class ProductReview(Model):
    """农产品评价模型"""
    
    id = fields.BigIntField(pk=True, description="评价ID")
    
    # 评分（1-5星）
    quality_rating = fields.IntField(description="质量评分")
    freshness_rating = fields.IntField(description="新鲜度评分")
    packaging_rating = fields.IntField(description="包装评分")
    overall_rating = fields.DecimalField(max_digits=3, decimal_places=2, description="总体评分")
    
    # 评价内容
    comment = fields.TextField(null=True, description="评价内容")
    images = fields.JSONField(default=list, description="评价图片")
    
    # 标签
    tags = fields.JSONField(default=list, description="评价标签")
    
    # 状态
    status = fields.CharEnumField(ReviewStatus, default=ReviewStatus.PUBLISHED, description="评价状态")
    
    # 商家回复
    merchant_reply = fields.TextField(null=True, description="商家回复")
    replied_at = fields.DatetimeField(null=True, description="回复时间")
    
    # 点赞数
    helpful_count = fields.IntField(default=0, description="有帮助数")
    
    # 是否匿名
    is_anonymous = fields.BooleanField(default=False, description="是否匿名")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    order = fields.ForeignKeyField('models.Order', related_name='product_reviews', description="关联订单")
    order_item = fields.ForeignKeyField('models.OrderItem', related_name='reviews', description="关联订单项")
    user = fields.ForeignKeyField('models.User', related_name='product_reviews', description="评价用户")
    product = fields.ForeignKeyField('models.Product', related_name='reviews', description="评价产品")
    merchant = fields.ForeignKeyField('models.Merchant', related_name='product_reviews', description="商家")

    class Meta:
        table = "product_review"
        table_description = "农产品评价表"

    def __str__(self):
        return f"ProductReview(id={self.id}, overall_rating={self.overall_rating})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('order', 'order_item', 'user', 'product', 'merchant')
        
        user_info = None
        if not self.is_anonymous:
            user_info = await self.user.to_dict() if self.user else None
        else:
            user_info = {
                "id": self.user_id,
                "username": "匿名用户",
                "avatar": None
            }
        
        return {
            "id": self.id,
            "order_id": self.order_id,
            "order_item_id": self.order_item_id,
            "user_id": self.user_id if not self.is_anonymous else None,
            "product_id": self.product_id,
            "merchant_id": self.merchant_id,
            "quality_rating": self.quality_rating,
            "freshness_rating": self.freshness_rating,
            "packaging_rating": self.packaging_rating,
            "overall_rating": float(self.overall_rating),
            "comment": self.comment,
            "images": self.images,
            "tags": self.tags,
            "status": self.status,
            "merchant_reply": self.merchant_reply,
            "replied_at": self.replied_at,
            "helpful_count": self.helpful_count,
            "is_anonymous": self.is_anonymous,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user": user_info,
            "product": await self.product.to_dict() if self.product else None,
        }


class ReviewHelpful(Model):
    """评价点赞记录模型"""
    
    id = fields.BigIntField(pk=True, description="记录ID")
    
    # 评价类型
    review_type = fields.CharField(max_length=20, description="评价类型")  # boat_service / product
    review_id = fields.BigIntField(description="评价ID")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    # 外键关系
    user = fields.ForeignKeyField('models.User', related_name='review_helpful_records', description="点赞用户")

    class Meta:
        table = "review_helpful"
        table_description = "评价点赞记录表"
        unique_together = (("user", "review_type", "review_id"),)  # 同一用户对同一评价只能点赞一次

    def __str__(self):
        return f"ReviewHelpful(user_id={self.user_id}, review_type={self.review_type}, review_id={self.review_id})"


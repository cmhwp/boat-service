from tortoise import fields
from tortoise.models import Model
from enum import Enum


class ProductStatus(str, Enum):
    """商品状态枚举"""
    AVAILABLE = "available"  # 可售
    SOLD_OUT = "sold_out"  # 售罄
    INACTIVE = "inactive"  # 下架


class ProductCategory(str, Enum):
    """商品分类枚举"""
    FRUIT = "fruit"  # 水果
    VEGETABLE = "vegetable"  # 蔬菜
    GRAIN = "grain"  # 粮食
    SEAFOOD = "seafood"  # 海鲜
    OTHER = "other"  # 其他


class Product(Model):
    """农产品模型"""
    
    id = fields.BigIntField(pk=True, description="商品ID")
    name = fields.CharField(max_length=100, description="商品名称")
    category = fields.CharEnumField(ProductCategory, default=ProductCategory.OTHER, description="商品分类")
    description = fields.TextField(null=True, description="商品描述")
    price = fields.DecimalField(max_digits=10, decimal_places=2, description="商品价格")
    stock = fields.IntField(default=0, description="库存数量")
    unit = fields.CharField(max_length=20, default="份", description="计量单位")
    images = fields.JSONField(default=list, description="商品图片列表")
    rating = fields.DecimalField(max_digits=3, decimal_places=2, default=0.00, description="评分")
    sales_count = fields.IntField(default=0, description="销售数量")
    status = fields.CharEnumField(ProductStatus, default=ProductStatus.AVAILABLE, description="状态")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关系
    merchant = fields.ForeignKeyField('models.Merchant', related_name='products', description="所属商家")

    class Meta:
        table = "product"
        table_description = "农产品表"

    def __str__(self):
        return f"Product(id={self.id}, name={self.name}, price={self.price})"

    async def to_dict(self) -> dict:
        """转换为字典"""
        await self.fetch_related('merchant')
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": float(self.price),
            "stock": self.stock,
            "unit": self.unit,
            "images": self.images,
            "rating": float(self.rating),
            "sales_count": self.sales_count,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "merchant": await self.merchant.to_dict() if self.merchant else None
        } 
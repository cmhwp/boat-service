from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from app.models.product import ProductStatus, ProductCategory


class ProductCreateSchema(BaseModel):
    """商品创建数据验证"""
    name: str = Field(..., max_length=100, description="商品名称")
    category: ProductCategory = Field(default=ProductCategory.OTHER, description="商品分类")
    description: Optional[str] = Field(None, description="商品描述")
    price: Decimal = Field(..., gt=0, description="商品价格")
    stock: int = Field(..., ge=0, description="库存数量")
    unit: str = Field(default="份", max_length=20, description="计量单位")
    images: Optional[List[str]] = Field(default=[], description="商品图片列表")

    @validator('images')
    def validate_images(cls, v):
        if v and len(v) > 10:
            raise ValueError('最多只能上传10张图片')
        return v


class ProductUpdateSchema(BaseModel):
    """商品更新数据验证"""
    name: Optional[str] = Field(None, max_length=100, description="商品名称")
    category: Optional[ProductCategory] = Field(None, description="商品分类")
    description: Optional[str] = Field(None, description="商品描述")
    price: Optional[Decimal] = Field(None, gt=0, description="商品价格")
    stock: Optional[int] = Field(None, ge=0, description="库存数量")
    unit: Optional[str] = Field(None, max_length=20, description="计量单位")
    images: Optional[List[str]] = Field(None, description="商品图片列表")
    status: Optional[ProductStatus] = Field(None, description="状态")

    @validator('images')
    def validate_images(cls, v):
        if v and len(v) > 10:
            raise ValueError('最多只能上传10张图片')
        return v


class ProductResponseSchema(BaseModel):
    """商品响应数据"""
    id: int = Field(..., description="商品ID")
    merchant_id: int = Field(..., description="商家ID")
    name: str = Field(..., description="商品名称")
    category: ProductCategory = Field(..., description="商品分类")
    description: Optional[str] = Field(None, description="商品描述")
    price: float = Field(..., description="商品价格")
    stock: int = Field(..., description="库存数量")
    unit: str = Field(..., description="计量单位")
    images: List[str] = Field(default=[], description="商品图片列表")
    rating: float = Field(..., description="评分")
    sales_count: int = Field(..., description="销售数量")
    status: ProductStatus = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ProductDetailSchema(ProductResponseSchema):
    """商品详情数据"""
    merchant: Optional[dict] = Field(None, description="商家信息")


class ProductListItemSchema(BaseModel):
    """商品列表项数据"""
    id: int = Field(..., description="商品ID")
    merchant_id: int = Field(..., description="商家ID")
    name: str = Field(..., description="商品名称")
    category: ProductCategory = Field(..., description="商品分类")
    price: float = Field(..., description="商品价格")
    stock: int = Field(..., description="库存数量")
    unit: str = Field(..., description="计量单位")
    images: List[str] = Field(default=[], description="商品图片列表")
    rating: float = Field(..., description="评分")
    sales_count: int = Field(..., description="销售数量")
    status: ProductStatus = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ProductStockUpdateSchema(BaseModel):
    """商品库存更新数据验证"""
    stock: int = Field(..., ge=0, description="库存数量")
    status: Optional[ProductStatus] = Field(None, description="状态")


class ProductSearchSchema(BaseModel):
    """商品搜索数据验证"""
    keyword: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    category: Optional[ProductCategory] = Field(None, description="商品分类")
    min_price: Optional[Decimal] = Field(None, ge=0, description="最低价格")
    max_price: Optional[Decimal] = Field(None, ge=0, description="最高价格")
    status: Optional[ProductStatus] = Field(None, description="状态")
    merchant_id: Optional[int] = Field(None, description="商家ID")

    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('最高价格不能小于最低价格')
        return v


# =================== 管理员相关模式 ===================

class AdminProductQuerySchema(BaseModel):
    """管理员商品查询数据验证"""
    merchant_id: Optional[int] = Field(None, description="商家ID过滤")
    category: Optional[ProductCategory] = Field(None, description="商品分类过滤")
    status: Optional[ProductStatus] = Field(None, description="状态过滤")
    name: Optional[str] = Field(None, description="商品名称搜索")
    min_price: Optional[Decimal] = Field(None, ge=0, description="最低价格")
    max_price: Optional[Decimal] = Field(None, ge=0, description="最高价格")
    low_stock: Optional[bool] = Field(None, description="低库存筛选（库存<10）")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")

    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('最高价格不能小于最低价格')
        return v


class AdminProductOperationSchema(BaseModel):
    """管理员商品操作数据验证"""
    operation: str = Field(..., description="操作类型：deactivate（下架）| activate（上架）| sold_out（售罄）")
    reason: str = Field(..., min_length=5, max_length=500, description="操作原因")
    notes: Optional[str] = Field(None, max_length=500, description="管理员备注")

    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['deactivate', 'activate', 'sold_out']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_operations)}')
        return v


class AdminProductListItemSchema(ProductListItemSchema):
    """管理员商品列表项数据"""
    merchant_name: str = Field(..., description="商家名称")
    order_count: int = Field(default=0, description="订单数量")
    total_sales: float = Field(default=0.0, description="总销售额")

    class Config:
        from_attributes = True


class AdminProductDetailSchema(ProductDetailSchema):
    """管理员商品详情数据"""
    order_count: int = Field(default=0, description="订单数量")
    total_sales: float = Field(default=0.0, description="总销售额")
    recent_orders: List[dict] = Field(default=[], description="最近订单记录") 
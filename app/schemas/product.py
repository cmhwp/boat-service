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
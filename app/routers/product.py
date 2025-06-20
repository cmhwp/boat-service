from fastapi import APIRouter, Depends, Query, Path, UploadFile, File
from typing import Optional
from app.schemas.product import (
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductResponseSchema,
    ProductDetailSchema,
    ProductListItemSchema,
    ProductStockUpdateSchema,
    ProductSearchSchema,
    AdminProductQuerySchema,
    AdminProductOperationSchema,
    AdminProductListItemSchema,
    AdminProductDetailSchema
)
from app.schemas.response import ApiResponse, PaginatedData, ResponseHelper
from app.schemas.user import UploadResponseSchema
from app.services.product_service import ProductService
from app.utils.auth import get_current_user, require_admin
from app.utils.cos_utils import cos_uploader
from app.config.cos_config import cos_config
from app.models.user import User
from app.models.product import ProductStatus, ProductCategory

router = APIRouter(prefix="/products", tags=["products"])


# 图片上传API
@router.post("/upload-image", response_model=ApiResponse[UploadResponseSchema], summary="上传商品图片")
async def upload_product_image(
    file: UploadFile = File(..., description="商品图片文件"),
    current_user: User = Depends(get_current_user)
):
    """
    上传商品图片
    
    - **file**: 商品图片文件（支持jpg、jpeg、png、gif、webp格式，最大10MB）
    
    返回上传后的图片URL，用于添加或更新商品时填写images字段
    """
    try:
        file_url, upload_info = await cos_uploader.upload_image(file, cos_config.PRODUCT_PREFIX)
        
        response_data = UploadResponseSchema(
            url=upload_info['url'],
            filename=upload_info['filename'],
            size=upload_info['size'],
            content_type=upload_info['content_type']
        )
        
        return ResponseHelper.success(response_data, "商品图片上传成功")
    except Exception as e:
        return ResponseHelper.error(f"上传失败: {str(e)}", 500)


# 商家端API
@router.post("/", response_model=ApiResponse[ProductResponseSchema], summary="添加商品")
async def create_product(
    product_data: ProductCreateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    添加商品（商家端）
    
    - **name**: 商品名称（必填，最大100字符）
    - **category**: 商品分类（默认其他）
    - **description**: 商品描述（可选）
    - **price**: 商品价格（必填，大于0）
    - **stock**: 库存数量（必填，大于等于0）
    - **unit**: 计量单位（默认"份"）
    - **images**: 商品图片列表（可选，最多10张）
    
    只有审核通过的商家才能添加商品
    """
    return await ProductService.create_product(current_user, product_data)


@router.get("/my", response_model=ApiResponse[PaginatedData[ProductListItemSchema]], summary="获取我的商品列表")
async def get_my_products(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    status: Optional[ProductStatus] = Query(None, description="状态过滤"),
    category: Optional[ProductCategory] = Query(None, description="分类过滤"),
    current_user: User = Depends(get_current_user)
):
    """获取我的商品列表（商家端）"""
    return await ProductService.get_my_products(current_user, page, page_size, status, category)


@router.get("/my/{product_id}", response_model=ApiResponse[ProductDetailSchema], summary="获取我的商品详情")
async def get_my_product_detail(
    product_id: int = Path(..., description="商品ID"),
    current_user: User = Depends(get_current_user)
):
    """获取我的商品详情（商家端）"""
    return await ProductService.get_product_detail(current_user, product_id)


@router.put("/my/{product_id}", response_model=ApiResponse[ProductResponseSchema], summary="更新我的商品信息")
async def update_my_product(
    product_id: int = Path(..., description="商品ID"),
    product_data: ProductUpdateSchema = ...,
    current_user: User = Depends(get_current_user)
):
    """
    更新我的商品信息（商家端）
    
    - **name**: 商品名称（可选）
    - **category**: 商品分类（可选）
    - **description**: 商品描述（可选）
    - **price**: 商品价格（可选）
    - **stock**: 库存数量（可选）
    - **unit**: 计量单位（可选）
    - **images**: 商品图片列表（可选）
    - **status**: 状态（可选）
    """
    return await ProductService.update_product(current_user, product_id, product_data)


@router.delete("/my/{product_id}", response_model=ApiResponse[dict], summary="删除我的商品")
async def delete_my_product(
    product_id: int = Path(..., description="商品ID"),
    current_user: User = Depends(get_current_user)
):
    """删除我的商品（商家端）- 软删除，将状态设置为inactive"""
    return await ProductService.delete_product(current_user, product_id)


@router.patch("/my/{product_id}/stock", response_model=ApiResponse[ProductResponseSchema], summary="更新商品库存")
async def update_product_stock(
    product_id: int = Path(..., description="商品ID"),
    stock_data: ProductStockUpdateSchema = ...,
    current_user: User = Depends(get_current_user)
):
    """
    更新商品库存（商家端）
    
    - **stock**: 库存数量（必填，大于等于0）
    - **status**: 状态（可选）
    
    库存为0时自动设置为售罄状态
    """
    return await ProductService.update_product_stock(current_user, product_id, stock_data)


# 用户端API
@router.get("/search", response_model=ApiResponse[PaginatedData[ProductListItemSchema]], summary="搜索商品")
async def search_products(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[ProductCategory] = Query(None, description="商品分类"),
    min_price: Optional[float] = Query(None, description="最低价格", ge=0),
    max_price: Optional[float] = Query(None, description="最高价格", ge=0),
    merchant_id: Optional[int] = Query(None, description="商家ID")
):
    """
    搜索商品（用户端）
    
    - **keyword**: 搜索关键词（在商品名称和描述中搜索）
    - **category**: 商品分类过滤
    - **min_price**: 最低价格
    - **max_price**: 最高价格
    - **merchant_id**: 商家ID过滤
    
    只显示状态为可售且所属商家已审核通过的商品
    按销量和创建时间排序
    """
    search_data = ProductSearchSchema(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        merchant_id=merchant_id
    )
    return await ProductService.search_products(search_data, page, page_size)


@router.get("/category/{category}", response_model=ApiResponse[PaginatedData[ProductListItemSchema]], summary="按分类获取商品")
async def get_products_by_category(
    category: ProductCategory = Path(..., description="商品分类"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100)
):
    """按分类获取商品列表（用户端）"""
    return await ProductService.get_products_by_category(category, page, page_size)


@router.get("/popular", response_model=ApiResponse[PaginatedData[ProductListItemSchema]], summary="获取热门商品")
async def get_popular_products(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100)
):
    """
    获取热门商品（用户端）
    
    按销量和评分排序显示热门商品
    """
    return await ProductService.get_popular_products(page, page_size)


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailSchema], summary="获取商品详情")
async def get_product_detail(
    product_id: int = Path(..., description="商品ID")
):
    """获取商品详情（用户端）"""
    return await ProductService.get_public_product_detail(product_id)


# =================== 管理员端商品管理接口 ===================

@router.get("/admin/all", response_model=ApiResponse[PaginatedData[AdminProductListItemSchema]], summary="管理员获取所有商品")
async def admin_get_all_products(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    merchant_id: Optional[int] = Query(None, description="商家ID过滤"),
    category: Optional[ProductCategory] = Query(None, description="商品分类过滤"),
    status: Optional[ProductStatus] = Query(None, description="状态过滤"),
    name: Optional[str] = Query(None, description="商品名称搜索"),
    min_price: Optional[float] = Query(None, description="最低价格", ge=0),
    max_price: Optional[float] = Query(None, description="最高价格", ge=0),
    low_stock: Optional[bool] = Query(None, description="低库存筛选（库存<10）"),
    current_user: User = Depends(require_admin)
):
    """
    管理员获取所有商品列表
    
    - **merchant_id**: 商家ID过滤（可选）
    - **category**: 商品分类过滤（可选）
    - **status**: 状态过滤（可选）
    - **name**: 商品名称搜索（可选）
    - **min_price**: 最低价格（可选）
    - **max_price**: 最高价格（可选）
    - **low_stock**: 低库存筛选（可选）
    
    包含商家信息、订单统计、销售统计等完整数据
    """
    from decimal import Decimal
    query_params = AdminProductQuerySchema(
        merchant_id=merchant_id,
        category=category,
        status=status,
        name=name,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        low_stock=low_stock,
        page=page,
        page_size=page_size
    )
    return await ProductService.admin_get_all_products(current_user, query_params)


@router.get("/admin/{product_id}", response_model=ApiResponse[AdminProductDetailSchema], summary="管理员获取商品详情")
async def admin_get_product_detail(
    product_id: int = Path(..., description="商品ID"),
    current_user: User = Depends(require_admin)
):
    """
    管理员获取商品详情
    
    包含完整的商品信息、商家信息、订单统计、最近订单记录等
    """
    return await ProductService.admin_get_product_detail(current_user, product_id)


@router.post("/admin/{product_id}/operate", response_model=ApiResponse[ProductResponseSchema], summary="管理员操作商品")
async def admin_operate_product(
    product_id: int = Path(..., description="商品ID"),
    operation_data: AdminProductOperationSchema = ...,
    current_user: User = Depends(require_admin)
):
    """
    管理员操作商品
    
    - **operation**: 操作类型（必填）
      - deactivate: 下架商品（设为停售状态）
      - activate: 上架商品（设为可售状态）
      - sold_out: 设置售罄状态
    - **reason**: 操作原因（必填）
    - **notes**: 管理员备注（可选）
    
    用于处理违规商品或管理商品状态
    操作记录会保存在商品描述中
    """
    return await ProductService.admin_operate_product(current_user, product_id, operation_data)


@router.get("/admin/statistics", response_model=ApiResponse[dict], summary="管理员获取商品统计")
async def admin_get_product_statistics(
    current_user: User = Depends(require_admin)
):
    """
    管理员获取商品统计
    
    包含：
    - 各状态商品数量统计
    - 低库存商品统计
    - 各分类商品分布
    - 总订单数和销售额统计
    """
    return await ProductService.admin_get_product_statistics(current_user) 
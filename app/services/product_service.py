from typing import Optional, List
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.expressions import Q
from app.models.product import Product, ProductStatus, ProductCategory
from app.models.merchant import Merchant, MerchantStatus
from app.models.user import User, UserRole
from app.schemas.product import (
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductResponseSchema,
    ProductDetailSchema,
    ProductListItemSchema,
    ProductStockUpdateSchema,
    ProductSearchSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData


class ProductService:
    """商品服务类"""

    @staticmethod
    async def create_product(current_user: User, product_data: ProductCreateSchema) -> ApiResponse:
        """创建商品"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id, status=MerchantStatus.ACTIVE).first()
            if not merchant:
                return ResponseHelper.forbidden("只有审核通过的商家才能添加商品")

            # 创建商品
            product = await Product.create(
                merchant_id=merchant.id,
                name=product_data.name,
                category=product_data.category,
                description=product_data.description,
                price=product_data.price,
                stock=product_data.stock,
                unit=product_data.unit,
                images=product_data.images or []
            )

            product_response = ProductResponseSchema.from_orm(product)
            return ResponseHelper.created(product_response, "商品添加成功")

        except IntegrityError:
            return ResponseHelper.error("数据完整性错误", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"添加商品失败: {str(e)}")

    @staticmethod
    async def get_my_products(current_user: User, page: int = 1, page_size: int = 10, 
                             status: Optional[ProductStatus] = None,
                             category: Optional[ProductCategory] = None) -> ApiResponse:
        """获取我的商品列表"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 构建查询
            query = Product.filter(merchant_id=merchant.id)
            if status:
                query = query.filter(status=status)
            if category:
                query = query.filter(category=category)

            # 分页查询
            offset = (page - 1) * page_size
            products = await query.offset(offset).limit(page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            product_list = [ProductListItemSchema.from_orm(product) for product in products]
            
            total_pages = (total + page_size - 1) // page_size
            paginated_data = PaginatedData(
                items=product_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取商品列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取商品列表失败: {str(e)}")

    @staticmethod
    async def get_product_detail(current_user: User, product_id: int) -> ApiResponse:
        """获取商品详情"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取商品详情
            product = await Product.filter(id=product_id, merchant_id=merchant.id).select_related('merchant').first()
            if not product:
                return ResponseHelper.not_found("商品不存在")

            product_detail = ProductDetailSchema.from_orm(product)
            return ResponseHelper.success(product_detail, "获取商品详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取商品详情失败: {str(e)}")

    @staticmethod
    async def update_product(current_user: User, product_id: int, product_data: ProductUpdateSchema) -> ApiResponse:
        """更新商品信息"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取商品
            product = await Product.filter(id=product_id, merchant_id=merchant.id).first()
            if not product:
                return ResponseHelper.not_found("商品不存在")

            # 更新字段
            update_data = product_data.dict(exclude_unset=True)
            if update_data:
                await product.update_from_dict(update_data)
                await product.save()

            product_response = ProductResponseSchema.from_orm(product)
            return ResponseHelper.success(product_response, "商品信息更新成功")

        except IntegrityError:
            return ResponseHelper.error("数据完整性错误", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"更新商品信息失败: {str(e)}")

    @staticmethod
    async def delete_product(current_user: User, product_id: int) -> ApiResponse:
        """删除商品"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取商品
            product = await Product.filter(id=product_id, merchant_id=merchant.id).first()
            if not product:
                return ResponseHelper.not_found("商品不存在")

            # 软删除：将状态设置为inactive
            product.status = ProductStatus.INACTIVE
            await product.save()

            return ResponseHelper.success({"deleted": True}, "商品删除成功")

        except Exception as e:
            return ResponseHelper.server_error(f"删除商品失败: {str(e)}")

    @staticmethod
    async def update_product_stock(current_user: User, product_id: int, stock_data: ProductStockUpdateSchema) -> ApiResponse:
        """更新商品库存"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 获取商品
            product = await Product.filter(id=product_id, merchant_id=merchant.id).first()
            if not product:
                return ResponseHelper.not_found("商品不存在")

            # 更新库存
            product.stock = stock_data.stock
            if stock_data.status:
                product.status = stock_data.status
            elif stock_data.stock == 0:
                product.status = ProductStatus.SOLD_OUT
            elif product.status == ProductStatus.SOLD_OUT and stock_data.stock > 0:
                product.status = ProductStatus.AVAILABLE

            await product.save()

            product_response = ProductResponseSchema.from_orm(product)
            return ResponseHelper.success(product_response, "商品库存更新成功")

        except Exception as e:
            return ResponseHelper.server_error(f"更新商品库存失败: {str(e)}")

    @staticmethod
    async def search_products(search_data: ProductSearchSchema, page: int = 1, page_size: int = 10) -> ApiResponse:
        """搜索商品（用户端）"""
        try:
            # 构建查询条件
            query = Product.filter(
                status=ProductStatus.AVAILABLE,
                merchant__status=MerchantStatus.ACTIVE
            ).select_related('merchant')
            
            # 关键词搜索
            if search_data.keyword:
                query = query.filter(
                    Q(name__icontains=search_data.keyword) | 
                    Q(description__icontains=search_data.keyword)
                )
            
            # 分类筛选
            if search_data.category:
                query = query.filter(category=search_data.category)
            
            # 价格筛选
            if search_data.min_price:
                query = query.filter(price__gte=search_data.min_price)
            if search_data.max_price:
                query = query.filter(price__lte=search_data.max_price)
            
            # 商家筛选
            if search_data.merchant_id:
                query = query.filter(merchant_id=search_data.merchant_id)

            # 分页查询
            offset = (page - 1) * page_size
            products = await query.offset(offset).limit(page_size).order_by('-sales_count', '-created_at')
            total = await query.count()

            # 转换为响应数据
            product_list = []
            for product in products:
                product_dict = await product.to_dict()
                product_list.append(ProductListItemSchema(**product_dict))
            
            total_pages = (total + page_size - 1) // page_size
            paginated_data = PaginatedData(
                items=product_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "搜索商品成功")

        except Exception as e:
            return ResponseHelper.server_error(f"搜索商品失败: {str(e)}")

    @staticmethod
    async def get_public_product_detail(product_id: int) -> ApiResponse:
        """获取公开商品详情（用户端）"""
        try:
            product = await Product.filter(
                id=product_id, 
                status=ProductStatus.AVAILABLE,
                merchant__status=MerchantStatus.ACTIVE
            ).select_related('merchant').first()
            
            if not product:
                return ResponseHelper.not_found("商品不存在或不可用")

            product_dict = await product.to_dict()
            product_detail = ProductDetailSchema(**product_dict)
            return ResponseHelper.success(product_detail, "获取商品详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取商品详情失败: {str(e)}")

    @staticmethod
    async def get_products_by_category(category: ProductCategory, page: int = 1, page_size: int = 10) -> ApiResponse:
        """按分类获取商品列表"""
        try:
            # 构建查询条件
            query = Product.filter(
                category=category,
                status=ProductStatus.AVAILABLE,
                merchant__status=MerchantStatus.ACTIVE
            ).select_related('merchant')

            # 分页查询
            offset = (page - 1) * page_size
            products = await query.offset(offset).limit(page_size).order_by('-sales_count', '-created_at')
            total = await query.count()

            # 转换为响应数据
            product_list = []
            for product in products:
                product_dict = await product.to_dict()
                product_list.append(ProductListItemSchema(**product_dict))
            
            total_pages = (total + page_size - 1) // page_size
            paginated_data = PaginatedData(
                items=product_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取分类商品成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取分类商品失败: {str(e)}")

    @staticmethod
    async def get_popular_products(page: int = 1, page_size: int = 10) -> ApiResponse:
        """获取热门商品"""
        try:
            # 构建查询条件，按销量排序
            query = Product.filter(
                status=ProductStatus.AVAILABLE,
                merchant__status=MerchantStatus.ACTIVE
            ).select_related('merchant')

            # 分页查询
            offset = (page - 1) * page_size
            products = await query.offset(offset).limit(page_size).order_by('-sales_count', '-rating')
            total = await query.count()

            # 转换为响应数据
            product_list = []
            for product in products:
                product_dict = await product.to_dict()
                product_list.append(ProductListItemSchema(**product_dict))
            
            total_pages = (total + page_size - 1) // page_size
            paginated_data = PaginatedData(
                items=product_list,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取热门商品成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取热门商品失败: {str(e)}") 
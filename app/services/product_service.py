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
    ProductSearchSchema,
    AdminProductQuerySchema,
    AdminProductOperationSchema,
    AdminProductListItemSchema,
    AdminProductDetailSchema
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

            # 使用 to_dict 方法正确转换数据
            product_dict = await product.to_dict()
            product_detail = ProductDetailSchema(**product_dict)
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
        """获取热门商品（用户端）"""
        try:
            # 构建查询 - 按销量降序排列
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

    # =================== 管理员相关方法 ===================

    @staticmethod
    async def admin_get_all_products(current_user: User, query_params: AdminProductQuerySchema) -> ApiResponse:
        """管理员获取所有商品列表"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            # 构建查询
            query = Product.all().select_related('merchant')
            
            if query_params.merchant_id:
                query = query.filter(merchant_id=query_params.merchant_id)
            if query_params.category:
                query = query.filter(category=query_params.category)
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.name:
                query = query.filter(name__icontains=query_params.name)
            if query_params.min_price:
                query = query.filter(price__gte=query_params.min_price)
            if query_params.max_price:
                query = query.filter(price__lte=query_params.max_price)
            if query_params.low_stock:
                query = query.filter(stock__lt=10)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            products = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            product_list = []
            for product in products:
                # 获取商家名称
                merchant_name = product.merchant.merchant_name if product.merchant else "未知商家"
                
                # 统计订单数据
                from app.models.order import OrderItem
                order_items = await OrderItem.filter(product_id=product.id).select_related('order')
                order_count = len(set(item.order_id for item in order_items))
                total_sales = sum(float(item.total_price) for item in order_items if item.order.status in ['completed', 'delivered'])
                
                product_data = {
                    "id": product.id,
                    "merchant_id": product.merchant_id,
                    "name": product.name,
                    "category": product.category,
                    "price": float(product.price),
                    "stock": product.stock,
                    "unit": product.unit,
                    "images": product.images,
                    "rating": float(product.rating),
                    "sales_count": product.sales_count,
                    "status": product.status,
                    "created_at": product.created_at,
                    "merchant_name": merchant_name,
                    "order_count": order_count,
                    "total_sales": total_sales
                }
                
                product_list.append(product_data)
            
            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=product_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取商品列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取商品列表失败: {str(e)}")

    @staticmethod
    async def admin_get_product_detail(current_user: User, product_id: int) -> ApiResponse:
        """管理员获取商品详情"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            # 获取商品详情
            product = await Product.filter(id=product_id).select_related('merchant').first()
            if not product:
                return ResponseHelper.not_found("商品不存在")

            # 获取订单统计数据
            from app.models.order import OrderItem
            order_items = await OrderItem.filter(product_id=product.id).select_related('order')
            order_count = len(set(item.order_id for item in order_items))
            total_sales = sum(float(item.total_price) for item in order_items if item.order.status in ['completed', 'delivered'])
            
            # 获取最近的订单记录
            recent_order_items = await OrderItem.filter(
                product_id=product.id
            ).select_related('order', 'order__user').order_by('-created_at').limit(5)
            
            recent_order_data = []
            for item in recent_order_items:
                order_data = {
                    "order_id": item.order.id,
                    "order_number": item.order.order_number,
                    "user_name": item.order.user.nickname or item.order.user.username if item.order.user else "未知用户",
                    "quantity": item.quantity,
                    "total_price": float(item.total_price),
                    "order_status": item.order.status,
                    "created_at": item.created_at
                }
                recent_order_data.append(order_data)
            
            # 转换为详情数据
            product_dict = await product.to_dict()
            product_dict.update({
                "order_count": order_count,
                "total_sales": total_sales,
                "recent_orders": recent_order_data
            })
            
            product_detail = AdminProductDetailSchema(**product_dict)
            return ResponseHelper.success(product_detail, "获取商品详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取商品详情失败: {str(e)}")

    @staticmethod
    async def admin_operate_product(current_user: User, product_id: int, operation_data: AdminProductOperationSchema) -> ApiResponse:
        """管理员操作商品"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            product = await Product.get(id=product_id)
            
            if operation_data.operation == "deactivate":
                # 下架商品
                if product.status == ProductStatus.INACTIVE:
                    return ResponseHelper.error("商品已被下架", 400)
                
                product.status = ProductStatus.INACTIVE
                
            elif operation_data.operation == "activate":
                # 上架商品
                if product.status == ProductStatus.AVAILABLE:
                    return ResponseHelper.error("商品已是可售状态", 400)
                
                # 检查库存，如果为0则设为售罄
                if product.stock == 0:
                    product.status = ProductStatus.SOLD_OUT
                else:
                    product.status = ProductStatus.AVAILABLE
                
            elif operation_data.operation == "sold_out":
                # 设置售罄状态
                product.status = ProductStatus.SOLD_OUT
            
            # 记录操作日志（这里简化处理，实际应该有专门的日志表）
            # 可以在商品描述中添加管理员操作记录
            from datetime import datetime
            operation_log = f"\n[管理员操作 {datetime.now().strftime('%Y-%m-%d %H:%M')}] {operation_data.operation}: {operation_data.reason}"
            if operation_data.notes:
                operation_log += f" 备注：{operation_data.notes}"
            
            product.description = (product.description or "") + operation_log
            await product.save()
            
            product_response = ProductResponseSchema.from_orm(product)
            return ResponseHelper.success(product_response, f"商品操作成功")

        except DoesNotExist:
            return ResponseHelper.not_found("商品不存在")
        except Exception as e:
            return ResponseHelper.server_error(f"商品操作失败: {str(e)}")

    @staticmethod
    async def admin_get_product_statistics(current_user: User) -> ApiResponse:
        """管理员获取商品统计"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")

            # 获取所有商品
            all_products = await Product.all()
            
            stats = {
                "total_products": len(all_products),
                "available_products": 0,
                "sold_out_products": 0,
                "inactive_products": 0,
                "low_stock_products": 0,
                "total_orders": 0,
                "total_sales": 0.0,
                "top_categories": {}
            }
            
            # 统计各状态商品数量
            for product in all_products:
                if product.status == ProductStatus.AVAILABLE:
                    stats["available_products"] += 1
                elif product.status == ProductStatus.SOLD_OUT:
                    stats["sold_out_products"] += 1
                elif product.status == ProductStatus.INACTIVE:
                    stats["inactive_products"] += 1
                
                if product.stock < 10:
                    stats["low_stock_products"] += 1
                
                # 统计各分类商品数量
                category = product.category
                if category in stats["top_categories"]:
                    stats["top_categories"][category] += 1
                else:
                    stats["top_categories"][category] = 1
            
            # 统计订单和销售数据
            from app.models.order import OrderItem
            all_order_items = await OrderItem.all().select_related('order')
            completed_items = [item for item in all_order_items if item.order.status in ['completed', 'delivered']]
            
            stats["total_orders"] = len(set(item.order_id for item in all_order_items))
            stats["total_sales"] = sum(float(item.total_price) for item in completed_items)
            
            return ResponseHelper.success(stats, "获取商品统计成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取商品统计失败: {str(e)}") 
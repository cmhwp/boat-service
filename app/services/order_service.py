from typing import Optional, List, Dict, Any
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise import transactions
from datetime import datetime
from decimal import Decimal
import uuid
import random

from app.models.order import Order, OrderItem, Cart, PaymentRecord, OrderStatus, PaymentMethod
from app.models.product import Product, ProductStatus
from app.models.merchant import Merchant, MerchantStatus
from app.models.user import User
from app.schemas.order import (
    OrderCreateSchema,
    DirectOrderCreateSchema,
    PaymentCreateSchema,
    OrderStatusUpdateSchema,
    OrderQuerySchema,
    OrderResponseSchema,
    OrderDetailSchema,
    OrderListItemSchema,
    PaymentResponseSchema,
    OrderStatsSchema,
    AdminOrderQuerySchema,
    AdminOrderListItemSchema,
    AdminOrderDetailSchema
)
from app.schemas.response import ResponseHelper, ApiResponse, PaginatedData
from app.models.user import UserRole


class OrderService:
    """订单服务类"""

    @staticmethod
    def _generate_order_number() -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"OD{timestamp}{random_suffix}"

    @staticmethod
    def _generate_payment_number() -> str:
        """生成支付单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"PAY{timestamp}{random_suffix}"

    @staticmethod
    async def create_order_from_cart(current_user: User, order_data: OrderCreateSchema) -> ApiResponse:
        """从购物车创建订单"""
        try:
            async with transactions.in_transaction():
                # 1. 获取购物车商品
                cart_items = await Cart.filter(
                    id__in=order_data.cart_item_ids,
                    user=current_user
                ).select_related('product', 'product__merchant')
                
                if not cart_items:
                    return ResponseHelper.error("购物车商品不存在", 400)
                
                if len(cart_items) != len(order_data.cart_item_ids):
                    return ResponseHelper.error("部分商品不存在", 400)
                
                # 2. 按商家分组（一个订单只能包含同一商家的商品）
                merchant_groups = {}
                for item in cart_items:
                    merchant_id = item.product.merchant_id
                    if merchant_id not in merchant_groups:
                        merchant_groups[merchant_id] = []
                    merchant_groups[merchant_id].append(item)
                
                if len(merchant_groups) > 1:
                    return ResponseHelper.error("一个订单只能包含同一商家的商品，请分别下单", 400)
                
                merchant_id = list(merchant_groups.keys())[0]
                merchant = await Merchant.get(id=merchant_id)
                
                if merchant.status != MerchantStatus.ACTIVE:
                    return ResponseHelper.error("该商家未通过审核", 400)
                
                # 3. 验证商品库存和状态
                total_amount = Decimal('0')
                order_items_data = []
                
                for cart_item in cart_items:
                    product = cart_item.product
                    
                    # 检查商品状态
                    if product.status != ProductStatus.AVAILABLE:
                        return ResponseHelper.error(f"商品「{product.name}」已下架", 400)
                    
                    # 检查库存
                    if product.stock < cart_item.quantity:
                        return ResponseHelper.error(
                            f"商品「{product.name}」库存不足，当前库存：{product.stock}{product.unit}", 400)
                    
                    # 计算金额
                    item_total = product.price * cart_item.quantity
                    total_amount += item_total
                    
                    # 准备订单项数据
                    order_items_data.append({
                        'product': product,
                        'quantity': cart_item.quantity,
                        'unit_price': product.price,
                        'total_price': item_total,
                        'product_name': product.name,
                        'product_unit': product.unit,
                        'product_image': product.images[0] if product.images else None
                    })
                
                # 4. 计算运费（简单模拟：满100免运费）
                shipping_fee = Decimal('10') if total_amount < Decimal('100') else Decimal('0')
                final_amount = total_amount + shipping_fee
                
                # 5. 创建订单
                order = await Order.create(
                    order_number=OrderService._generate_order_number(),
                    user=current_user,
                    merchant=merchant,
                    total_amount=total_amount,
                    shipping_fee=shipping_fee,
                    final_amount=final_amount,
                    receiver_name=order_data.receiver_name,
                    receiver_phone=order_data.receiver_phone,
                    receiver_address=order_data.receiver_address,
                    user_notes=order_data.user_notes,
                    status=OrderStatus.PENDING
                )
                
                # 6. 创建订单项
                for item_data in order_items_data:
                    await OrderItem.create(
                        order=order,
                        product=item_data['product'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=item_data['total_price'],
                        product_name=item_data['product_name'],
                        product_unit=item_data['product_unit'],
                        product_image=item_data['product_image']
                    )
                
                # 7. 删除购物车商品
                await Cart.filter(id__in=order_data.cart_item_ids).delete()
                
                order_dict = await order.to_dict()
                order_response = OrderResponseSchema(**order_dict)
                return ResponseHelper.created(order_response, "订单创建成功")

        except IntegrityError:
            return ResponseHelper.error("订单创建失败，请稍后重试", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"创建订单失败: {str(e)}")

    @staticmethod
    async def create_direct_order(current_user: User, order_data: DirectOrderCreateSchema) -> ApiResponse:
        """立即购买创建订单"""
        try:
            async with transactions.in_transaction():
                # 1. 检查商品
                product = await Product.filter(
                    id=order_data.product_id,
                    status=ProductStatus.AVAILABLE
                ).select_related('merchant').first()
                
                if not product:
                    return ResponseHelper.not_found("商品不存在或已下架")
                
                if product.merchant.status != MerchantStatus.ACTIVE:
                    return ResponseHelper.error("该商家未通过审核", 400)
                
                # 2. 检查库存
                if product.stock < order_data.quantity:
                    return ResponseHelper.error(f"库存不足，当前库存：{product.stock}{product.unit}", 400)
                
                # 3. 计算金额
                total_amount = product.price * order_data.quantity
                shipping_fee = Decimal('10') if total_amount < Decimal('100') else Decimal('0')
                final_amount = total_amount + shipping_fee
                
                # 4. 创建订单
                order = await Order.create(
                    order_number=OrderService._generate_order_number(),
                    user=current_user,
                    merchant=product.merchant,
                    total_amount=total_amount,
                    shipping_fee=shipping_fee,
                    final_amount=final_amount,
                    receiver_name=order_data.receiver_name,
                    receiver_phone=order_data.receiver_phone,
                    receiver_address=order_data.receiver_address,
                    user_notes=order_data.user_notes,
                    status=OrderStatus.PENDING
                )
                
                # 5. 创建订单项
                await OrderItem.create(
                    order=order,
                    product=product,
                    quantity=order_data.quantity,
                    unit_price=product.price,
                    total_price=total_amount,
                    product_name=product.name,
                    product_unit=product.unit,
                    product_image=product.images[0] if product.images else None
                )
                
                order_dict = await order.to_dict()
                order_response = OrderResponseSchema(**order_dict)
                return ResponseHelper.created(order_response, "订单创建成功")

        except Exception as e:
            return ResponseHelper.server_error(f"创建订单失败: {str(e)}")

    @staticmethod
    async def create_payment(current_user: User, payment_data: PaymentCreateSchema) -> ApiResponse:
        """创建支付（模拟支付）"""
        try:
            async with transactions.in_transaction():
                # 1. 获取订单
                order = await Order.filter(
                    id=payment_data.order_id,
                    user=current_user,
                    status=OrderStatus.PENDING
                ).first()
                
                if not order:
                    return ResponseHelper.not_found("订单不存在或无法支付")
                
                # 2. 创建支付记录
                payment = await PaymentRecord.create(
                    payment_number=OrderService._generate_payment_number(),
                    order=order,
                    user=current_user,
                    amount=order.final_amount,
                    payment_method=payment_data.payment_method,
                    third_party_number=f"MOCK_{random.randint(100000, 999999)}"  # 模拟第三方支付单号
                )
                
                # 3. 模拟支付处理（90%成功率）
                is_success = random.random() > 0.1  # 90%成功率
                
                if is_success:
                    # 支付成功
                    payment.is_success = True
                    payment.paid_at = datetime.now()
                    await payment.save()
                    
                    # 更新订单状态
                    order.status = OrderStatus.PAID
                    order.payment_method = payment_data.payment_method
                    order.paid_at = datetime.now()
                    await order.save()
                    
                    # 扣减库存
                    await OrderService._reduce_product_stock(order.id)
                    
                    payment_dict = await payment.to_dict()
                    payment_response = PaymentResponseSchema(**payment_dict)
                    return ResponseHelper.success(payment_response, "支付成功")
                else:
                    # 支付失败
                    payment.is_success = False
                    await payment.save()
                    
                    payment_dict = await payment.to_dict()
                    payment_response = PaymentResponseSchema(**payment_dict)
                    return ResponseHelper.error("支付失败，请重试", 400, payment_response)

        except Exception as e:
            return ResponseHelper.server_error(f"支付失败: {str(e)}")

    @staticmethod
    async def _reduce_product_stock(order_id: int) -> None:
        """扣减商品库存"""
        try:
            order_items = await OrderItem.filter(order_id=order_id).select_related('product')
            
            for item in order_items:
                product = item.product
                # 扣减库存
                product.stock -= item.quantity
                # 增加销量
                product.sales_count += item.quantity
                # 如果库存为0，设置为售罄状态
                if product.stock <= 0:
                    product.status = ProductStatus.SOLD_OUT
                await product.save()
                
        except Exception as e:
            # 记录错误但不影响支付流程
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"扣减库存失败: {str(e)}")

    @staticmethod
    async def get_user_orders(current_user: User, query_params: OrderQuerySchema) -> ApiResponse:
        """获取用户订单列表"""
        try:
            # 构建查询
            query = Order.filter(user=current_user).select_related('merchant')
            
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.start_date:
                query = query.filter(created_at__gte=query_params.start_date)
            if query_params.end_date:
                query = query.filter(created_at__lte=query_params.end_date)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            orders = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            order_list = []
            for order in orders:
                # 统计订单项信息
                order_items = await OrderItem.filter(order_id=order.id)
                item_count = len(order_items)
                total_quantity = sum(item.quantity for item in order_items)
                
                order_item = OrderListItemSchema(
                    id=order.id,
                    order_number=order.order_number,
                    merchant_id=order.merchant_id,
                    merchant_name=order.merchant.merchant_name,
                    total_amount=float(order.total_amount),
                    final_amount=float(order.final_amount),
                    status=order.status,
                    item_count=item_count,
                    total_quantity=total_quantity,
                    created_at=order.created_at
                )
                order_list.append(order_item)
            
            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=order_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取订单列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取订单列表失败: {str(e)}")

    @staticmethod
    async def get_order_detail(current_user: User, order_id: int) -> ApiResponse:
        """获取订单详情"""
        try:
            order = await Order.filter(
                id=order_id,
                user=current_user
            ).select_related('merchant', 'user').first()
            
            if not order:
                return ResponseHelper.not_found("订单不存在")

            order_dict = await order.to_dict()
            order_detail = OrderDetailSchema(**order_dict)
            return ResponseHelper.success(order_detail, "获取订单详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取订单详情失败: {str(e)}")

    @staticmethod
    async def cancel_order(current_user: User, order_id: int, cancel_reason: str) -> ApiResponse:
        """取消订单"""
        try:
            async with transactions.in_transaction():
                order = await Order.filter(
                    id=order_id,
                    user=current_user
                ).first()
                
                if not order:
                    return ResponseHelper.not_found("订单不存在")
                
                # 只有待支付状态的订单可以取消
                if order.status != OrderStatus.PENDING:
                    return ResponseHelper.error("当前状态的订单无法取消", 400)
                
                # 更新订单状态
                order.status = OrderStatus.CANCELLED
                order.cancelled_at = datetime.now()
                order.cancel_reason = cancel_reason
                await order.save()
                
                order_dict = await order.to_dict()
                order_response = OrderResponseSchema(**order_dict)
                return ResponseHelper.success(order_response, "订单已取消")

        except Exception as e:
            return ResponseHelper.server_error(f"取消订单失败: {str(e)}")

    @staticmethod
    async def get_merchant_orders(current_user: User, query_params: OrderQuerySchema) -> ApiResponse:
        """获取商家订单列表"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 构建查询
            query = Order.filter(merchant=merchant).select_related('user')
            
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.start_date:
                query = query.filter(created_at__gte=query_params.start_date)
            if query_params.end_date:
                query = query.filter(created_at__lte=query_params.end_date)
            if query_params.user_id:
                query = query.filter(user_id=query_params.user_id)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            orders = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            order_list = []
            for order in orders:
                order_dict = await order.to_dict()
                order_detail = OrderDetailSchema(**order_dict)
                order_list.append(order_detail)
            
            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=order_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取订单列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取订单列表失败: {str(e)}")

    @staticmethod
    async def update_order_status(current_user: User, order_id: int, status_data: OrderStatusUpdateSchema) -> ApiResponse:
        """更新订单状态（商家操作）"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            async with transactions.in_transaction():
                order = await Order.filter(
                    id=order_id,
                    merchant=merchant
                ).first()
                
                if not order:
                    return ResponseHelper.not_found("订单不存在")
                
                # 验证状态转换的合法性
                valid_transitions = {
                    OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
                    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
                    OrderStatus.DELIVERED: [OrderStatus.COMPLETED]
                }
                
                current_status = order.status
                target_status = status_data.status
                
                if current_status not in valid_transitions:
                    return ResponseHelper.error(f"当前状态「{current_status}」无法修改", 400)
                
                if target_status not in valid_transitions[current_status]:
                    return ResponseHelper.error(f"无法从「{current_status}」变更为「{target_status}」", 400)
                
                # 更新订单状态
                order.status = target_status
                if status_data.merchant_notes:
                    order.merchant_notes = status_data.merchant_notes
                if status_data.cancel_reason:
                    order.cancel_reason = status_data.cancel_reason
                
                # 设置对应的时间戳
                current_time = datetime.now()
                if target_status == OrderStatus.SHIPPED:
                    order.shipped_at = current_time
                elif target_status == OrderStatus.DELIVERED:
                    order.delivered_at = current_time
                elif target_status == OrderStatus.COMPLETED:
                    order.completed_at = current_time
                elif target_status == OrderStatus.CANCELLED:
                    order.cancelled_at = current_time
                    # 如果是已支付订单被取消，需要恢复库存
                    if current_status == OrderStatus.PAID:
                        await OrderService._restore_product_stock(order_id)
                
                await order.save()
                
                order_dict = await order.to_dict()
                order_response = OrderResponseSchema(**order_dict)
                return ResponseHelper.success(order_response, f"订单状态已更新为「{target_status}」")

        except Exception as e:
            return ResponseHelper.server_error(f"更新订单状态失败: {str(e)}")

    @staticmethod
    async def _restore_product_stock(order_id: int) -> None:
        """恢复商品库存"""
        try:
            order_items = await OrderItem.filter(order_id=order_id).select_related('product')
            
            for item in order_items:
                product = item.product
                # 恢复库存
                product.stock += item.quantity
                # 减少销量
                product.sales_count -= item.quantity
                # 如果之前是售罄状态，恢复为可售状态
                if product.status == ProductStatus.SOLD_OUT and product.stock > 0:
                    product.status = ProductStatus.AVAILABLE
                await product.save()
                
        except Exception as e:
            # 记录错误但不影响订单状态更新
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"恢复库存失败: {str(e)}")

    @staticmethod
    async def get_order_stats(current_user: User) -> ApiResponse:
        """获取订单统计（商家）"""
        try:
            # 检查用户是否是商家
            merchant = await Merchant.filter(user_id=current_user.id).first()
            if not merchant:
                return ResponseHelper.forbidden("用户不是商家")

            # 统计各状态订单数量
            all_orders = await Order.filter(merchant=merchant)
            
            stats = {
                "total_orders": len(all_orders),
                "pending_orders": 0,
                "paid_orders": 0,
                "shipped_orders": 0,
                "completed_orders": 0,
                "cancelled_orders": 0,
                "total_amount": 0.0,
                "paid_amount": 0.0
            }
            
            for order in all_orders:
                stats["total_amount"] += float(order.final_amount)
                
                if order.status == OrderStatus.PENDING:
                    stats["pending_orders"] += 1
                elif order.status == OrderStatus.PAID:
                    stats["paid_orders"] += 1
                    stats["paid_amount"] += float(order.final_amount)
                elif order.status == OrderStatus.SHIPPED:
                    stats["shipped_orders"] += 1
                    stats["paid_amount"] += float(order.final_amount)
                elif order.status == OrderStatus.COMPLETED:
                    stats["completed_orders"] += 1
                    stats["paid_amount"] += float(order.final_amount)
                elif order.status == OrderStatus.CANCELLED:
                    stats["cancelled_orders"] += 1
            
            order_stats = OrderStatsSchema(**stats)
            return ResponseHelper.success(order_stats, "获取订单统计成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取订单统计失败: {str(e)}")

    # =================== 管理员相关方法 ===================

    @staticmethod
    async def admin_get_all_orders(current_user: User, query_params) -> ApiResponse:
        """管理员获取所有订单列表"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            # 构建查询
            query = Order.all().select_related('user', 'merchant')
            
            if query_params.status:
                query = query.filter(status=query_params.status)
            if query_params.start_date:
                query = query.filter(created_at__gte=query_params.start_date)
            if query_params.end_date:
                query = query.filter(created_at__lte=query_params.end_date)
            if query_params.merchant_id:
                query = query.filter(merchant_id=query_params.merchant_id)
            if query_params.user_id:
                query = query.filter(user_id=query_params.user_id)
            if query_params.order_number:
                query = query.filter(order_number__icontains=query_params.order_number)

            # 分页查询
            offset = (query_params.page - 1) * query_params.page_size
            orders = await query.offset(offset).limit(query_params.page_size).order_by('-created_at')
            total = await query.count()

            # 转换为响应数据
            order_list = []
            for order in orders:
                # 获取商家名称
                merchant_name = order.merchant.merchant_name if order.merchant else "未知商家"
                
                # 获取用户信息
                user_name = order.user.username if order.user else "未知用户"
                user_phone = order.user.phone if order.user else None
                
                # 获取支付信息
                payment_method = None
                paid_at = None
                # 单独查询支付记录
                payment_records = await PaymentRecord.filter(order_id=order.id)
                if payment_records:
                    successful_payment = next((p for p in payment_records if p.is_success), None)
                    if successful_payment:
                        payment_method = successful_payment.payment_method
                        paid_at = successful_payment.paid_at
                
                # 计算订单项统计
                order_items_count = await OrderItem.filter(order_id=order.id).count()
                total_quantity = await OrderItem.filter(order_id=order.id).values('quantity')
                total_quantity = sum(item['quantity'] for item in total_quantity)
                
                order_data = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "merchant_id": order.merchant_id,
                    "merchant_name": merchant_name,
                    "total_amount": float(order.total_amount),
                    "final_amount": float(order.final_amount),
                    "status": order.status,
                    "item_count": order_items_count,
                    "total_quantity": total_quantity,
                    "created_at": order.created_at,
                    "user_name": user_name,
                    "user_phone": user_phone,
                    "payment_method": payment_method,
                    "paid_at": paid_at
                }
                
                order_list.append(order_data)
            
            total_pages = (total + query_params.page_size - 1) // query_params.page_size
            paginated_data = PaginatedData(
                items=order_list,
                total=total,
                page=query_params.page,
                page_size=query_params.page_size,
                total_pages=total_pages
            )

            return ResponseHelper.success(paginated_data, "获取订单列表成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取订单列表失败: {str(e)}")

    @staticmethod
    async def admin_get_order_detail(current_user: User, order_id: int) -> ApiResponse:
        """管理员获取订单详情"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            # 获取订单详情
            order = await Order.filter(id=order_id).select_related('user', 'merchant').first()
            if not order:
                return ResponseHelper.not_found("订单不存在")

            # 获取支付记录
            payment_records = await PaymentRecord.filter(order_id=order_id)
            
            # 转换为详情数据
            order_dict = await order.to_dict()
            
            # 添加支付记录
            payment_data = []
            for payment in payment_records:
                payment_dict = await payment.to_dict()
                payment_data.append(payment_dict)
            
            order_dict['payment_records'] = payment_data
            
            order_detail = AdminOrderDetailSchema(**order_dict)
            return ResponseHelper.success(order_detail, "获取订单详情成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取订单详情失败: {str(e)}")

    @staticmethod
    async def admin_operate_order(current_user: User, order_id: int, operation_data) -> ApiResponse:
        """管理员操作订单"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")
            
            async with transactions.in_transaction():
                order = await Order.get(id=order_id)
                
                if operation_data.operation == "force_cancel":
                    # 强制取消订单
                    if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                        return ResponseHelper.error("订单已完成或已取消，无法操作", 400)
                    
                    # 如果是已支付订单，需要恢复库存
                    if order.status in [OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                        await OrderService._restore_product_stock(order_id)
                    
                    order.status = OrderStatus.CANCELLED
                    order.cancelled_at = datetime.now()
                    order.cancel_reason = f"管理员强制取消：{operation_data.reason}"
                    if operation_data.notes:
                        order.merchant_notes = f"管理员备注：{operation_data.notes}"
                    
                elif operation_data.operation == "refund":
                    # 处理退款
                    if order.status != OrderStatus.PAID:
                        return ResponseHelper.error("只有已支付的订单才能退款", 400)
                    
                    # 恢复库存
                    await OrderService._restore_product_stock(order_id)
                    
                    order.status = OrderStatus.REFUNDED
                    order.cancel_reason = f"管理员退款：{operation_data.reason}"
                    if operation_data.notes:
                        order.merchant_notes = f"管理员备注：{operation_data.notes}"
                
                await order.save()
                
                order_dict = await order.to_dict()
                from app.schemas.order import OrderResponseSchema
                order_response = OrderResponseSchema(**order_dict)
                return ResponseHelper.success(order_response, f"订单操作成功")

        except DoesNotExist:
            return ResponseHelper.not_found("订单不存在")
        except Exception as e:
            return ResponseHelper.server_error(f"订单操作失败: {str(e)}")

    @staticmethod
    async def admin_get_order_statistics(current_user: User) -> ApiResponse:
        """管理员获取全平台订单统计"""
        try:
            # 检查用户是否是管理员
            if current_user.role != UserRole.ADMIN:
                return ResponseHelper.forbidden("只有管理员才能访问此功能")

            # 获取所有订单
            all_orders = await Order.all()
            
            stats = {
                "total_orders": len(all_orders),
                "pending_orders": 0,
                "paid_orders": 0,
                "shipped_orders": 0,
                "completed_orders": 0,
                "cancelled_orders": 0,
                "refunded_orders": 0,
                "total_amount": 0.0,
                "paid_amount": 0.0
            }
            
            for order in all_orders:
                stats["total_amount"] += float(order.final_amount)
                
                if order.status == OrderStatus.PENDING:
                    stats["pending_orders"] += 1
                elif order.status == OrderStatus.PAID:
                    stats["paid_orders"] += 1
                    stats["paid_amount"] += float(order.final_amount)
                elif order.status == OrderStatus.SHIPPED:
                    stats["shipped_orders"] += 1
                    stats["paid_amount"] += float(order.final_amount)
                elif order.status == OrderStatus.COMPLETED:
                    stats["completed_orders"] += 1
                    stats["paid_amount"] += float(order.final_amount)
                elif order.status == OrderStatus.CANCELLED:
                    stats["cancelled_orders"] += 1
                elif order.status == OrderStatus.REFUNDED:
                    stats["refunded_orders"] += 1
            
            # 添加管理员特有的统计信息
            stats["platform_commission"] = stats["paid_amount"] * 0.05  # 假设平台抽成5%
            stats["merchant_revenue"] = stats["paid_amount"] * 0.95
            
            return ResponseHelper.success(stats, "获取平台订单统计成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取订单统计失败: {str(e)}") 
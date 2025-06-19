from typing import Optional, List
from tortoise.exceptions import IntegrityError, DoesNotExist
from decimal import Decimal

from app.models.order import Cart
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.order import CartAddSchema, CartUpdateSchema, CartItemResponseSchema
from app.schemas.response import ResponseHelper, ApiResponse


class CartService:
    """购物车服务类"""

    @staticmethod
    async def add_to_cart(current_user: User, cart_data: CartAddSchema) -> ApiResponse:
        """添加商品到购物车"""
        try:
            # 检查商品是否存在且可购买
            product = await Product.filter(
                id=cart_data.product_id,
                status=ProductStatus.AVAILABLE
            ).first()
            
            if not product:
                return ResponseHelper.not_found("商品不存在或已下架")
            
            # 检查库存
            if product.stock < cart_data.quantity:
                return ResponseHelper.error(f"库存不足，当前库存：{product.stock}{product.unit}", 400)
            
            # 检查是否已存在相同商品，存在则更新数量
            existing_cart_item = await Cart.filter(
                user=current_user,
                product_id=cart_data.product_id
            ).first()
            
            if existing_cart_item:
                # 更新数量
                new_quantity = existing_cart_item.quantity + cart_data.quantity
                if new_quantity > product.stock:
                    return ResponseHelper.error(f"添加失败，总数量超过库存限制（{product.stock}{product.unit}）", 400)
                
                existing_cart_item.quantity = new_quantity
                await existing_cart_item.save()
                
                cart_dict = await existing_cart_item.to_dict()
                cart_item = CartItemResponseSchema(
                    **cart_dict,
                    subtotal=float(product.price) * new_quantity
                )
                return ResponseHelper.success(cart_item, "商品数量已更新")
            else:
                # 创建新的购物车项
                cart_item = await Cart.create(
                    user=current_user,
                    product_id=cart_data.product_id,
                    quantity=cart_data.quantity
                )
                
                cart_dict = await cart_item.to_dict()
                cart_response = CartItemResponseSchema(
                    **cart_dict,
                    subtotal=float(product.price) * cart_data.quantity
                )
                return ResponseHelper.success(cart_response, "商品已添加到购物车")

        except IntegrityError:
            return ResponseHelper.error("添加购物车失败", 400)
        except Exception as e:
            return ResponseHelper.server_error(f"添加购物车失败: {str(e)}")

    @staticmethod
    async def get_cart_items(current_user: User) -> ApiResponse:
        """获取购物车商品列表"""
        try:
            cart_items = await Cart.filter(user=current_user).select_related('product').order_by('-created_at')
            
            cart_list = []
            total_amount = Decimal('0')
            total_items = 0
            
            for item in cart_items:
                # 检查商品状态和库存
                product = item.product
                if product.status != ProductStatus.AVAILABLE:
                    # 商品已下架，标记但不计入总价
                    cart_dict = await item.to_dict()
                    cart_response = CartItemResponseSchema(
                        **cart_dict,
                        subtotal=0.0
                    )
                    cart_response.product['is_available'] = False
                    cart_response.product['unavailable_reason'] = '商品已下架'
                    cart_list.append(cart_response)
                    continue
                
                if product.stock < item.quantity:
                    # 库存不足，调整数量
                    if product.stock == 0:
                        cart_dict = await item.to_dict()
                        cart_response = CartItemResponseSchema(
                            **cart_dict,
                            subtotal=0.0
                        )
                        cart_response.product['is_available'] = False
                        cart_response.product['unavailable_reason'] = '商品缺货'
                        cart_list.append(cart_response)
                        continue
                    else:
                        # 自动调整为可用库存数量
                        item.quantity = product.stock
                        await item.save()
                
                # 计算小计
                subtotal = product.price * item.quantity
                total_amount += subtotal
                total_items += item.quantity
                
                cart_dict = await item.to_dict()
                cart_response = CartItemResponseSchema(
                    **cart_dict,
                    subtotal=float(subtotal)
                )
                cart_response.product['is_available'] = True
                cart_list.append(cart_response)
            
            result = {
                "items": cart_list,
                "total_amount": float(total_amount),
                "total_items": total_items,
                "item_count": len(cart_list)
            }
            
            return ResponseHelper.success(result, "获取购物车成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取购物车失败: {str(e)}")

    @staticmethod
    async def update_cart_item(current_user: User, cart_item_id: int, update_data: CartUpdateSchema) -> ApiResponse:
        """更新购物车商品数量"""
        try:
            # 获取购物车项
            cart_item = await Cart.filter(
                id=cart_item_id,
                user=current_user
            ).select_related('product').first()
            
            if not cart_item:
                return ResponseHelper.not_found("购物车商品不存在")
            
            # 检查商品状态
            product = cart_item.product
            if product.status != ProductStatus.AVAILABLE:
                return ResponseHelper.error("商品已下架", 400)
            
            # 检查库存
            if product.stock < update_data.quantity:
                return ResponseHelper.error(f"库存不足，当前库存：{product.stock}{product.unit}", 400)
            
            # 更新数量
            cart_item.quantity = update_data.quantity
            await cart_item.save()
            
            cart_dict = await cart_item.to_dict()
            cart_response = CartItemResponseSchema(
                **cart_dict,
                subtotal=float(product.price) * update_data.quantity
            )
            
            return ResponseHelper.success(cart_response, "购物车已更新")

        except Exception as e:
            return ResponseHelper.server_error(f"更新购物车失败: {str(e)}")

    @staticmethod
    async def remove_cart_item(current_user: User, cart_item_id: int) -> ApiResponse:
        """删除购物车商品"""
        try:
            cart_item = await Cart.filter(
                id=cart_item_id,
                user=current_user
            ).first()
            
            if not cart_item:
                return ResponseHelper.not_found("购物车商品不存在")
            
            await cart_item.delete()
            return ResponseHelper.success({"deleted": True}, "商品已从购物车移除")

        except Exception as e:
            return ResponseHelper.server_error(f"删除购物车商品失败: {str(e)}")

    @staticmethod
    async def clear_cart(current_user: User) -> ApiResponse:
        """清空购物车"""
        try:
            deleted_count = await Cart.filter(user=current_user).delete()
            
            result = {
                "cleared": True,
                "deleted_count": deleted_count
            }
            
            return ResponseHelper.success(result, f"购物车已清空，共移除{deleted_count}件商品")

        except Exception as e:
            return ResponseHelper.server_error(f"清空购物车失败: {str(e)}")

    @staticmethod
    async def get_cart_stats(current_user: User) -> ApiResponse:
        """获取购物车统计信息"""
        try:
            # 统计购物车商品数量
            total_items = await Cart.filter(user=current_user).count()
            
            # 计算可购买商品的总金额
            cart_items = await Cart.filter(user=current_user).select_related('product')
            
            total_amount = Decimal('0')
            available_items = 0
            
            for item in cart_items:
                product = item.product
                if product.status == ProductStatus.AVAILABLE and product.stock >= item.quantity:
                    total_amount += product.price * item.quantity
                    available_items += item.quantity
            
            result = {
                "total_items": total_items,
                "available_items": available_items,
                "total_amount": float(total_amount),
                "has_unavailable_items": total_items > available_items
            }
            
            return ResponseHelper.success(result, "获取购物车统计成功")

        except Exception as e:
            return ResponseHelper.server_error(f"获取购物车统计失败: {str(e)}")

    @staticmethod
    async def batch_remove_cart_items(current_user: User, cart_item_ids: List[int]) -> ApiResponse:
        """批量删除购物车商品"""
        try:
            if not cart_item_ids:
                return ResponseHelper.error("请选择要删除的商品", 400)
            
            # 验证所有商品都属于当前用户
            valid_items = await Cart.filter(
                id__in=cart_item_ids,
                user=current_user
            ).all()
            
            if len(valid_items) != len(cart_item_ids):
                return ResponseHelper.error("部分商品不存在或无权限删除", 400)
            
            # 批量删除
            deleted_count = await Cart.filter(
                id__in=cart_item_ids,
                user=current_user
            ).delete()
            
            result = {
                "deleted": True,
                "deleted_count": deleted_count
            }
            
            return ResponseHelper.success(result, f"成功删除{deleted_count}件商品")

        except Exception as e:
            return ResponseHelper.server_error(f"批量删除失败: {str(e)}") 
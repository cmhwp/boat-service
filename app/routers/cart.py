from fastapi import APIRouter, Depends, Query, Path, Body
from typing import Optional, List

from app.models.user import User
from app.schemas.order import CartAddSchema, CartUpdateSchema, CartItemResponseSchema
from app.schemas.response import ApiResponse
from app.services.cart_service import CartService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/", response_model=ApiResponse[CartItemResponseSchema], summary="添加商品到购物车")
async def add_to_cart(
    cart_data: CartAddSchema,
    current_user: User = Depends(get_current_user)
):
    """
    添加商品到购物车
    
    - **product_id**: 商品ID（必填）
    - **quantity**: 数量（必填，1-999）
    
    系统会自动验证：
    - 商品是否存在且可购买
    - 库存是否充足
    - 如果购物车中已有相同商品，则累加数量
    """
    return await CartService.add_to_cart(current_user, cart_data)


@router.get("/", response_model=ApiResponse, summary="获取购物车商品列表")
async def get_cart_items(
    current_user: User = Depends(get_current_user)
):
    """
    获取用户购物车商品列表
    
    返回信息包括：
    - 购物车商品列表
    - 总金额（仅计算可购买商品）
    - 商品总数量
    - 自动处理缺货和下架商品
    """
    return await CartService.get_cart_items(current_user)


@router.put("/{cart_item_id}", response_model=ApiResponse[CartItemResponseSchema], summary="更新购物车商品数量")
async def update_cart_item(
    cart_item_id: int = Path(..., description="购物车项ID"),
    update_data: CartUpdateSchema = ...,
    current_user: User = Depends(get_current_user)
):
    """
    更新购物车中指定商品的数量
    
    - **quantity**: 新的数量（必填，1-999）
    
    限制条件：
    - 只能修改当前用户的购物车商品
    - 数量不能超过库存
    - 商品必须是可购买状态
    """
    return await CartService.update_cart_item(current_user, cart_item_id, update_data)


@router.delete("/{cart_item_id}", response_model=ApiResponse, summary="删除购物车商品")
async def remove_cart_item(
    cart_item_id: int = Path(..., description="购物车项ID"),
    current_user: User = Depends(get_current_user)
):
    """
    从购物车中删除指定商品
    
    只能删除当前用户的购物车商品
    """
    return await CartService.remove_cart_item(current_user, cart_item_id)


@router.delete("/", response_model=ApiResponse, summary="清空购物车")
async def clear_cart(
    current_user: User = Depends(get_current_user)
):
    """
    清空用户购物车中的所有商品
    
    返回删除的商品数量
    """
    return await CartService.clear_cart(current_user)


@router.get("/stats", response_model=ApiResponse, summary="获取购物车统计")
async def get_cart_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取购物车统计信息
    
    返回信息包括：
    - 购物车商品总数
    - 可购买商品数量
    - 可购买商品总金额
    - 是否有不可购买商品
    """
    return await CartService.get_cart_stats(current_user)


@router.delete("/batch", response_model=ApiResponse, summary="批量删除购物车商品")
async def batch_remove_cart_items(
    cart_item_ids: List[int] = Body(..., description="购物车项ID列表"),
    current_user: User = Depends(get_current_user)
):
    """
    批量删除购物车中的多个商品
    
    - **cart_item_ids**: 购物车项ID列表（必填）
    
    只能删除当前用户的购物车商品
    """
    return await CartService.batch_remove_cart_items(current_user, cart_item_ids) 
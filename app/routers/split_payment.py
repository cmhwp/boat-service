from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.split_payment_service import SplitPaymentService
from app.schemas.split_payment import (
    SplitRuleCreateSchema,
    SplitPaymentQuerySchema
)
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/split-payments", tags=["分账管理"])


@router.post("/rules", response_model=ApiResponse, summary="创建分账规则（管理员）")
async def create_split_rule(
    rule_data: SplitRuleCreateSchema,
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """创建分账规则"""
    return await SplitPaymentService.create_split_rule(rule_data)


@router.get("/", response_model=ApiResponse, summary="获取分账记录列表")
async def get_split_payments(
    query: SplitPaymentQuerySchema = Depends(),
    current_user: User = Depends(get_current_user)
):
    """获取分账记录列表（商家查看自己的，船员查看自己的，管理员查看全部）"""
    # 根据用户角色过滤数据
    if current_user.role == UserRole.MERCHANT:
        from app.models.merchant import Merchant
        merchant = await Merchant.filter(user=current_user).first()
        if merchant:
            query.merchant_id = merchant.id
    elif current_user.role == UserRole.CREW:
        from app.models.crew import Crew
        crew = await Crew.filter(user=current_user).first()
        if crew:
            query.crew_id = crew.id
    # 管理员不需要过滤，可以查看全部
    
    return await SplitPaymentService.get_split_payments(query)


@router.get("/stats", response_model=ApiResponse, summary="获取分账统计")
async def get_split_stats(
    current_user: User = Depends(get_current_user)
):
    """获取分账统计（商家查看自己的，船员查看自己的，管理员查看全部）"""
    merchant_id = None
    crew_id = None
    
    if current_user.role == UserRole.MERCHANT:
        from app.models.merchant import Merchant
        merchant = await Merchant.filter(user=current_user).first()
        if merchant:
            merchant_id = merchant.id
    elif current_user.role == UserRole.CREW:
        from app.models.crew import Crew
        crew = await Crew.filter(user=current_user).first()
        if crew:
            crew_id = crew.id
    
    return await SplitPaymentService.get_split_stats(merchant_id, crew_id)


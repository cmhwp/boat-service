#!/usr/bin/env python3
"""初始化分账规则"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from tortoise import Tortoise
from app.config.database import DATABASE_CONFIG
from app.models.split_payment import SplitRule, SplitType


async def init_split_rules():
    """初始化分账规则"""
    try:
        # 初始化数据库连接
        await Tortoise.init(config=DATABASE_CONFIG)
        await Tortoise.generate_schemas()
        
        print("开始初始化分账规则...")
        
        # 检查是否已存在规则
        booking_rule = await SplitRule.filter(split_type=SplitType.BOOKING, is_active=True).first()
        if not booking_rule:
            # 创建预约分账规则：平台5%，商家35%，船员60%
            booking_rule = await SplitRule.create(
                split_type=SplitType.BOOKING,
                platform_ratio=5.00,
                merchant_ratio=35.00,
                crew_ratio=60.00,
                description="预约服务分账规则：平台抽成5%，商家35%，船员60%",
                is_active=True
            )
            print(f"[OK] 已创建预约分账规则: {booking_rule}")
        else:
            print(f"[OK] 预约分账规则已存在: {booking_rule}")
        
        # 创建订单分账规则：平台10%，商家90%
        order_rule = await SplitRule.filter(split_type=SplitType.ORDER, is_active=True).first()
        if not order_rule:
            order_rule = await SplitRule.create(
                split_type=SplitType.ORDER,
                platform_ratio=10.00,
                merchant_ratio=90.00,
                crew_ratio=0.00,
                description="订单商品分账规则：平台抽成10%，商家90%",
                is_active=True
            )
            print(f"[OK] 已创建订单分账规则: {order_rule}")
        else:
            print(f"[OK] 订单分账规则已存在: {order_rule}")
        
        print("\n[OK] 分账规则初始化完成！")
        print(f"\n分账规则配置:")
        print(f"  预约服务: 平台{booking_rule.platform_ratio}% | 商家{booking_rule.merchant_ratio}% | 船员{booking_rule.crew_ratio}%")
        print(f"  订单商品: 平台{order_rule.platform_ratio}% | 商家{order_rule.merchant_ratio}%")
        
    except Exception as e:
        print(f"[ERROR] 初始化失败: {str(e)}")
        raise
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(init_split_rules())


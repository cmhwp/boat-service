#!/usr/bin/env python3
"""
测试数据库连接脚本
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from tortoise import Tortoise
from app.config.database import DATABASE_CONFIG
from app.models.user import User


async def test_database_connection():
    """测试数据库连接"""
    try:
        print("🔗 正在连接数据库...")
        await Tortoise.init(config=DATABASE_CONFIG)
        print("✅ 数据库连接成功")
        
        # 测试基本查询
        print("🔍 测试用户查询...")
        user_count = await User.all().count()
        print(f"📊 用户总数: {user_count}")
        
        # 测试特定查询
        admin_user = await User.filter(username="admin").first()
        if admin_user:
            print(f"👤 找到管理员用户: {admin_user.username}")
        else:
            print("❌ 未找到管理员用户")
        
        print("✅ 数据库连接测试完成")
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()
        print("🔐 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(test_database_connection()) 
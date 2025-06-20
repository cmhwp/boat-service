#!/usr/bin/env python3
"""
初始化管理员账户脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.config.database import DATABASE_CONFIG
from app.models.user import User, UserRole


async def init_admin():
    """初始化管理员账户"""
    try:
        # 初始化数据库连接
        await Tortoise.init(config=DATABASE_CONFIG)
        
        # 检查管理员是否已存在
        admin_exists = await User.filter(username="admin").first()
        if admin_exists:
            print("❌ 管理员账户 admin1 已存在")
            return
        
        # 检查邮箱是否已被使用
        email_exists = await User.filter(email="admin@boat.com").first()
        if email_exists:
            print("❌ 邮箱 admin@boat.com 已被使用")
            return
        
        # 创建管理员账户
        hashed_password = User.hash_password("admin123")
        admin_user = await User.create(
            username="admin1",
            email="admin@boat.com",
            password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        print("✅ 管理员账户创建成功！")
        print(f"   用户名: {admin_user.username}")
        print(f"   邮箱: {admin_user.email}")
        print(f"   角色: {admin_user.role}")
        print(f"   ID: {admin_user.id}")
        print(f"   创建时间: {admin_user.created_at}")
        
    except Exception as e:
        print(f"❌ 创建管理员账户失败: {str(e)}")
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()


if __name__ == "__main__":
    print("🚀 开始初始化管理员账户...")
    asyncio.run(init_admin())
    print("🎉 初始化完成！") 
import asyncio
from tortoise import Tortoise
from app.config.database import DATABASE_CONFIG
from app.models.user import User, UserRole, RealnameStatus


async def init_database():
    """初始化数据库"""
    await Tortoise.init(config=DATABASE_CONFIG)
    await Tortoise.generate_schemas()
    
    # 创建默认管理员用户
    admin_exists = await User.get_or_none(username="admin")
    if not admin_exists:
        admin_user = await User.create(
            username="admin",
            email="admin@example.com",
            password=User.hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            realname_status=RealnameStatus.VERIFIED
        )
        print(f"[OK] 默认管理员用户创建成功: {admin_user.username}")
    else:
        print("[INFO] 管理员用户已存在")
    
    await Tortoise.close_connections()
    print("[OK] 数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(init_database()) 
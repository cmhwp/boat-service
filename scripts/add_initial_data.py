"""
添加初始测试数据脚本
"""
import asyncio
import sys
import os
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.config.database import DATABASE_CONFIG
from app.models.user import User, UserRole, RealnameStatus
from app.models.merchant import Merchant, MerchantStatus
from app.models.boat import Boat, BoatType, BoatStatus
from app.models.product import Product, ProductCategory, ProductStatus
from app.models.crew import CrewApplication, Crew, CrewApplicationStatus, CrewStatus


async def add_initial_data():
    """添加初始数据"""
    print("🚀 开始添加初始数据...")
    
    # 初始化数据库连接
    await Tortoise.init(config=DATABASE_CONFIG)
    
    # 1. 添加用户数据
    await add_users()
    
    # 2. 添加商家数据
    await add_merchants()
    
    # 3. 添加船艇数据
    await add_boats()
    
    # 4. 添加农产品数据
    await add_products()
    
    # 5. 添加船员数据
    await add_crew_data()
    
    # 关闭数据库连接
    await Tortoise.close_connections()
    print("✅ 初始数据添加完成!")


async def add_users():
    """添加用户数据"""
    print("📝 添加用户数据...")
    
    users_data = [
        {
            "username": "admin",
            "email": "admin@boat-service.com",
            "password": User.hash_password("admin123"),
            "role": UserRole.ADMIN,
            "is_active": True,
            "realname_status": RealnameStatus.VERIFIED,
            "phone": "13800138000"
        },
        {
            "username": "merchant1",
            "email": "merchant1@example.com", 
            "password": User.hash_password("merchant123456"),
            "role": UserRole.MERCHANT,
            "is_active": True,
            "realname_status": RealnameStatus.VERIFIED,
            "phone": "13800138001"
        },
        {
            "username": "merchant2",
            "email": "merchant2@example.com",
            "password": User.hash_password("merchant123456"),
            "role": UserRole.MERCHANT,
            "is_active": True,
            "realname_status": RealnameStatus.VERIFIED,
            "phone": "13800138002"
        },
        {
            "username": "user1",
            "email": "user1@example.com",
            "password": User.hash_password("user123456"),
            "role": UserRole.USER,
            "is_active": True,
            "realname_status": RealnameStatus.VERIFIED,
            "phone": "13800138003"
        },
        {
            "username": "user2",
            "email": "user2@example.com",
            "password": User.hash_password("user123456"),
            "role": UserRole.USER,
            "is_active": True,
            "realname_status": RealnameStatus.UNVERIFIED,
            "phone": "13800138004"
        },
        {
            "username": "crew1",
            "email": "crew1@example.com",
            "password": User.hash_password("crew123456"),
            "role": UserRole.CREW,
            "is_active": True,
            "realname_status": RealnameStatus.VERIFIED,
            "phone": "13800138005"
        },
        {
            "username": "crew2",
            "email": "crew2@example.com",
            "password": User.hash_password("crew123456"),
            "role": UserRole.CREW,
            "is_active": True,
            "realname_status": RealnameStatus.VERIFIED,
            "phone": "13800138006"
        }
    ]
    
    for user_data in users_data:
        user = await User.get_or_none(username=user_data["username"])
        if not user:
            await User.create(**user_data)
            print(f"  ✓ 创建用户: {user_data['username']} ({user_data['role']})")
        else:
            print(f"  ⚠️ 用户已存在: {user_data['username']}")


async def add_merchants():
    """添加商家数据"""
    print("🏪 添加商家数据...")
    
    # 获取商家用户
    merchant_user1 = await User.get(username="merchant1")
    merchant_user2 = await User.get(username="merchant2")
    
    merchants_data = [
        {
            "merchant_name": "蓝海船艇服务",
            "license_number": "440100000001234",
            "license_image": "merchant-licenses/license1.jpg",
            "contact_phone": "020-88888888",
            "address": "广州市海珠区滨江东路123号",
            "description": "专业提供高品质船艇租赁服务，拥有多艘现代化观光船和钓鱼船",
            "status": MerchantStatus.ACTIVE,
            "user": merchant_user1
        },
        {
            "merchant_name": "绿色农场直供",
            "license_number": "440100000005678",
            "license_image": "merchant-licenses/license2.jpg", 
            "contact_phone": "020-66666666",
            "address": "广州市番禺区农业示范园区",
            "description": "专注有机农产品种植和销售，产品绿色健康，直接从农场到餐桌",
            "status": MerchantStatus.ACTIVE,
            "user": merchant_user2
        }
    ]
    
    for merchant_data in merchants_data:
        merchant = await Merchant.get_or_none(merchant_name=merchant_data["merchant_name"])
        if not merchant:
            await Merchant.create(**merchant_data)
            print(f"  ✓ 创建商家: {merchant_data['merchant_name']}")
        else:
            print(f"  ⚠️ 商家已存在: {merchant_data['merchant_name']}")


async def add_boats():
    """添加船艇数据"""
    print("🚢 添加船艇数据...")
    
    # 获取商家
    merchant1 = await Merchant.get(merchant_name="蓝海船艇服务")
    
    boats_data = [
        {
            "name": "海风号观光船",
            "license_number": "GD001234",
            "boat_type": BoatType.SIGHTSEEING,
            "capacity": 50,
            "hourly_rate": Decimal("200.00"),
            "description": "豪华双层观光船，设施齐全，适合团体观光游览",
            "images": ["boats/boat1_1.jpg", "boats/boat1_2.jpg"],
            "status": BoatStatus.AVAILABLE,
            "current_location": "珠江码头A区",
            "merchant": merchant1
        },
        {
            "name": "渔乐号钓鱼船",
            "license_number": "GD005678",
            "boat_type": BoatType.FISHING,
            "capacity": 12,
            "hourly_rate": Decimal("150.00"),
            "description": "专业钓鱼船，配备完善的钓鱼设备和安全设施",
            "images": ["boats/boat2_1.jpg", "boats/boat2_2.jpg"],
            "status": BoatStatus.AVAILABLE,
            "current_location": "珠江码头B区",
            "merchant": merchant1
        },
        {
            "name": "快乐号客船",
            "license_number": "GD009012",
            "boat_type": BoatType.PASSENGER,
            "capacity": 30,
            "hourly_rate": Decimal("180.00"),
            "description": "舒适客船，适合商务接待和家庭出游",
            "images": ["boats/boat3_1.jpg"],
            "status": BoatStatus.AVAILABLE,
            "current_location": "珠江码头C区",
            "merchant": merchant1
        }
    ]
    
    for boat_data in boats_data:
        boat = await Boat.get_or_none(license_number=boat_data["license_number"])
        if not boat:
            await Boat.create(**boat_data)
            print(f"  ✓ 创建船艇: {boat_data['name']} (类型: {boat_data['boat_type']})")
        else:
            print(f"  ⚠️ 船艇已存在: {boat_data['name']}")


async def add_products():
    """添加农产品数据"""
    print("🥬 添加农产品数据...")
    
    # 获取商家
    merchant2 = await Merchant.get(merchant_name="绿色农场直供")
    
    products_data = [
        {
            "name": "有机番茄",
            "category": ProductCategory.VEGETABLE,
            "description": "新鲜有机番茄，无农药残留，口感甜美",
            "price": Decimal("8.80"),
            "stock": 100,
            "unit": "斤",
            "images": ["products/tomato1.jpg", "products/tomato2.jpg"],
            "rating": Decimal("4.80"),
            "sales_count": 55,
            "status": ProductStatus.AVAILABLE,
            "merchant": merchant2
        },
        {
            "name": "农家土鸡蛋",
            "category": ProductCategory.OTHER,
            "description": "散养土鸡蛋，营养丰富，蛋黄金黄",
            "price": Decimal("2.50"),
            "stock": 200,
            "unit": "个",
            "images": ["products/egg1.jpg"],
            "rating": Decimal("4.90"),
            "sales_count": 120,
            "status": ProductStatus.AVAILABLE,
            "merchant": merchant2
        },
        {
            "name": "新鲜草莓",
            "category": ProductCategory.FRUIT,
            "description": "当季新鲜草莓，香甜可口，富含维生素C",
            "price": Decimal("15.00"),
            "stock": 50,
            "unit": "盒",
            "images": ["products/strawberry1.jpg", "products/strawberry2.jpg"],
            "rating": Decimal("4.70"),
            "sales_count": 35,
            "status": ProductStatus.AVAILABLE,
            "merchant": merchant2
        },
        {
            "name": "有机青菜",
            "category": ProductCategory.VEGETABLE,
            "description": "绿色有机青菜，叶片肥厚，营养丰富",
            "price": Decimal("6.50"),
            "stock": 80,
            "unit": "斤",
            "images": ["products/vegetable1.jpg"],
            "rating": Decimal("4.60"),
            "sales_count": 45,
            "status": ProductStatus.AVAILABLE,
            "merchant": merchant2
        },
        {
            "name": "优质大米",
            "category": ProductCategory.GRAIN,
            "description": "东北优质大米，颗粒饱满，口感香甜",
            "price": Decimal("12.00"),
            "stock": 30,
            "unit": "袋(5斤)",
            "images": ["products/rice1.jpg"],
            "rating": Decimal("4.85"),
            "sales_count": 25,
            "status": ProductStatus.AVAILABLE,
            "merchant": merchant2
        },
        {
            "name": "新鲜海虾",
            "category": ProductCategory.SEAFOOD,
            "description": "活捉新鲜海虾，肉质鲜美，营养价值高",
            "price": Decimal("35.00"),
            "stock": 20,
            "unit": "斤",
            "images": ["products/shrimp1.jpg", "products/shrimp2.jpg"],
            "rating": Decimal("4.95"),
            "sales_count": 18,
            "status": ProductStatus.AVAILABLE,
            "merchant": merchant2
        }
    ]
    
    for product_data in products_data:
        product = await Product.get_or_none(name=product_data["name"], merchant=merchant2)
        if not product:
            await Product.create(**product_data)
            print(f"  ✓ 创建产品: {product_data['name']} (价格: ¥{product_data['price']})")
        else:
            print(f"  ⚠️ 产品已存在: {product_data['name']}")


async def add_crew_data():
    """添加船员相关数据"""
    print("👨‍⚓ 添加船员数据...")
    
    # 获取用户和商家
    crew_user1 = await User.get(username="crew1")
    crew_user2 = await User.get(username="crew2")
    merchant1 = await Merchant.get(merchant_name="蓝海船艇服务")
    
    # 添加船员申请
    applications_data = [
        {
            "user": crew_user1,
            "merchant": merchant1,
            "status": CrewApplicationStatus.APPROVED
        },
        {
            "user": crew_user2,
            "merchant": merchant1,
            "status": CrewApplicationStatus.APPROVED
        }
    ]
    
    for app_data in applications_data:
        existing_app = await CrewApplication.get_or_none(
            user=app_data["user"], 
            merchant=app_data["merchant"]
        )
        if not existing_app:
            await CrewApplication.create(**app_data)
            print(f"  ✓ 创建船员申请: {app_data['user'].username} -> {app_data['merchant'].merchant_name}")
    
    # 添加船员信息
    crews_data = [
        {
            "user": crew_user1,
            "merchant": merchant1,
            "boat_license": "GD船员001",
            "status": CrewStatus.ACTIVE,
            "rating": Decimal("4.80")
        },
        {
            "user": crew_user2,
            "merchant": merchant1,
            "boat_license": "GD船员002",
            "status": CrewStatus.ACTIVE,
            "rating": Decimal("4.65")
        }
    ]
    
    for crew_data in crews_data:
        existing_crew = await Crew.get_or_none(
            user=crew_data["user"], 
            merchant=crew_data["merchant"]
        )
        if not existing_crew:
            await Crew.create(**crew_data)
            print(f"  ✓ 创建船员: {crew_data['user'].username} (证号: {crew_data['boat_license']})")


async def print_summary():
    """打印数据统计摘要"""
    print("\n📊 数据统计摘要:")
    
    user_count = await User.all().count()
    merchant_count = await Merchant.all().count()
    boat_count = await Boat.all().count()
    product_count = await Product.all().count()
    crew_count = await Crew.all().count()
    
    print(f"  👥 用户总数: {user_count}")
    print(f"  🏪 商家总数: {merchant_count}")
    print(f"  🚢 船艇总数: {boat_count}")
    print(f"  🥬 产品总数: {product_count}")
    print(f"  👨‍⚓ 船员总数: {crew_count}")
    
    print("\n🔐 测试账号信息:")
    print("  管理员: admin / admin123")
    print("  商家1: merchant1 / 123456")
    print("  商家2: merchant2 / 123456")
    print("  用户1: user1 / 123456")
    print("  用户2: user2 / 123456")
    print("  船员1: crew1 / 123456")
    print("  船员2: crew2 / 123456")


if __name__ == "__main__":
    try:
        asyncio.run(add_initial_data())
        asyncio.run(print_summary())
    except Exception as e:
        print(f"❌ 添加初始数据失败: {str(e)}")
        import traceback
        traceback.print_exc() 
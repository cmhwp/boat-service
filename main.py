from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import ValidationError, IntegrityError
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.config.database import DATABASE_CONFIG
from app.config.redis_client import RedisClient
from app.routers.user import router as user_router
from app.routers.realname_auth import router as realname_auth_router
from app.routers.merchant import router as merchant_router
from app.routers.crew import router as crew_router
from app.routers.boat import router as boat_router
from app.routers.product import router as product_router
from app.utils.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    tortoise_validation_error_handler,
    tortoise_integrity_error_handler,
    general_exception_handler
)
from app.schemas.response import ResponseHelper

# 加载环境变量
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化Redis连接
    await RedisClient.initialize()
    
    yield
    
    # 关闭时清理资源
    await RedisClient.close()


# 创建FastAPI应用
app = FastAPI(
    title="绿色智能船艇农文旅服务平台",
    description="基于FastAPI+Tortoise ORM+MySQL+Redis的智能船艇服务平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该配置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, tortoise_validation_error_handler)
app.add_exception_handler(IntegrityError, tortoise_integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(user_router, prefix="/api/v1")
app.include_router(realname_auth_router, prefix="/api/v1")
app.include_router(merchant_router, prefix="/api/v1")
app.include_router(crew_router, prefix="/api/v1")
app.include_router(boat_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1")

# 数据库配置
register_tortoise(
    app,
    config=DATABASE_CONFIG,
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get("/")
async def root():
    """根路径"""
    data = {
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }
    return ResponseHelper.success(data, "欢迎使用绿色智能船艇农文旅服务平台")


@app.get("/health")
async def health_check():
    """健康检查"""
    from app.utils.redis_utils import RedisManager
    import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat() + "Z",
        "database": "connected",
        "redis": "disconnected",
        "redis_details": {}
    }
    
    # 检查Redis连接
    try:
        redis_test = await RedisManager.test_connection()
        if redis_test["success"]:
            health_status["redis"] = "connected"
            health_status["redis_details"] = {
                "message": redis_test["message"],
                "value_type": redis_test.get("value_type", "unknown")
            }
        else:
            health_status["redis"] = "disconnected"
            health_status["redis_details"] = {
                "error": redis_test["message"]
            }
    except Exception as e:
        health_status["redis"] = "disconnected"
        health_status["redis_details"] = {
            "error": f"健康检查异常: {e}"
        }
    
    return ResponseHelper.success(health_status, "系统运行正常")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

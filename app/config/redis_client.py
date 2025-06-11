import redis.asyncio as redis
import os
from typing import Optional
from .database import REDIS_CONFIG


class RedisClient:
    """Redis客户端单例"""
    
    _instance: Optional[redis.Redis] = None
    _initialized: bool = False
    
    @classmethod
    async def get_instance(cls) -> Optional[redis.Redis]:
        """获取Redis客户端实例"""
        if not cls._initialized:
            await cls.initialize()
        return cls._instance
    
    @classmethod
    async def initialize(cls) -> bool:
        """初始化Redis连接"""
        try:
            cls._instance = redis.Redis(**REDIS_CONFIG)
            await cls._instance.ping()
            cls._initialized = True
            print("✅ Redis连接成功")
            return True
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            cls._instance = None
            cls._initialized = False
            return False
    
    @classmethod
    async def close(cls):
        """关闭Redis连接"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            cls._initialized = False
            print("Redis连接已关闭")


# 便捷函数
async def get_redis_client() -> Optional[redis.Redis]:
    """获取Redis客户端"""
    return await RedisClient.get_instance() 
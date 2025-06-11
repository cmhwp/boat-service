import redis.asyncio as redis
from typing import Optional, Union
import json
from app.config.redis_client import get_redis_client


class RedisManager:
    """Redis管理器"""
    
    @staticmethod
    async def test_connection() -> dict:
        """测试Redis连接"""
        try:
            client = await get_redis_client()
            if not client:
                return {"success": False, "message": "Redis客户端未初始化"}
            
            # 测试ping
            await client.ping()
            
            # 测试设置和获取
            test_key = "test_connection"
            test_value = "test_value"
            await client.setex(test_key, 10, test_value)
            retrieved_value = await client.get(test_key)
            await client.delete(test_key)
            
            return {
                "success": True,
                "message": "Redis连接正常",
                "test_result": f"设置值: {test_value}, 获取值: {retrieved_value}",
                "value_type": type(retrieved_value).__name__
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Redis连接测试失败: {e}",
                "error_type": type(e).__name__
            }
    
    @staticmethod
    async def set_with_expiry(key: str, value: Union[str, dict], expire_seconds: int) -> bool:
        """设置带过期时间的键值对"""
        try:
            client = await get_redis_client()
            if not client:
                return False
            
            # 确保值是字符串格式
            if isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
            
            await client.setex(key, expire_seconds, value)
            return True
        except Exception as e:
            print(f"Redis设置失败: {e}")
            return False
    
    @staticmethod
    async def get(key: str) -> Optional[str]:
        """获取值"""
        try:
            client = await get_redis_client()
            if not client:
                return None
            
            value = await client.get(key)
            if value is None:
                return None
            
            # 检查值的类型，如果是bytes则decode，如果是str则直接返回
            if isinstance(value, bytes):
                return value.decode('utf-8')
            else:
                return str(value)
        except Exception as e:
            print(f"Redis获取失败: {e}")
            return None
    
    @staticmethod
    async def get_json(key: str) -> Optional[dict]:
        """获取JSON值"""
        try:
            value = await RedisManager.get(key)
            if value:
                return json.loads(value)
            return None
        except json.JSONDecodeError as e:
            print(f"Redis JSON解析失败: {e}, 原始值: {value}")
            return None
        except Exception as e:
            print(f"Redis获取JSON失败: {e}")
            return None
    
    @staticmethod
    async def delete(key: str) -> bool:
        """删除键"""
        try:
            client = await get_redis_client()
            if not client:
                return False
            
            await client.delete(key)
            return True
        except Exception as e:
            print(f"Redis删除失败: {e}")
            return False
    
    @staticmethod
    async def exists(key: str) -> bool:
        """检查键是否存在"""
        try:
            client = await get_redis_client()
            if not client:
                return False
            
            return bool(await client.exists(key))
        except Exception as e:
            print(f"Redis检查存在性失败: {e}")
            return False
    
    @staticmethod
    async def get_ttl(key: str) -> int:
        """获取键的剩余过期时间"""
        try:
            client = await get_redis_client()
            if not client:
                return -1
            
            return await client.ttl(key)
        except Exception as e:
            print(f"Redis获取TTL失败: {e}")
            return -1


class EmailVerificationManager:
    """邮箱验证管理器"""
    
    VERIFICATION_CODE_PREFIX = "email_verification:"
    VERIFICATION_CODE_EXPIRE = 300  # 5分钟
    
    @staticmethod
    async def store_verification_code(email: str, code: str) -> bool:
        """存储验证码"""
        key = f"{EmailVerificationManager.VERIFICATION_CODE_PREFIX}{email}"
        return await RedisManager.set_with_expiry(
            key, code, EmailVerificationManager.VERIFICATION_CODE_EXPIRE
        )
    
    @staticmethod
    async def get_verification_code(email: str) -> Optional[str]:
        """获取验证码"""
        key = f"{EmailVerificationManager.VERIFICATION_CODE_PREFIX}{email}"
        return await RedisManager.get(key)
    
    @staticmethod
    async def verify_code(email: str, code: str) -> bool:
        """验证验证码"""
        stored_code = await EmailVerificationManager.get_verification_code(email)
        if stored_code and stored_code == code:
            # 验证成功后删除验证码
            await EmailVerificationManager.delete_verification_code(email)
            return True
        return False
    
    @staticmethod
    async def delete_verification_code(email: str) -> bool:
        """删除验证码"""
        key = f"{EmailVerificationManager.VERIFICATION_CODE_PREFIX}{email}"
        return await RedisManager.delete(key)
    
    @staticmethod
    async def get_code_ttl(email: str) -> int:
        """获取验证码剩余时间"""
        key = f"{EmailVerificationManager.VERIFICATION_CODE_PREFIX}{email}"
        return await RedisManager.get_ttl(key)


class PasswordResetManager:
    """密码重置管理器"""
    
    RESET_TOKEN_PREFIX = "password_reset:"
    RESET_TOKEN_EXPIRE = 1800  # 30分钟
    
    @staticmethod
    async def store_reset_token(email: str, token: str, user_id: int) -> bool:
        """存储重置token"""
        key = f"{PasswordResetManager.RESET_TOKEN_PREFIX}{token}"
        data = {
            "email": email,
            "user_id": user_id
        }
        return await RedisManager.set_with_expiry(
            key, data, PasswordResetManager.RESET_TOKEN_EXPIRE
        )
    
    @staticmethod
    async def get_reset_token_data(token: str) -> Optional[dict]:
        """获取重置token数据"""
        key = f"{PasswordResetManager.RESET_TOKEN_PREFIX}{token}"
        return await RedisManager.get_json(key)
    
    @staticmethod
    async def verify_reset_token(token: str) -> Optional[dict]:
        """验证重置token"""
        data = await PasswordResetManager.get_reset_token_data(token)
        if data:
            # 验证成功后删除token（一次性使用）
            await PasswordResetManager.delete_reset_token(token)
            return data
        return None
    
    @staticmethod
    async def delete_reset_token(token: str) -> bool:
        """删除重置token"""
        key = f"{PasswordResetManager.RESET_TOKEN_PREFIX}{token}"
        return await RedisManager.delete(key)
    
    @staticmethod
    async def get_token_ttl(token: str) -> int:
        """获取token剩余时间"""
        key = f"{PasswordResetManager.RESET_TOKEN_PREFIX}{token}"
        return await RedisManager.get_ttl(key) 
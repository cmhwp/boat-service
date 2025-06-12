import os
from typing import List
import json


class COSConfig:
    """腾讯云COS配置"""
    
    # 基础配置
    SECRET_ID = os.getenv("COS_SECRET_ID")
    SECRET_KEY = os.getenv("COS_SECRET_KEY")
    REGION = os.getenv("COS_REGION", "ap-guangzhou")
    BUCKET = os.getenv("COS_BUCKET")
    DOMAIN = os.getenv("COS_DOMAIN")
    
    # 上传配置
    MAX_FILE_SIZE = int(os.getenv("COS_MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_IMAGE_TYPES = json.loads(os.getenv("COS_ALLOWED_IMAGE_TYPES", '["jpg", "jpeg", "png", "gif", "webp"]'))
    
    # 文件路径前缀
    AVATAR_PREFIX = os.getenv("COS_AVATAR_PREFIX", "avatars/")
    IDENTITY_PREFIX = os.getenv("COS_IDENTITY_PREFIX", "identity/")
    BOAT_PREFIX = os.getenv("COS_BOAT_PREFIX", "boats/")
    SERVICE_PREFIX = os.getenv("COS_SERVICE_PREFIX", "services/")
    PRODUCT_PREFIX = os.getenv("COS_PRODUCT_PREFIX", "products/")
    REVIEW_PREFIX = os.getenv("COS_REVIEW_PREFIX", "reviews/")
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        required_fields = [
            cls.SECRET_ID,
            cls.SECRET_KEY,
            cls.REGION,
            cls.BUCKET,
            cls.DOMAIN
        ]
        return all(field is not None for field in required_fields)
    
    @classmethod
    def get_full_url(cls, key: str) -> str:
        """获取完整的文件URL"""
        if cls.DOMAIN:
            return f"{cls.DOMAIN.rstrip('/')}/{key}"
        return f"https://{cls.BUCKET}.cos.{cls.REGION}.myqcloud.com/{key}"


# 全局配置实例
cos_config = COSConfig() 
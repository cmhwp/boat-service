import os
from typing import Dict, Any

# 数据库配置
DATABASE_CONFIG: Dict[str, Any] = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "3306")),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", "123456"),
                "database": os.getenv("DB_NAME", "boat_service"),
                "charset": "utf8mb4",
                "echo": os.getenv("DB_ECHO", "False").lower() == "true",
            }
        }
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user", 
                "app.models.realname_auth", 
                "app.models.merchant", 
                "app.models.crew", 
                "aerich.models"
            ],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai"
}

# Redis配置
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD", None),
    "decode_responses": True,
} 
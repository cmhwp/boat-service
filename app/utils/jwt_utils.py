import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.schemas.user import TokenPayload
from app.models.user import User


class JWTManager:
    """JWT管理器"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    def create_access_token(self, user: User) -> Dict[str, Any]:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,  # 转换为秒
        }

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """验证token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_payload = TokenPayload(**payload)
            return token_payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None


# 全局JWT管理器实例
jwt_manager = JWTManager() 
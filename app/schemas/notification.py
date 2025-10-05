from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class NotificationCreateSchema(BaseModel):
    """通知创建"""
    user_id: int = Field(..., description="接收用户ID")
    notification_type: str = Field(..., description="通知类型")
    title: str = Field(..., max_length=100, description="通知标题")
    content: str = Field(..., description="通知内容")
    related_id: Optional[int] = Field(None, description="关联数据ID")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class NotificationResponseSchema(BaseModel):
    """通知响应"""
    id: int
    notification_type: str
    title: str
    content: str
    related_id: Optional[int]
    extra_data: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    read_at: Optional[datetime]
    user_id: int


class NotificationListItemSchema(BaseModel):
    """通知列表项"""
    id: int
    notification_type: str
    title: str
    content: str
    status: str
    created_at: datetime


class NotificationQuerySchema(BaseModel):
    """通知查询"""
    notification_type: Optional[str] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class NotificationStatsSchema(BaseModel):
    """通知统计"""
    total_count: int
    unread_count: int
    read_count: int


class NotificationMarkReadSchema(BaseModel):
    """标记已读"""
    notification_ids: list[int] = Field(..., description="通知ID列表")


class WebSocketMessageSchema(BaseModel):
    """WebSocket消息"""
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


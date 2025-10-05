from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.utils.auth import get_current_user, get_user_from_token
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationQuerySchema,
    NotificationMarkReadSchema
)
from app.schemas.response import ApiResponse
from app.utils.websocket_manager import websocket_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["通知管理"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket连接端点"""
    try:
        # 验证token并获取用户
        user = await get_user_from_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # 建立连接
        await websocket_manager.connect(websocket, user.id)
        logger.info(f"WebSocket连接建立: user_id={user.id}")
        
        try:
            # 发送欢迎消息
            await websocket_manager.send_personal_message(
                {
                    "type": "connection",
                    "data": {
                        "message": "连接成功",
                        "user_id": user.id
                    }
                },
                user.id
            )
            
            # 保持连接
            while True:
                data = await websocket.receive_text()
                # 心跳检测
                if data == "ping":
                    await websocket.send_text("pong")
                
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket, user.id)
            logger.info(f"WebSocket连接断开: user_id={user.id}")
        
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


@router.get("/", response_model=ApiResponse, summary="获取通知列表")
async def get_notifications(
    query: NotificationQuerySchema = Depends(),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知列表"""
    return await NotificationService.get_user_notifications(current_user, query)


@router.post("/mark-read", response_model=ApiResponse, summary="标记通知为已读")
async def mark_notifications_as_read(
    mark_data: NotificationMarkReadSchema,
    current_user: User = Depends(get_current_user)
):
    """标记指定通知为已读"""
    return await NotificationService.mark_as_read(current_user, mark_data)


@router.post("/mark-all-read", response_model=ApiResponse, summary="标记全部已读")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user)
):
    """标记所有通知为已读"""
    return await NotificationService.mark_all_as_read(current_user)


@router.get("/stats", response_model=ApiResponse, summary="获取通知统计")
async def get_notification_stats(
    current_user: User = Depends(get_current_user)
):
    """获取通知统计信息"""
    return await NotificationService.get_notification_stats(current_user)


@router.delete("/{notification_id}", response_model=ApiResponse, summary="删除通知")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除指定通知"""
    return await NotificationService.delete_notification(current_user, notification_id)


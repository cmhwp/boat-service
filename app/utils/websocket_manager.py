from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储用户ID到WebSocket连接的映射
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """建立WebSocket连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket连接建立: user_id={user_id}, 当前连接数={len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket连接断开: user_id={user_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        """发送个人消息"""
        if user_id in self.active_connections:
            disconnected_ws = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"发送消息失败: user_id={user_id}, error={str(e)}")
                    disconnected_ws.append(connection)
            
            # 清理断开的连接
            for ws in disconnected_ws:
                self.disconnect(ws, user_id)

    async def send_notification(self, user_id: int, notification: dict):
        """发送通知消息"""
        message = {
            "type": "notification",
            "data": notification
        }
        await self.send_personal_message(message, user_id)

    async def broadcast(self, message: dict, exclude_user_ids: List[int] = None):
        """广播消息（可排除特定用户）"""
        exclude_user_ids = exclude_user_ids or []
        for user_id in list(self.active_connections.keys()):
            if user_id not in exclude_user_ids:
                await self.send_personal_message(message, user_id)

    def get_connection_count(self, user_id: int = None) -> int:
        """获取连接数"""
        if user_id:
            return len(self.active_connections.get(user_id, []))
        return sum(len(connections) for connections in self.active_connections.values())

    def is_user_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()


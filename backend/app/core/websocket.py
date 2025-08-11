"""
WebSocket 管理器
"""
from typing import List, Dict, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 存储活跃连接: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储用户订阅: {client_id: set(channels)}
        self.subscriptions: Dict[str, set] = {}
        # 存储频道订阅者: {channel: set(client_ids)}
        self.channels: Dict[str, set] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        
        logger.info(f"WebSocket连接建立: {client_id}")
        
        # 发送欢迎消息
        await self.send_message(client_id, {
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, client_id: str):
        """断开WebSocket连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # 清理订阅
        if client_id in self.subscriptions:
            for channel in self.subscriptions[client_id]:
                if channel in self.channels:
                    self.channels[channel].discard(client_id)
                    if not self.channels[channel]:
                        del self.channels[channel]
            del self.subscriptions[client_id]
        
        logger.info(f"WebSocket连接断开: {client_id}")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """向特定客户端发送消息"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                return True
            except Exception as e:
                logger.error(f"发送消息失败 {client_id}: {e}")
                self.disconnect(client_id)
                return False
        return False
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接的客户端"""
        if not self.active_connections:
            return
        
        disconnected_clients = []
        for client_id in self.active_connections:
            success = await self.send_message(client_id, message)
            if not success:
                disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """向特定频道广播消息"""
        if channel not in self.channels:
            return
        
        subscribers = self.channels[channel].copy()
        disconnected_clients = []
        
        for client_id in subscribers:
            success = await self.send_message(client_id, message)
            if not success:
                disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def subscribe(self, client_id: str, channel: str):
        """订阅频道"""
        if client_id not in self.subscriptions:
            return False
        
        self.subscriptions[client_id].add(channel)
        
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(client_id)
        
        logger.info(f"客户端 {client_id} 订阅频道 {channel}")
        return True
    
    def unsubscribe(self, client_id: str, channel: str):
        """取消订阅频道"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(channel)
        
        if channel in self.channels:
            self.channels[channel].discard(client_id)
            if not self.channels[channel]:
                del self.channels[channel]
        
        logger.info(f"客户端 {client_id} 取消订阅频道 {channel}")
        return True
    
    def get_channel_subscribers(self, channel: str) -> List[str]:
        """获取频道订阅者列表"""
        return list(self.channels.get(channel, set()))
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            "total_connections": len(self.active_connections),
            "active_channels": len(self.channels),
            "connections": list(self.active_connections.keys()),
            "channels": {
                channel: len(subscribers) 
                for channel, subscribers in self.channels.items()
            }
        }


# 全局连接管理器实例
manager = ConnectionManager()


class NotificationService:
    """通知服务"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
    
    async def notify_experiment_status(self, experiment_id: str, status: str, progress: int = 0, message: str = ""):
        """通知实验状态变化"""
        notification = {
            "type": "experiment_status",
            "experiment_id": experiment_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送到实验频道
        channel = f"experiment:{experiment_id}"
        await self.manager.broadcast_to_channel(channel, notification)
        
        # 发送到全局实验频道
        await self.manager.broadcast_to_channel("experiments", notification)
    
    async def notify_experiment_complete(self, experiment_id: str, results: Dict[str, Any]):
        """通知实验完成"""
        notification = {
            "type": "experiment_complete",
            "experiment_id": experiment_id,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        channel = f"experiment:{experiment_id}"
        await self.manager.broadcast_to_channel(channel, notification)
        await self.manager.broadcast_to_channel("experiments", notification)
    
    async def notify_experiment_error(self, experiment_id: str, error_message: str):
        """通知实验错误"""
        notification = {
            "type": "experiment_error",
            "experiment_id": experiment_id,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        channel = f"experiment:{experiment_id}"
        await self.manager.broadcast_to_channel(channel, notification)
        await self.manager.broadcast_to_channel("experiments", notification)
    
    async def notify_system_status(self, status: Dict[str, Any]):
        """通知系统状态"""
        notification = {
            "type": "system_status",
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.manager.broadcast_to_channel("system", notification)
    
    async def notify_task_queue_status(self, queue_info: Dict[str, Any]):
        """通知任务队列状态"""
        notification = {
            "type": "task_queue_status",
            "queue_info": queue_info,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.manager.broadcast_to_channel("system", notification)
    
    async def send_custom_notification(self, channel: str, notification_type: str, data: Dict[str, Any]):
        """发送自定义通知"""
        notification = {
            "type": notification_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.manager.broadcast_to_channel(channel, notification)


# 全局通知服务实例
notification_service = NotificationService(manager)


async def handle_websocket_message(client_id: str, message: Dict[str, Any]):
    """处理WebSocket消息"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        channel = message.get("channel")
        if channel:
            success = manager.subscribe(client_id, channel)
            await manager.send_message(client_id, {
                "type": "subscription_response",
                "channel": channel,
                "success": success,
                "message": f"订阅频道 {channel} {'成功' if success else '失败'}"
            })
    
    elif message_type == "unsubscribe":
        channel = message.get("channel")
        if channel:
            success = manager.unsubscribe(client_id, channel)
            await manager.send_message(client_id, {
                "type": "unsubscription_response",
                "channel": channel,
                "success": success,
                "message": f"取消订阅频道 {channel} {'成功' if success else '失败'}"
            })
    
    elif message_type == "ping":
        await manager.send_message(client_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    elif message_type == "get_info":
        info = manager.get_connection_info()
        await manager.send_message(client_id, {
            "type": "connection_info",
            "info": info
        })
    
    else:
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"未知消息类型: {message_type}"
        })
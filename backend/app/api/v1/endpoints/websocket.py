"""
WebSocket API 端点
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import logging
from typing import Dict, Any

from app.core.websocket import manager, notification_service, handle_websocket_message
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/connect/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket连接端点"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(client_id, message)
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "无效的JSON格式"
                })
            except Exception as e:
                logger.error(f"处理WebSocket消息失败 {client_id}: {e}")
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": f"消息处理失败: {str(e)}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket连接异常 {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/connections")
async def get_connection_info():
    """获取连接信息"""
    return {
        "success": True,
        "data": manager.get_connection_info()
    }


@router.post("/notify/experiment/{experiment_id}")
async def notify_experiment_status(
    experiment_id: str,
    status: str,
    progress: int = 0,
    message: str = ""
):
    """手动发送实验状态通知（用于测试）"""
    await notification_service.notify_experiment_status(
        experiment_id, status, progress, message
    )
    return {"success": True, "message": "通知已发送"}


@router.post("/notify/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """广播消息（用于测试）"""
    notification = {
        "type": "broadcast",
        "data": message,
        "timestamp": "now"
    }
    await manager.broadcast(notification)
    return {"success": True, "message": "广播消息已发送"}


@router.post("/notify/channel/{channel}")
async def notify_channel(channel: str, message: Dict[str, Any]):
    """向特定频道发送通知（用于测试）"""
    await notification_service.send_custom_notification(
        channel, "custom", message
    )
    return {"success": True, "message": f"消息已发送到频道 {channel}"}
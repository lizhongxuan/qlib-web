"""
APM监控API端点
提供应用性能监控和系统健康检查接口
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from ...services.apm_service import apm_service
from ...services.error_logging_service import error_logging_service, ErrorCategory, ErrorLevel
from ...services.user_analytics_service import user_analytics_service, ActionType


router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Any:
    """
    系统健康检查
    """
    try:
        health_data = apm_service.get_health_check()
        return {
            "success": True,
            "data": health_data
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "status": "critical",
                "error": str(e)
            }
        }


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取性能指标仪表盘
    需要管理员权限
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        dashboard_data = apm_service.get_performance_dashboard()
        return {
            "success": True,
            "message": "获取性能指标成功",
            "data": dashboard_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标失败: {str(e)}"
        )


@router.get("/performance/summary", response_model=Dict[str, Any])
async def get_performance_summary(
    minutes: int = 5,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取性能摘要
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        summary = apm_service.collector.get_performance_summary(minutes)
        return {
            "success": True,
            "message": "获取性能摘要成功",
            "data": summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能摘要失败: {str(e)}"
        )


@router.post("/metrics/custom", response_model=Dict[str, Any])
async def record_custom_metric(
    metric_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    记录自定义性能指标
    """
    try:
        name = metric_data.get("name")
        value = metric_data.get("value")
        tags = metric_data.get("tags", {})
        unit = metric_data.get("unit", "ms")
        
        if not name or value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少必要参数: name和value"
            )
        
        # 添加用户标签
        tags["user_id"] = str(current_user.id)
        tags["username"] = current_user.username
        
        apm_service.record_custom_metric(name, float(value), tags, unit)
        
        return {
            "success": True,
            "message": "自定义指标记录成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录自定义指标失败: {str(e)}"
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取当前告警信息
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        dashboard_data = apm_service.get_performance_dashboard()
        alerts = dashboard_data.get("alerts", [])
        
        return {
            "success": True,
            "message": "获取告警信息成功",
            "data": {
                "alerts": alerts,
                "alert_count": len(alerts),
                "critical_count": len([a for a in alerts if a.get("level") == "critical"]),
                "warning_count": len([a for a in alerts if a.get("level") == "warning"])
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警信息失败: {str(e)}"
        )


@router.put("/alerts/config", response_model=Dict[str, Any])
async def update_alert_config(
    config_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新告警配置
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        # 更新告警阈值
        if "thresholds" in config_data:
            apm_service.alert_thresholds.update(config_data["thresholds"])
        
        # 更新告警开关
        if "alerts_enabled" in config_data:
            apm_service.alerts_enabled = config_data["alerts_enabled"]
        
        return {
            "success": True,
            "message": "告警配置更新成功",
            "data": {
                "thresholds": apm_service.alert_thresholds,
                "alerts_enabled": apm_service.alerts_enabled
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新告警配置失败: {str(e)}"
        )


@router.get("/system/stats", response_model=Dict[str, Any])
async def get_system_stats(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取系统统计信息
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        import psutil
        import os
        from datetime import datetime
        
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        # 获取进程信息
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        stats = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": disk.percent,
                "boot_time": boot_time.isoformat(),
                "cpu_count": psutil.cpu_count(),
            },
            "process": {
                "pid": os.getpid(),
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            },
            "metrics": {
                "active_requests": len(apm_service.collector.active_requests),
                "total_performance_metrics": len(apm_service.collector.performance_metrics),
                "total_request_metrics": len(amp_service.collector.request_metrics),
                "total_system_metrics": len(apm_service.collector.system_metrics)
            }
        }
        
        return {
            "success": True,
            "message": "获取系统统计成功",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统统计失败: {str(e)}"
        )


@router.get("/errors/dashboard", response_model=Dict[str, Any])
async def get_error_dashboard(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取错误监控仪表盘
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        dashboard_data = error_logging_service.get_error_dashboard()
        return {
            "success": True,
            "message": "获取错误仪表盘成功",
            "data": dashboard_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错误仪表盘失败: {str(e)}"
        )


@router.get("/errors/recent", response_model=Dict[str, Any])
async def get_recent_errors(
    limit: int = 50,
    hours: int = 24,
    level: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取最近的错误记录
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        # 转换枚举类型
        error_level = None
        if level:
            try:
                error_level = ErrorLevel(level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的错误级别: {level}"
                )
        
        error_category = None
        if category:
            try:
                error_category = ErrorCategory(category)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的错误分类: {category}"
                )
        
        errors = error_logging_service.get_recent_errors(
            limit=limit,
            hours=hours,
            level=error_level,
            category=error_category
        )
        
        return {
            "success": True,
            "message": "获取最近错误成功",
            "data": {
                "errors": errors,
                "total": len(errors),
                "filters": {
                    "limit": limit,
                    "hours": hours,
                    "level": level,
                    "category": category
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取最近错误失败: {str(e)}"
        )


@router.get("/errors/statistics", response_model=Dict[str, Any])
async def get_error_statistics(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取错误统计信息
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        statistics = error_logging_service.get_error_statistics(hours=hours)
        return {
            "success": True,
            "message": "获取错误统计成功",
            "data": statistics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错误统计失败: {str(e)}"
        )


@router.post("/errors/log", response_model=Dict[str, Any])
async def log_custom_error(
    error_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    记录自定义错误
    """
    try:
        message = error_data.get("message")
        level = error_data.get("level", "error")
        category = error_data.get("category", "unknown")
        additional_context = error_data.get("context", {})
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少错误消息"
            )
        
        # 转换枚举类型
        try:
            error_level = ErrorLevel(level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的错误级别: {level}"
            )
        
        try:
            error_category = ErrorCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的错误分类: {category}"
            )
        
        # 记录错误
        request_context = {
            "user_id": current_user.id,
            "additional_context": additional_context
        }
        
        if error_level == ErrorLevel.WARNING:
            error_record = error_logging_service.log_warning(
                message, error_category, request_context
            )
        else:
            error_record = error_logging_service.collector.collect_custom_error(
                message, error_level, error_category, request_context, additional_context
            )
        
        return {
            "success": True,
            "message": "错误记录成功",
            "data": {
                "error_id": f"{error_record.timestamp.isoformat()}_{error_record.exception_type}"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录错误失败: {str(e)}"
        )


@router.post("/analytics/track", response_model=Dict[str, Any])
async def track_user_action(
    action_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    追踪用户行为
    """
    try:
        action_type_str = action_data.get("action_type")
        page = action_data.get("page")
        resource_id = action_data.get("resource_id")
        duration = action_data.get("duration")
        
        if not action_type_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少行为类型"
            )
        
        # 转换行为类型
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的行为类型: {action_type_str}"
            )
        
        # 追踪用户行为
        user_analytics_service.track_action(
            user_id=current_user.id,
            action_type=action_type,
            page=page,
            resource_id=resource_id,
            duration=duration,
            request_info=action_data.get("request_info", {})
        )
        
        return {
            "success": True,
            "message": "用户行为追踪成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"追踪用户行为失败: {str(e)}"
        )


@router.get("/analytics/user/{user_id}/insights", response_model=Dict[str, Any])
async def get_user_insights(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取用户行为洞察
    """
    # 权限检查：只能查看自己的数据，或管理员可以查看所有用户数据
    if current_user.id != user_id and current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        insights = user_analytics_service.get_user_insights(user_id)
        return {
            "success": True,
            "message": "获取用户洞察成功",
            "data": insights
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户洞察失败: {str(e)}"
        )


@router.get("/analytics/platform", response_model=Dict[str, Any])
async def get_platform_analytics(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取平台整体分析
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        analytics = user_analytics_service.get_platform_analytics(hours)
        return {
            "success": True,
            "message": "获取平台分析成功",
            "data": analytics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取平台分析失败: {str(e)}"
        )


@router.get("/analytics/segmentation", response_model=Dict[str, Any])
async def get_user_segmentation(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取用户分群分析
    """
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        segmentation = user_analytics_service.get_user_segmentation()
        return {
            "success": True,
            "message": "获取用户分群分析成功",
            "data": segmentation
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户分群分析失败: {str(e)}"
        )


@router.post("/analytics/session/start", response_model=Dict[str, Any])
async def start_user_session(
    session_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    开始用户会话追踪
    """
    try:
        session_id = session_data.get("session_id")
        request_info = session_data.get("request_info", {})
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少会话ID"
            )
        
        session = user_analytics_service.start_user_session(
            user_id=current_user.id,
            session_id=session_id,
            request_info=request_info
        )
        
        return {
            "success": True,
            "message": "会话追踪开始",
            "data": {
                "session_id": session_id,
                "start_time": session.start_time.isoformat() if session else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始会话追踪失败: {str(e)}"
        )


@router.put("/analytics/session/{session_id}/update", response_model=Dict[str, Any])
async def update_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户会话活动
    """
    try:
        user_analytics_service.update_user_session(session_id)
        return {
            "success": True,
            "message": "会话活动更新成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新会话活动失败: {str(e)}"
        )


@router.post("/analytics/session/{session_id}/end", response_model=Dict[str, Any])
async def end_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    结束用户会话追踪
    """
    try:
        user_analytics_service.end_user_session(session_id)
        return {
            "success": True,
            "message": "会话追踪结束"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"结束会话追踪失败: {str(e)}"
        )
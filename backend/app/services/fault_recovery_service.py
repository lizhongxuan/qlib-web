"""
故障自动恢复服务
提供服务自愈、故障检测、自动重启等功能
"""
import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import subprocess
import threading

from ..core.database import get_db
from ..services.error_logging_service import error_logging_service, ErrorCategory
from ..services.apm_service import apm_service


class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    RECOVERING = "recovering"
    FAILED = "failed"


class RecoveryAction(Enum):
    """恢复动作"""
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RESTART_PROCESS = "restart_process"
    SCALE_UP = "scale_up"
    FAILOVER = "failover"
    NOTIFY_ADMIN = "notify_admin"


@dataclass
class ServiceHealth:
    """服务健康状态"""
    name: str
    status: ServiceStatus
    last_check: datetime
    error_count: int = 0
    recovery_attempts: int = 0
    uptime: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time: float = 0.0
    error_rate: float = 0.0
    additional_metrics: Dict[str, Any] = None


@dataclass 
class RecoveryRule:
    """恢复规则"""
    service_name: str
    condition: str
    action: RecoveryAction
    max_attempts: int = 3
    cooldown_minutes: int = 5
    enabled: bool = True
    priority: int = 1


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks = {}
        
    def register_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """注册健康检查函数"""
        self.checks[name] = check_func
    
    async def check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            start_time = time.time()
            db = next(get_db())
            result = db.execute("SELECT 1").fetchone()
            response_time = (time.time() - start_time) * 1000
            
            return {
                "healthy": result is not None,
                "response_time": response_time,
                "error": None
            }
        except Exception as e:
            return {
                "healthy": False,
                "response_time": 0,
                "error": str(e)
            }
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """检查Redis健康状态"""
        try:
            # 这里需要实际的Redis连接
            # 简化实现，实际应该连接Redis
            return {
                "healthy": True,
                "response_time": 1.0,
                "error": None
            }
        except Exception as e:
            return {
                "healthy": False,
                "response_time": 0,
                "error": str(e)
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 判断健康状态
            healthy = (
                cpu_percent < 90 and 
                memory.percent < 90 and 
                disk.percent < 90
            )
            
            return {
                "healthy": healthy,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "error": None if healthy else "资源使用率过高"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """检查单个服务健康状态"""
        health_data = {
            "name": service_name,
            "status": ServiceStatus.HEALTHY,
            "last_check": datetime.now(),
            "error_count": 0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "response_time": 0.0,
            "error_rate": 0.0
        }
        
        try:
            # 根据服务名称执行相应的健康检查
            if service_name == "database":
                result = await self.check_database_health()
                health_data["response_time"] = result.get("response_time", 0)
                if not result["healthy"]:
                    health_data["status"] = ServiceStatus.CRITICAL
                    health_data["error_count"] = 1
                    
            elif service_name == "redis":
                result = await self.check_redis_health()
                health_data["response_time"] = result.get("response_time", 0)
                if not result["healthy"]:
                    health_data["status"] = ServiceStatus.WARNING
                    health_data["error_count"] = 1
                    
            elif service_name == "system":
                result = await self.check_system_resources()
                health_data["cpu_usage"] = result.get("cpu_percent", 0)
                health_data["memory_usage"] = result.get("memory_percent", 0)
                if not result["healthy"]:
                    health_data["status"] = ServiceStatus.WARNING
                    
            # 获取APM数据
            apm_data = apm_service.get_health_check()
            if apm_data.get("status") != "healthy":
                health_data["status"] = ServiceStatus.WARNING
                health_data["error_rate"] = 0.1  # 示例错误率
                
        except Exception as e:
            health_data["status"] = ServiceStatus.FAILED
            health_data["error_count"] = 1
            error_logging_service.log_error(
                e, ErrorCategory.SYSTEM,
                {"service": service_name, "check_type": "health_check"}
            )
        
        return ServiceHealth(**health_data)


class RecoveryExecutor:
    """恢复执行器"""
    
    def __init__(self):
        self.recovery_history = defaultdict(list)
        self.last_recovery_time = defaultdict(datetime)
        
    async def execute_recovery(self, service_name: str, action: RecoveryAction) -> Dict[str, Any]:
        """执行恢复动作"""
        try:
            result = {"success": False, "message": "", "action": action.value}
            
            if action == RecoveryAction.RESTART_SERVICE:
                result = await self._restart_service(service_name)
            elif action == RecoveryAction.CLEAR_CACHE:
                result = await self._clear_cache(service_name)
            elif action == RecoveryAction.RESTART_PROCESS:
                result = await self._restart_process(service_name)
            elif action == RecoveryAction.SCALE_UP:
                result = await self._scale_up_service(service_name)
            elif action == RecoveryAction.FAILOVER:
                result = await self._failover_service(service_name)
            elif action == RecoveryAction.NOTIFY_ADMIN:
                result = await self._notify_admin(service_name)
            
            # 记录恢复历史
            self.recovery_history[service_name].append({
                "timestamp": datetime.now(),
                "action": action.value,
                "success": result["success"],
                "message": result["message"]
            })
            
            # 限制历史记录数量
            if len(self.recovery_history[service_name]) > 50:
                self.recovery_history[service_name] = self.recovery_history[service_name][-50:]
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "message": f"恢复动作执行失败: {str(e)}",
                "action": action.value
            }
            
            error_logging_service.log_error(
                e, ErrorCategory.SYSTEM,
                {"service": service_name, "action": action.value}
            )
            
            return error_result
    
    async def _restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启服务"""
        try:
            # 这里应该实现实际的服务重启逻辑
            # 简化实现，返回成功状态
            await asyncio.sleep(1)  # 模拟重启时间
            
            return {
                "success": True,
                "message": f"服务 {service_name} 重启成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"服务 {service_name} 重启失败: {str(e)}"
            }
    
    async def _clear_cache(self, service_name: str) -> Dict[str, Any]:
        """清理缓存"""
        try:
            # 实现缓存清理逻辑
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "message": f"服务 {service_name} 缓存清理成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"缓存清理失败: {str(e)}"
            }
    
    async def _restart_process(self, service_name: str) -> Dict[str, Any]:
        """重启进程"""
        try:
            # 实现进程重启逻辑
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "message": f"进程 {service_name} 重启成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"进程重启失败: {str(e)}"
            }
    
    async def _scale_up_service(self, service_name: str) -> Dict[str, Any]:
        """扩容服务"""
        try:
            # 实现服务扩容逻辑
            await asyncio.sleep(3)
            
            return {
                "success": True,
                "message": f"服务 {service_name} 扩容成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"服务扩容失败: {str(e)}"
            }
    
    async def _failover_service(self, service_name: str) -> Dict[str, Any]:
        """故障转移"""
        try:
            # 实现故障转移逻辑
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "message": f"服务 {service_name} 故障转移成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"故障转移失败: {str(e)}"
            }
    
    async def _notify_admin(self, service_name: str) -> Dict[str, Any]:
        """通知管理员"""
        try:
            # 实现管理员通知逻辑
            # 这里可以集成邮件、短信、企业微信等通知方式
            
            return {
                "success": True,
                "message": f"已通知管理员关于服务 {service_name} 的问题"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"通知发送失败: {str(e)}"
            }


class FaultRecoveryService:
    """故障自动恢复服务"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.recovery_executor = RecoveryExecutor()
        self.recovery_rules = []
        self.services_status = {}
        self.monitor_task = None
        self.enabled = True
        
        # 初始化默认恢复规则
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """初始化默认恢复规则"""
        default_rules = [
            RecoveryRule(
                service_name="database",
                condition="status == 'critical'",
                action=RecoveryAction.RESTART_SERVICE,
                max_attempts=3,
                cooldown_minutes=5
            ),
            RecoveryRule(
                service_name="redis", 
                condition="status == 'warning'",
                action=RecoveryAction.CLEAR_CACHE,
                max_attempts=2,
                cooldown_minutes=3
            ),
            RecoveryRule(
                service_name="system",
                condition="cpu_usage > 95 or memory_usage > 95",
                action=RecoveryAction.RESTART_PROCESS,
                max_attempts=1,
                cooldown_minutes=10
            ),
            RecoveryRule(
                service_name="*",  # 通用规则
                condition="error_count > 10",
                action=RecoveryAction.NOTIFY_ADMIN,
                max_attempts=1,
                cooldown_minutes=30
            )
        ]
        
        self.recovery_rules.extend(default_rules)
    
    async def start_monitoring(self):
        """启动故障监控"""
        if not self.monitor_task:
            self.monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """停止故障监控"""
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
    
    async def _monitor_loop(self):
        """监控循环"""
        while True:
            try:
                if self.enabled:
                    await self._check_all_services()
                    await self._apply_recovery_rules()
                
                # 每30秒检查一次
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_logging_service.log_error(
                    e, ErrorCategory.SYSTEM,
                    {"component": "fault_recovery_monitor"}
                )
                await asyncio.sleep(30)
    
    async def _check_all_services(self):
        """检查所有服务健康状态"""
        services = ["database", "redis", "system", "application"]
        
        for service_name in services:
            try:
                health = await self.health_checker.check_service_health(service_name)
                self.services_status[service_name] = health
                
                # 记录状态变化
                if (service_name in self.services_status and 
                    self.services_status[service_name].status != health.status):
                    
                    error_logging_service.log_warning(
                        f"服务 {service_name} 状态变化: {health.status.value}",
                        ErrorCategory.SYSTEM
                    )
                
            except Exception as e:
                error_logging_service.log_error(
                    e, ErrorCategory.SYSTEM,
                    {"service": service_name, "component": "health_check"}
                )
    
    async def _apply_recovery_rules(self):
        """应用恢复规则"""
        for service_name, health in self.services_status.items():
            applicable_rules = self._get_applicable_rules(service_name, health)
            
            for rule in applicable_rules:
                if await self._should_apply_rule(rule, service_name, health):
                    await self._execute_recovery_rule(rule, service_name, health)
    
    def _get_applicable_rules(self, service_name: str, health: ServiceHealth) -> List[RecoveryRule]:
        """获取适用的恢复规则"""
        applicable_rules = []
        
        for rule in self.recovery_rules:
            if not rule.enabled:
                continue
                
            # 检查服务名称匹配
            if rule.service_name != "*" and rule.service_name != service_name:
                continue
            
            # 检查条件
            if self._evaluate_condition(rule.condition, health):
                applicable_rules.append(rule)
        
        # 按优先级排序
        applicable_rules.sort(key=lambda x: x.priority)
        return applicable_rules
    
    def _evaluate_condition(self, condition: str, health: ServiceHealth) -> bool:
        """评估恢复条件"""
        try:
            # 创建安全的评估环境
            context = {
                "status": health.status.value,
                "error_count": health.error_count,
                "cpu_usage": health.cpu_usage,
                "memory_usage": health.memory_usage,
                "response_time": health.response_time,
                "error_rate": health.error_rate
            }
            
            # 简单的条件评估
            # 实际实现中应该使用更安全的表达式解析器
            return eval(condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            error_logging_service.log_warning(
                f"条件评估失败: {condition}, 错误: {str(e)}",
                ErrorCategory.SYSTEM
            )
            return False
    
    async def _should_apply_rule(self, rule: RecoveryRule, service_name: str, health: ServiceHealth) -> bool:
        """检查是否应该应用规则"""
        # 检查最大尝试次数
        if health.recovery_attempts >= rule.max_attempts:
            return False
        
        # 检查冷却时间
        last_recovery = self.recovery_executor.last_recovery_time.get(service_name)
        if last_recovery:
            cooldown_end = last_recovery + timedelta(minutes=rule.cooldown_minutes)
            if datetime.now() < cooldown_end:
                return False
        
        return True
    
    async def _execute_recovery_rule(self, rule: RecoveryRule, service_name: str, health: ServiceHealth):
        """执行恢复规则"""
        try:
            # 更新恢复尝试次数
            health.recovery_attempts += 1
            health.status = ServiceStatus.RECOVERING
            
            # 执行恢复动作
            result = await self.recovery_executor.execute_recovery(service_name, rule.action)
            
            # 更新最后恢复时间
            self.recovery_executor.last_recovery_time[service_name] = datetime.now()
            
            # 记录恢复结果
            if result["success"]:
                error_logging_service.log_warning(
                    f"自动恢复成功: {service_name} - {result['message']}",
                    ErrorCategory.SYSTEM
                )
                # 重置错误计数
                health.error_count = 0
                health.recovery_attempts = 0
            else:
                error_logging_service.log_error(
                    Exception(result["message"]),
                    ErrorCategory.SYSTEM,
                    {"service": service_name, "recovery_action": rule.action.value}
                )
                
        except Exception as e:
            error_logging_service.log_error(
                e, ErrorCategory.SYSTEM,
                {"service": service_name, "rule": rule.service_name}
            )
    
    def add_recovery_rule(self, rule: RecoveryRule):
        """添加恢复规则"""
        self.recovery_rules.append(rule)
    
    def remove_recovery_rule(self, service_name: str, action: RecoveryAction):
        """移除恢复规则"""
        self.recovery_rules = [
            rule for rule in self.recovery_rules 
            if not (rule.service_name == service_name and rule.action == action)
        ]
    
    def get_service_status(self, service_name: str = None) -> Dict[str, Any]:
        """获取服务状态"""
        if service_name:
            health = self.services_status.get(service_name)
            if health:
                return asdict(health)
            return {"error": "Service not found"}
        
        return {
            service_name: asdict(health) 
            for service_name, health in self.services_status.items()
        }
    
    def get_recovery_history(self, service_name: str = None) -> Dict[str, Any]:
        """获取恢复历史"""
        if service_name:
            return {
                "service": service_name,
                "history": self.recovery_executor.recovery_history.get(service_name, [])
            }
        
        return dict(self.recovery_executor.recovery_history)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取故障恢复仪表盘数据"""
        # 统计服务状态
        status_counts = defaultdict(int)
        for health in self.services_status.values():
            status_counts[health.status.value] += 1
        
        # 统计恢复历史
        total_recoveries = sum(
            len(history) for history in self.recovery_executor.recovery_history.values()
        )
        
        successful_recoveries = 0
        for history in self.recovery_executor.recovery_history.values():
            successful_recoveries += sum(1 for h in history if h["success"])
        
        recovery_success_rate = successful_recoveries / total_recoveries if total_recoveries > 0 else 0
        
        # 最近的恢复记录
        recent_recoveries = []
        for service_name, history in self.recovery_executor.recovery_history.items():
            for record in history[-5:]:  # 最近5条
                recent_recoveries.append({
                    **record,
                    "service": service_name
                })
        
        recent_recoveries.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "overview": {
                "total_services": len(self.services_status),
                "healthy_services": status_counts.get("healthy", 0),
                "warning_services": status_counts.get("warning", 0),
                "critical_services": status_counts.get("critical", 0),
                "failed_services": status_counts.get("failed", 0)
            },
            "recovery_stats": {
                "total_recoveries": total_recoveries,
                "successful_recoveries": successful_recoveries,
                "success_rate": recovery_success_rate,
                "active_rules": len([r for r in self.recovery_rules if r.enabled])
            },
            "service_status": self.get_service_status(),
            "recent_recoveries": recent_recoveries[:10],
            "system_health": {
                "monitoring_enabled": self.enabled,
                "monitor_running": self.monitor_task is not None and not self.monitor_task.done()
            }
        }


# 全局故障恢复服务实例
fault_recovery_service = FaultRecoveryService()
"""
优雅降级服务
在系统部分功能故障时，提供降级策略以保证核心功能的可用性
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import threading
import functools

from ..services.error_logging_service import error_logging_service, ErrorCategory


class DegradationLevel(Enum):
    """降级级别"""
    NONE = "none"           # 无降级
    MINOR = "minor"         # 轻度降级
    MODERATE = "moderate"   # 中度降级
    SEVERE = "severe"       # 重度降级
    CRITICAL = "critical"   # 严重降级


class ServiceType(Enum):
    """服务类型"""
    ESSENTIAL = "essential"     # 核心服务
    IMPORTANT = "important"     # 重要服务
    OPTIONAL = "optional"       # 可选服务
    ENHANCEMENT = "enhancement" # 增强服务


@dataclass
class DegradationRule:
    """降级规则"""
    service_name: str
    service_type: ServiceType
    trigger_condition: str
    degradation_level: DegradationLevel
    fallback_action: str
    enabled: bool = True
    priority: int = 1
    auto_recovery: bool = True
    recovery_delay_seconds: int = 300  # 5分钟后尝试恢复


@dataclass
class ServiceStatus:
    """服务状态"""
    name: str
    service_type: ServiceType
    current_level: DegradationLevel
    is_degraded: bool = False
    degraded_since: Optional[datetime] = None
    last_check: Optional[datetime] = None
    error_count: int = 0
    response_time: float = 0.0
    success_rate: float = 1.0


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs):
        """调用函数并处理熔断逻辑"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """成功处理"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
    
    def _on_failure(self):
        """失败处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)


class FallbackHandler:
    """降级处理器"""
    
    def __init__(self):
        self.fallback_strategies = {}
        self.circuit_breakers = {}
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """注册降级策略"""
        self.fallback_strategies[service_name] = fallback_func
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """获取熔断器"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    async def execute_with_fallback(self, 
                                   service_name: str,
                                   primary_func: Callable,
                                   fallback_data: Any = None,
                                   *args, **kwargs) -> Dict[str, Any]:
        """执行主函数，失败时使用降级策略"""
        try:
            # 获取熔断器
            circuit_breaker = self.get_circuit_breaker(service_name)
            
            # 尝试执行主函数
            if asyncio.iscoroutinefunction(primary_func):
                result = await circuit_breaker.call(primary_func, *args, **kwargs)
            else:
                result = circuit_breaker.call(primary_func, *args, **kwargs)
            
            return {
                "success": True,
                "data": result,
                "degraded": False,
                "source": "primary"
            }
            
        except Exception as e:
            # 记录错误
            error_logging_service.log_warning(
                f"Service {service_name} failed, using fallback",
                ErrorCategory.BUSINESS_LOGIC
            )
            
            # 使用降级策略
            fallback_result = await self._execute_fallback(
                service_name, fallback_data, *args, **kwargs
            )
            
            return {
                "success": True,
                "data": fallback_result,
                "degraded": True,
                "source": "fallback",
                "error": str(e)
            }
    
    async def _execute_fallback(self, service_name: str, fallback_data: Any, *args, **kwargs):
        """执行降级策略"""
        if service_name in self.fallback_strategies:
            fallback_func = self.fallback_strategies[service_name]
            
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(fallback_data, *args, **kwargs)
                else:
                    return fallback_func(fallback_data, *args, **kwargs)
            except Exception as e:
                error_logging_service.log_error(
                    e, ErrorCategory.SYSTEM,
                    {"service": service_name, "fallback": True}
                )
                
        # 默认降级响应
        return self._get_default_fallback_response(service_name)
    
    def _get_default_fallback_response(self, service_name: str):
        """获取默认降级响应"""
        default_responses = {
            "experiments": {
                "experiments": [],
                "total": 0,
                "message": "实验列表服务暂时不可用，请稍后再试"
            },
            "analysis": {
                "results": {},
                "message": "分析服务暂时不可用，请稍后再试"
            },
            "recommendations": {
                "recommendations": [],
                "message": "推荐服务暂时不可用"
            },
            "notifications": {
                "message": "通知服务暂时不可用"
            }
        }
        
        return default_responses.get(service_name, {
            "message": f"服务 {service_name} 暂时不可用，请稍后再试"
        })


class GracefulDegradationService:
    """优雅降级服务"""
    
    def __init__(self):
        self.fallback_handler = FallbackHandler()
        self.service_statuses = {}
        self.degradation_rules = []
        self.degradation_history = defaultdict(list)
        self.monitoring_task = None
        self.enabled = True
        
        # 初始化默认规则和降级策略
        self._initialize_default_rules()
        self._register_default_fallbacks()
    
    def _initialize_default_rules(self):
        """初始化默认降级规则"""
        default_rules = [
            # 数据库相关降级
            DegradationRule(
                service_name="database",
                service_type=ServiceType.ESSENTIAL,
                trigger_condition="response_time > 5000 or error_rate > 0.1",
                degradation_level=DegradationLevel.MODERATE,
                fallback_action="use_cache"
            ),
            
            # 实验分析降级
            DegradationRule(
                service_name="analysis",
                service_type=ServiceType.IMPORTANT,
                trigger_condition="error_rate > 0.2 or response_time > 10000",
                degradation_level=DegradationLevel.MINOR,
                fallback_action="simplified_analysis"
            ),
            
            # 推荐服务降级
            DegradationRule(
                service_name="recommendations",
                service_type=ServiceType.OPTIONAL,
                trigger_condition="error_rate > 0.3",
                degradation_level=DegradationLevel.SEVERE,
                fallback_action="disable_recommendations"
            ),
            
            # 通知服务降级
            DegradationRule(
                service_name="notifications",
                service_type=ServiceType.ENHANCEMENT,
                trigger_condition="error_rate > 0.5",
                degradation_level=DegradationLevel.CRITICAL,
                fallback_action="disable_notifications"
            )
        ]
        
        self.degradation_rules.extend(default_rules)
    
    def _register_default_fallbacks(self):
        """注册默认降级策略"""
        
        # 实验列表降级策略
        async def experiments_fallback(fallback_data, *args, **kwargs):
            # 返回缓存的实验列表或空列表
            return {
                "experiments": fallback_data.get("cached_experiments", []) if fallback_data else [],
                "total": 0,
                "degraded": True,
                "message": "使用缓存数据，部分功能可能不可用"
            }
        
        # 分析服务降级策略
        async def analysis_fallback(fallback_data, *args, **kwargs):
            # 返回简化的分析结果
            return {
                "performance": {
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "annual_return": 0.0
                },
                "message": "提供简化分析结果",
                "degraded": True
            }
        
        # 推荐服务降级策略
        def recommendations_fallback(fallback_data, *args, **kwargs):
            return {
                "parameters": {},
                "suggestions": ["推荐服务暂时不可用"],
                "confidence": 0.0,
                "degraded": True
            }
        
        # 通知服务降级策略
        def notifications_fallback(fallback_data, *args, **kwargs):
            # 静默处理，不发送通知
            return {"sent": False, "degraded": True}
        
        # 注册降级策略
        self.fallback_handler.register_fallback("experiments", experiments_fallback)
        self.fallback_handler.register_fallback("analysis", analysis_fallback)
        self.fallback_handler.register_fallback("recommendations", recommendations_fallback)
        self.fallback_handler.register_fallback("notifications", notifications_fallback)
    
    async def start_monitoring(self):
        """启动降级监控"""
        if not self.monitoring_task:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """停止降级监控"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    async def _monitoring_loop(self):
        """监控循环"""
        while True:
            try:
                if self.enabled:
                    await self._check_service_health()
                    await self._apply_degradation_rules()
                    await self._attempt_recovery()
                
                # 每60秒检查一次
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_logging_service.log_error(
                    e, ErrorCategory.SYSTEM,
                    {"component": "graceful_degradation_monitor"}
                )
                await asyncio.sleep(60)
    
    async def _check_service_health(self):
        """检查服务健康状态"""
        services = ["database", "analysis", "recommendations", "notifications"]
        
        for service_name in services:
            try:
                # 获取服务健康状态（简化实现）
                health_data = await self._get_service_health_data(service_name)
                
                # 更新服务状态
                if service_name not in self.service_statuses:
                    self.service_statuses[service_name] = ServiceStatus(
                        name=service_name,
                        service_type=ServiceType.IMPORTANT,
                        current_level=DegradationLevel.NONE
                    )
                
                status = self.service_statuses[service_name]
                status.last_check = datetime.now()
                status.error_count = health_data.get("error_count", 0)
                status.response_time = health_data.get("response_time", 0)
                status.success_rate = health_data.get("success_rate", 1.0)
                
            except Exception as e:
                error_logging_service.log_error(
                    e, ErrorCategory.SYSTEM,
                    {"service": service_name, "component": "health_check"}
                )
    
    async def _get_service_health_data(self, service_name: str) -> Dict[str, Any]:
        """获取服务健康数据"""
        # 这里应该集成实际的健康检查逻辑
        # 简化实现，返回模拟数据
        
        import random
        return {
            "error_count": random.randint(0, 5),
            "response_time": random.randint(100, 2000),
            "success_rate": random.uniform(0.8, 1.0)
        }
    
    async def _apply_degradation_rules(self):
        """应用降级规则"""
        for rule in self.degradation_rules:
            if not rule.enabled:
                continue
            
            service_status = self.service_statuses.get(rule.service_name)
            if not service_status:
                continue
            
            # 评估降级条件
            should_degrade = self._evaluate_degradation_condition(rule, service_status)
            
            if should_degrade and not service_status.is_degraded:
                await self._apply_degradation(rule, service_status)
            elif not should_degrade and service_status.is_degraded:
                # 检查是否可以恢复
                if rule.auto_recovery:
                    await self._attempt_service_recovery(rule, service_status)
    
    def _evaluate_degradation_condition(self, rule: DegradationRule, status: ServiceStatus) -> bool:
        """评估降级条件"""
        try:
            # 创建评估上下文
            context = {
                "error_count": status.error_count,
                "response_time": status.response_time,
                "success_rate": status.success_rate,
                "error_rate": 1 - status.success_rate
            }
            
            # 简单的条件评估
            return eval(rule.trigger_condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            error_logging_service.log_warning(
                f"降级条件评估失败: {rule.trigger_condition}, 错误: {str(e)}",
                ErrorCategory.SYSTEM
            )
            return False
    
    async def _apply_degradation(self, rule: DegradationRule, status: ServiceStatus):
        """应用降级"""
        try:
            status.is_degraded = True
            status.degraded_since = datetime.now()
            status.current_level = rule.degradation_level
            
            # 记录降级历史
            self.degradation_history[rule.service_name].append({
                "timestamp": datetime.now(),
                "action": "degrade",
                "level": rule.degradation_level.value,
                "reason": rule.trigger_condition,
                "fallback_action": rule.fallback_action
            })
            
            # 限制历史记录数量
            if len(self.degradation_history[rule.service_name]) > 100:
                self.degradation_history[rule.service_name] = self.degradation_history[rule.service_name][-100:]
            
            error_logging_service.log_warning(
                f"服务 {rule.service_name} 已降级至 {rule.degradation_level.value} 级别",
                ErrorCategory.SYSTEM
            )
            
        except Exception as e:
            error_logging_service.log_error(
                e, ErrorCategory.SYSTEM,
                {"service": rule.service_name, "degradation_level": rule.degradation_level.value}
            )
    
    async def _attempt_recovery(self):
        """尝试恢复"""
        for service_name, status in self.service_statuses.items():
            if status.is_degraded and status.degraded_since:
                # 检查是否已经降级足够长时间
                elapsed = datetime.now() - status.degraded_since
                if elapsed.total_seconds() >= 300:  # 5分钟后尝试恢复
                    
                    # 找到对应的规则
                    rule = next((r for r in self.degradation_rules if r.service_name == service_name), None)
                    if rule and rule.auto_recovery:
                        await self._attempt_service_recovery(rule, status)
    
    async def _attempt_service_recovery(self, rule: DegradationRule, status: ServiceStatus):
        """尝试服务恢复"""
        try:
            # 检查服务是否已经恢复正常
            if not self._evaluate_degradation_condition(rule, status):
                status.is_degraded = False
                status.degraded_since = None
                status.current_level = DegradationLevel.NONE
                
                # 记录恢复历史
                self.degradation_history[rule.service_name].append({
                    "timestamp": datetime.now(),
                    "action": "recover",
                    "level": "none",
                    "reason": "auto_recovery"
                })
                
                error_logging_service.log_warning(
                    f"服务 {rule.service_name} 已自动恢复正常",
                    ErrorCategory.SYSTEM
                )
                
        except Exception as e:
            error_logging_service.log_error(
                e, ErrorCategory.SYSTEM,
                {"service": rule.service_name, "recovery": True}
            )
    
    def add_degradation_rule(self, rule: DegradationRule):
        """添加降级规则"""
        self.degradation_rules.append(rule)
    
    def remove_degradation_rule(self, service_name: str, degradation_level: DegradationLevel):
        """移除降级规则"""
        self.degradation_rules = [
            rule for rule in self.degradation_rules
            if not (rule.service_name == service_name and rule.degradation_level == degradation_level)
        ]
    
    async def execute_with_degradation(self, 
                                     service_name: str, 
                                     primary_func: Callable,
                                     fallback_data: Any = None,
                                     *args, **kwargs) -> Dict[str, Any]:
        """执行函数并处理降级"""
        return await self.fallback_handler.execute_with_fallback(
            service_name, primary_func, fallback_data, *args, **kwargs
        )
    
    def get_service_status(self, service_name: str = None) -> Dict[str, Any]:
        """获取服务状态"""
        if service_name:
            status = self.service_statuses.get(service_name)
            if status:
                data = asdict(status)
                if data['degraded_since']:
                    data['degraded_since'] = data['degraded_since'].isoformat()
                if data['last_check']:
                    data['last_check'] = data['last_check'].isoformat()
                return data
            return {"error": "Service not found"}
        
        result = {}
        for name, status in self.service_statuses.items():
            data = asdict(status)
            if data['degraded_since']:
                data['degraded_since'] = data['degraded_since'].isoformat()
            if data['last_check']:
                data['last_check'] = data['last_check'].isoformat()
            result[name] = data
        
        return result
    
    def get_degradation_history(self, service_name: str = None) -> Dict[str, Any]:
        """获取降级历史"""
        if service_name:
            return {
                "service": service_name,
                "history": [
                    {**record, "timestamp": record["timestamp"].isoformat()}
                    for record in self.degradation_history.get(service_name, [])
                ]
            }
        
        result = {}
        for name, history in self.degradation_history.items():
            result[name] = [
                {**record, "timestamp": record["timestamp"].isoformat()}
                for record in history
            ]
        
        return result
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取降级监控仪表盘数据"""
        # 统计降级状态
        total_services = len(self.service_statuses)
        degraded_services = sum(1 for status in self.service_statuses.values() if status.is_degraded)
        
        # 按降级级别统计
        level_counts = defaultdict(int)
        for status in self.service_statuses.values():
            if status.is_degraded:
                level_counts[status.current_level.value] += 1
        
        # 统计降级历史
        total_degradations = sum(len(history) for history in self.degradation_history.values())
        recent_degradations = []
        
        for service_name, history in self.degradation_history.items():
            for record in history[-5:]:  # 最近5条
                recent_degradations.append({
                    **record,
                    "service": service_name,
                    "timestamp": record["timestamp"].isoformat()
                })
        
        recent_degradations.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "overview": {
                "total_services": total_services,
                "healthy_services": total_services - degraded_services,
                "degraded_services": degraded_services,
                "degradation_rate": degraded_services / total_services if total_services > 0 else 0
            },
            "degradation_levels": dict(level_counts),
            "statistics": {
                "total_degradations": total_degradations,
                "active_rules": len([r for r in self.degradation_rules if r.enabled]),
                "auto_recovery_enabled": sum(1 for r in self.degradation_rules if r.auto_recovery)
            },
            "service_status": self.get_service_status(),
            "recent_degradations": recent_degradations[:10],
            "system_health": {
                "degradation_enabled": self.enabled,
                "monitoring_active": self.monitoring_task is not None and not self.monitoring_task.done()
            }
        }


# 降级装饰器
def with_degradation(service_name: str, fallback_data: Any = None):
    """降级装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await graceful_degradation_service.execute_with_degradation(
                service_name, func, fallback_data, *args, **kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            async def async_func():
                return func(*args, **kwargs)
            
            import asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                graceful_degradation_service.execute_with_degradation(
                    service_name, async_func, fallback_data
                )
            )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局降级服务实例
graceful_degradation_service = GracefulDegradationService()
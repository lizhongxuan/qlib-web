"""
应用性能监控 (APM) 服务
提供应用性能指标收集、分析和监控功能
"""
import time
import json
import asyncio
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import psutil
import threading
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db


@dataclass
class PerformanceMetric:
    """性能指标数据结构"""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str]
    unit: str = "ms"


@dataclass
class RequestMetric:
    """请求指标数据结构"""
    timestamp: datetime
    method: str
    endpoint: str
    status_code: int
    duration: float
    user_id: Optional[int] = None
    error: Optional[str] = None


@dataclass
class SystemMetric:
    """系统指标数据结构"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.performance_metrics: deque = deque(maxlen=max_history)
        self.request_metrics: deque = deque(maxlen=max_history)
        self.system_metrics: deque = deque(maxlen=max_history)
        self.active_requests: Dict[str, float] = {}
        self.error_counts: defaultdict = defaultdict(int)
        self.lock = threading.Lock()
    
    def record_performance_metric(self, metric: PerformanceMetric):
        """记录性能指标"""
        with self.lock:
            self.performance_metrics.append(metric)
    
    def record_request_metric(self, metric: RequestMetric):
        """记录请求指标"""
        with self.lock:
            self.request_metrics.append(metric)
            
            # 记录错误统计
            if metric.status_code >= 400:
                error_key = f"{metric.endpoint}:{metric.status_code}"
                self.error_counts[error_key] += 1
    
    def record_system_metric(self, metric: SystemMetric):
        """记录系统指标"""
        with self.lock:
            self.system_metrics.append(metric)
    
    def start_request(self, request_id: str) -> str:
        """开始请求计时"""
        with self.lock:
            self.active_requests[request_id] = time.time()
        return request_id
    
    def end_request(self, request_id: str) -> float:
        """结束请求计时"""
        with self.lock:
            start_time = self.active_requests.pop(request_id, None)
            if start_time:
                return (time.time() - start_time) * 1000  # 转换为毫秒
        return 0.0
    
    def get_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """获取性能摘要"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            # 过滤最近的指标
            recent_requests = [
                r for r in self.request_metrics 
                if r.timestamp >= cutoff_time
            ]
            recent_performance = [
                p for p in self.performance_metrics 
                if p.timestamp >= cutoff_time
            ]
            recent_system = [
                s for s in self.system_metrics 
                if s.timestamp >= cutoff_time
            ]
        
        if not recent_requests:
            return {"error": "没有足够的数据"}
        
        # 计算请求统计
        response_times = [r.duration for r in recent_requests]
        status_codes = [r.status_code for r in recent_requests]
        
        summary = {
            "time_range": f"最近{minutes}分钟",
            "total_requests": len(recent_requests),
            "response_time": {
                "avg": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
                "p99": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times),
                "min": min(response_times),
                "max": max(response_times)
            },
            "status_codes": {
                "2xx": sum(1 for code in status_codes if 200 <= code < 300),
                "4xx": sum(1 for code in status_codes if 400 <= code < 500),
                "5xx": sum(1 for code in status_codes if code >= 500),
            },
            "error_rate": sum(1 for code in status_codes if code >= 400) / len(status_codes),
            "rps": len(recent_requests) / (minutes * 60),  # requests per second
            "active_requests": len(self.active_requests)
        }
        
        # 添加系统指标
        if recent_system:
            latest_system = recent_system[-1]
            summary["system"] = {
                "cpu_percent": latest_system.cpu_percent,
                "memory_percent": latest_system.memory_percent,
                "disk_percent": latest_system.disk_percent,
                "process_count": latest_system.process_count
            }
        
        return summary


class APMService:
    """APM服务主类"""
    
    def __init__(self):
        self.collector = MetricsCollector()
        self.system_monitor_task = None
        self.alerts_enabled = True
        self.alert_thresholds = {
            "response_time_p95": 1000,  # 95分位响应时间阈值 (ms)
            "error_rate": 0.05,         # 错误率阈值 (5%)
            "cpu_percent": 80,          # CPU使用率阈值
            "memory_percent": 85,       # 内存使用率阈值
        }
    
    async def start(self):
        """启动APM服务"""
        if not self.system_monitor_task:
            self.system_monitor_task = asyncio.create_task(self._system_monitor_loop())
    
    async def stop(self):
        """停止APM服务"""
        if self.system_monitor_task:
            self.system_monitor_task.cancel()
            try:
                await self.system_monitor_task
            except asyncio.CancelledError:
                pass
            self.system_monitor_task = None
    
    @asynccontextmanager
    async def trace_request(self, method: str, endpoint: str, user_id: Optional[int] = None):
        """请求追踪上下文管理器"""
        request_id = f"{method}:{endpoint}:{time.time()}"
        self.collector.start_request(request_id)
        
        start_time = time.time()
        status_code = 200
        error = None
        
        try:
            yield
        except Exception as e:
            status_code = 500
            error = str(e)
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            
            metric = RequestMetric(
                timestamp=datetime.now(),
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
                user_id=user_id,
                error=error
            )
            
            self.collector.record_request_metric(metric)
            self.collector.end_request(request_id)
    
    def record_custom_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = "ms"):
        """记录自定义性能指标"""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            tags=tags or {},
            unit=unit
        )
        self.collector.record_performance_metric(metric)
    
    def record_database_query(self, query: str, duration: float, success: bool = True):
        """记录数据库查询性能"""
        tags = {
            "query_type": self._get_query_type(query),
            "success": str(success)
        }
        self.record_custom_metric("database_query", duration, tags)
    
    def record_external_api_call(self, api_name: str, duration: float, status_code: int):
        """记录外部API调用性能"""
        tags = {
            "api_name": api_name,
            "status_code": str(status_code)
        }
        self.record_custom_metric("external_api", duration, tags)
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """获取性能仪表盘数据"""
        summary = self.collector.get_performance_summary()
        
        # 获取Top慢接口
        with self.collector.lock:
            recent_requests = list(self.collector.request_metrics)[-100:]  # 最近100个请求
        
        endpoint_stats = defaultdict(list)
        for req in recent_requests:
            endpoint_stats[req.endpoint].append(req.duration)
        
        slow_endpoints = []
        for endpoint, durations in endpoint_stats.items():
            if durations:
                slow_endpoints.append({
                    "endpoint": endpoint,
                    "avg_duration": statistics.mean(durations),
                    "max_duration": max(durations),
                    "request_count": len(durations)
                })
        
        slow_endpoints.sort(key=lambda x: x["avg_duration"], reverse=True)
        
        return {
            **summary,
            "slow_endpoints": slow_endpoints[:10],
            "alerts": self._check_alerts(summary),
            "trends": self._calculate_trends()
        }
    
    def get_health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        try:
            # 检查系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 检查数据库连接
            db_healthy = self._check_database_health()
            
            # 检查关键服务
            services_healthy = self._check_services_health()
            
            health_status = "healthy"
            issues = []
            
            # 检查阈值
            if cpu_percent > self.alert_thresholds["cpu_percent"]:
                health_status = "warning"
                issues.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            
            if memory.percent > self.alert_thresholds["memory_percent"]:
                health_status = "warning"
                issues.append(f"内存使用率过高: {memory.percent:.1f}%")
            
            if not db_healthy:
                health_status = "critical"
                issues.append("数据库连接异常")
            
            if not services_healthy:
                health_status = "warning"
                issues.append("部分服务异常")
            
            return {
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "uptime": self._get_uptime()
                },
                "database": {"healthy": db_healthy},
                "services": {"healthy": services_healthy},
                "issues": issues
            }
        
        except Exception as e:
            return {
                "status": "critical",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "issues": ["健康检查执行失败"]
            }
    
    async def _system_monitor_loop(self):
        """系统监控循环"""
        while True:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                process_count = len(psutil.pids())
                
                metric = SystemMetric(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk.percent,
                    network_io={
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv
                    },
                    process_count=process_count
                )
                
                self.collector.record_system_metric(metric)
                
                # 等待30秒
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"系统监控错误: {e}")
                await asyncio.sleep(30)
    
    def _get_query_type(self, query: str) -> str:
        """获取SQL查询类型"""
        query = query.strip().upper()
        if query.startswith('SELECT'):
            return 'SELECT'
        elif query.startswith('INSERT'):
            return 'INSERT'
        elif query.startswith('UPDATE'):
            return 'UPDATE'
        elif query.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _check_database_health(self) -> bool:
        """检查数据库健康状态"""
        try:
            db = next(get_db())
            result = db.execute(text("SELECT 1"))
            return result.fetchone() is not None
        except Exception:
            return False
    
    def _check_services_health(self) -> bool:
        """检查关键服务健康状态"""
        # 这里可以添加对Redis、Celery等服务的健康检查
        return True
    
    def _get_uptime(self) -> float:
        """获取系统运行时间（秒）"""
        return time.time() - psutil.boot_time()
    
    def _check_alerts(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查告警条件"""
        alerts = []
        
        if not self.alerts_enabled:
            return alerts
        
        # 检查响应时间
        if summary.get("response_time", {}).get("p95", 0) > self.alert_thresholds["response_time_p95"]:
            alerts.append({
                "level": "warning",
                "type": "performance",
                "message": f"95分位响应时间过高: {summary['response_time']['p95']:.1f}ms",
                "timestamp": datetime.now().isoformat()
            })
        
        # 检查错误率
        if summary.get("error_rate", 0) > self.alert_thresholds["error_rate"]:
            alerts.append({
                "level": "critical",
                "type": "error_rate",
                "message": f"错误率过高: {summary['error_rate']*100:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # 检查系统资源
        system = summary.get("system", {})
        if system.get("cpu_percent", 0) > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "level": "warning",
                "type": "resource",
                "message": f"CPU使用率过高: {system['cpu_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        if system.get("memory_percent", 0) > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "level": "warning",
                "type": "resource",
                "message": f"内存使用率过高: {system['memory_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """计算性能趋势"""
        # 这里可以实现更复杂的趋势分析
        with self.collector.lock:
            recent_requests = list(self.collector.request_metrics)[-50:]
        
        if len(recent_requests) < 10:
            return {"insufficient_data": True}
        
        # 简单的趋势计算
        first_half = recent_requests[:len(recent_requests)//2]
        second_half = recent_requests[len(recent_requests)//2:]
        
        first_avg = statistics.mean([r.duration for r in first_half])
        second_avg = statistics.mean([r.duration for r in second_half])
        
        trend = "stable"
        if second_avg > first_avg * 1.2:
            trend = "degrading"
        elif second_avg < first_avg * 0.8:
            trend = "improving"
        
        return {
            "response_time_trend": trend,
            "trend_percentage": ((second_avg - first_avg) / first_avg) * 100
        }


# 全局APM实例
apm_service = APMService()
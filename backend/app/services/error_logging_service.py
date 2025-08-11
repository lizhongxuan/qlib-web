"""
错误日志收集服务
提供结构化的错误日志收集、存储和分析功能
"""
import json
import traceback
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import asyncio
import threading
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ErrorLevel(Enum):
    """错误级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误分类"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """错误记录数据结构"""
    timestamp: datetime
    level: ErrorLevel
    category: ErrorCategory
    message: str
    exception_type: str
    stack_trace: str
    request_id: Optional[str] = None
    user_id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    additional_context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['category'] = self.category.value
        return data


class ErrorStorage:
    """错误存储管理器"""
    
    def __init__(self, max_memory_records: int = 1000, log_file_path: Optional[str] = None):
        self.max_memory_records = max_memory_records
        self.memory_storage: deque = deque(maxlen=max_memory_records)
        self.error_counts: defaultdict = defaultdict(int)
        self.error_trends: defaultdict = defaultdict(list)
        self.lock = threading.Lock()
        
        # 文件存储
        self.log_file_path = log_file_path
        if log_file_path:
            self.log_file = Path(log_file_path)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置文件日志记录器
        self.file_logger = None
        if log_file_path:
            self.file_logger = logging.getLogger('error_collector')
            handler = logging.FileHandler(log_file_path, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)
            self.file_logger.setLevel(logging.ERROR)
    
    def store_error(self, error: ErrorRecord):
        """存储错误记录"""
        with self.lock:
            # 内存存储
            self.memory_storage.append(error)
            
            # 更新统计计数
            self._update_error_stats(error)
            
            # 文件存储
            if self.file_logger:
                error_data = error.to_dict()
                self.file_logger.error(json.dumps(error_data, ensure_ascii=False))
    
    def _update_error_stats(self, error: ErrorRecord):
        """更新错误统计"""
        # 按类别统计
        self.error_counts[f"category:{error.category.value}"] += 1
        
        # 按级别统计
        self.error_counts[f"level:{error.level.value}"] += 1
        
        # 按端点统计
        if error.endpoint:
            self.error_counts[f"endpoint:{error.endpoint}"] += 1
        
        # 按异常类型统计
        self.error_counts[f"exception:{error.exception_type}"] += 1
        
        # 记录趋势数据（按小时）
        hour_key = error.timestamp.strftime("%Y-%m-%d-%H")
        self.error_trends[hour_key].append({
            "timestamp": error.timestamp.isoformat(),
            "level": error.level.value,
            "category": error.category.value
        })
    
    def get_recent_errors(self, limit: int = 100, 
                         level: Optional[ErrorLevel] = None,
                         category: Optional[ErrorCategory] = None,
                         hours: int = 24) -> List[ErrorRecord]:
        """获取最近的错误记录"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            filtered_errors = []
            for error in reversed(self.memory_storage):
                if error.timestamp < cutoff_time:
                    continue
                
                if level and error.level != level:
                    continue
                
                if category and error.category != category:
                    continue
                
                filtered_errors.append(error)
                
                if len(filtered_errors) >= limit:
                    break
            
            return filtered_errors
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_errors = [
                error for error in self.memory_storage 
                if error.timestamp >= cutoff_time
            ]
            
            if not recent_errors:
                return {"total": 0, "by_level": {}, "by_category": {}, "by_endpoint": {}}
            
            # 按级别统计
            level_stats = defaultdict(int)
            for error in recent_errors:
                level_stats[error.level.value] += 1
            
            # 按类别统计
            category_stats = defaultdict(int)
            for error in recent_errors:
                category_stats[error.category.value] += 1
            
            # 按端点统计
            endpoint_stats = defaultdict(int)
            for error in recent_errors:
                if error.endpoint:
                    endpoint_stats[error.endpoint] += 1
            
            # 按异常类型统计
            exception_stats = defaultdict(int)
            for error in recent_errors:
                exception_stats[error.exception_type] += 1
            
            return {
                "total": len(recent_errors),
                "time_range": f"最近{hours}小时",
                "by_level": dict(level_stats),
                "by_category": dict(category_stats),
                "by_endpoint": dict(list(endpoint_stats.items())[:10]),  # Top 10
                "by_exception_type": dict(list(exception_stats.items())[:10]),  # Top 10
                "error_rate": len(recent_errors) / hours  # 每小时错误数
            }
    
    def get_error_trends(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误趋势"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            # 按小时分组
            hourly_errors = defaultdict(int)
            hourly_by_level = defaultdict(lambda: defaultdict(int))
            
            for error in self.memory_storage:
                if error.timestamp < cutoff_time:
                    continue
                
                hour_key = error.timestamp.strftime("%Y-%m-%d %H:00")
                hourly_errors[hour_key] += 1
                hourly_by_level[hour_key][error.level.value] += 1
            
            # 生成时间序列
            timeline = []
            current_time = cutoff_time.replace(minute=0, second=0, microsecond=0)
            end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
            
            while current_time <= end_time:
                hour_key = current_time.strftime("%Y-%m-%d %H:00")
                timeline.append({
                    "hour": hour_key,
                    "total": hourly_errors.get(hour_key, 0),
                    "by_level": dict(hourly_by_level.get(hour_key, {}))
                })
                current_time += timedelta(hours=1)
            
            return {
                "timeline": timeline,
                "summary": {
                    "total_hours": len(timeline),
                    "peak_hour": max(timeline, key=lambda x: x["total"]) if timeline else None,
                    "avg_per_hour": sum(h["total"] for h in timeline) / len(timeline) if timeline else 0
                }
            }


class ErrorCollector:
    """错误收集器主类"""
    
    def __init__(self, storage: ErrorStorage):
        self.storage = storage
        self.enabled = True
        
    def collect_error(self, 
                     exception: Exception,
                     level: ErrorLevel = ErrorLevel.ERROR,
                     category: ErrorCategory = ErrorCategory.UNKNOWN,
                     request_context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """收集错误"""
        if not self.enabled:
            return None
        
        # 提取异常信息
        exc_type = type(exception).__name__
        exc_message = str(exception)
        stack_trace = traceback.format_exception(type(exception), exception, exception.__traceback__)
        stack_trace_str = ''.join(stack_trace)
        
        # 创建错误记录
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=exc_message,
            exception_type=exc_type,
            stack_trace=stack_trace_str,
            request_id=request_context.get('request_id') if request_context else None,
            user_id=request_context.get('user_id') if request_context else None,
            endpoint=request_context.get('endpoint') if request_context else None,
            method=request_context.get('method') if request_context else None,
            user_agent=request_context.get('user_agent') if request_context else None,
            ip_address=request_context.get('ip_address') if request_context else None,
            additional_context=request_context.get('additional_context') if request_context else {}
        )
        
        # 存储错误
        self.storage.store_error(error_record)
        
        return error_record
    
    def collect_custom_error(self,
                            message: str,
                            level: ErrorLevel = ErrorLevel.ERROR,
                            category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
                            request_context: Optional[Dict[str, Any]] = None,
                            additional_context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """收集自定义错误"""
        if not self.enabled:
            return None
        
        # 获取调用栈
        stack_trace = ''.join(traceback.format_stack())
        
        # 创建错误记录
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            exception_type="CustomError",
            stack_trace=stack_trace,
            request_id=request_context.get('request_id') if request_context else None,
            user_id=request_context.get('user_id') if request_context else None,
            endpoint=request_context.get('endpoint') if request_context else None,
            method=request_context.get('method') if request_context else None,
            user_agent=request_context.get('user_agent') if request_context else None,
            ip_address=request_context.get('ip_address') if request_context else None,
            additional_context=additional_context or {}
        )
        
        # 存储错误
        self.storage.store_error(error_record)
        
        return error_record
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取错误监控仪表盘数据"""
        stats_24h = self.storage.get_error_statistics(hours=24)
        stats_1h = self.storage.get_error_statistics(hours=1)
        trends = self.storage.get_error_trends(hours=24)
        recent_errors = self.storage.get_recent_errors(limit=20)
        
        return {
            "current_stats": {
                "last_24h": stats_24h,
                "last_1h": stats_1h
            },
            "trends": trends,
            "recent_errors": [error.to_dict() for error in recent_errors],
            "health_indicators": {
                "error_rate_24h": stats_24h.get("error_rate", 0),
                "critical_errors_24h": stats_24h.get("by_level", {}).get("critical", 0),
                "top_error_endpoint": max(
                    stats_24h.get("by_endpoint", {}).items(), 
                    key=lambda x: x[1], 
                    default=("无", 0)
                )[0],
                "most_common_exception": max(
                    stats_24h.get("by_exception_type", {}).items(),
                    key=lambda x: x[1],
                    default=("无", 0)
                )[0]
            }
        }


class ErrorLoggingService:
    """错误日志服务"""
    
    def __init__(self, log_directory: str = "/tmp/qlib-web-logs"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # 创建存储和收集器
        log_file = self.log_directory / "error.log"
        self.storage = ErrorStorage(
            max_memory_records=5000,
            log_file_path=str(log_file)
        )
        self.collector = ErrorCollector(self.storage)
        
        # 异常处理器
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_handler
    
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """全局异常处理器"""
        if issubclass(exc_type, KeyboardInterrupt):
            self._original_excepthook(exc_type, exc_value, exc_traceback)
            return
        
        # 收集未捕获的异常
        self.collector.collect_error(
            exc_value,
            level=ErrorLevel.CRITICAL,
            category=ErrorCategory.SYSTEM
        )
        
        # 调用原始异常处理器
        self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def log_error(self, exception: Exception, 
                  category: ErrorCategory = ErrorCategory.UNKNOWN,
                  request_context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """记录错误"""
        return self.collector.collect_error(
            exception, 
            level=ErrorLevel.ERROR,
            category=category,
            request_context=request_context
        )
    
    def log_warning(self, message: str, 
                   category: ErrorCategory = ErrorCategory.UNKNOWN,
                   request_context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """记录警告"""
        return self.collector.collect_custom_error(
            message,
            level=ErrorLevel.WARNING,
            category=category,
            request_context=request_context
        )
    
    def log_critical(self, exception: Exception,
                    category: ErrorCategory = ErrorCategory.SYSTEM,
                    request_context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
        """记录严重错误"""
        return self.collector.collect_error(
            exception,
            level=ErrorLevel.CRITICAL, 
            category=category,
            request_context=request_context
        )
    
    def get_error_dashboard(self) -> Dict[str, Any]:
        """获取错误监控仪表盘"""
        return self.collector.get_dashboard_data()
    
    def get_recent_errors(self, **kwargs) -> List[Dict[str, Any]]:
        """获取最近错误"""
        errors = self.storage.get_recent_errors(**kwargs)
        return [error.to_dict() for error in errors]
    
    def get_error_statistics(self, **kwargs) -> Dict[str, Any]:
        """获取错误统计"""
        return self.storage.get_error_statistics(**kwargs)
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for log_file in self.log_directory.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    print(f"已删除旧日志文件: {log_file}")
                    
        except Exception as e:
            print(f"清理日志文件失败: {e}")


# 全局错误日志服务实例
error_logging_service = ErrorLoggingService()
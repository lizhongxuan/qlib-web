"""
APM中间件
自动追踪HTTP请求性能和错误
"""
import time
import uuid
from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from ..services.apm_service import apm_service


class APMMiddleware(BaseHTTPMiddleware):
    """APM性能监控中间件"""
    
    def __init__(self, app: FastAPI, exclude_paths: Optional[list] = None):
        super().__init__(app)
        # 排除不需要监控的路径
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/health"  # 健康检查本身不需要监控
        ]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求和响应"""
        
        # 检查是否需要排除此路径
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 开始追踪
        start_time = time.time()
        status_code = 200
        error = None
        user_id = None
        
        try:
            # 尝试获取用户ID（如果已认证）
            user_id = getattr(request.state, 'current_user_id', None)
            
            # 使用APM服务追踪请求
            async with apm_service.trace_request(
                method=request.method,
                endpoint=self._get_route_pattern(request),
                user_id=user_id
            ):
                response = await call_next(request)
                status_code = response.status_code
                
                # 添加追踪头
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = str((time.time() - start_time) * 1000)
                
                return response
                
        except Exception as e:
            status_code = 500
            error = str(e)
            
            # 记录错误指标
            apm_service.record_custom_metric(
                "request_error",
                1,
                {
                    "endpoint": self._get_route_pattern(request),
                    "method": request.method,
                    "error_type": type(e).__name__,
                    "status_code": str(status_code)
                },
                unit="count"
            )
            
            raise
    
    def _should_exclude_path(self, path: str) -> bool:
        """判断是否应该排除此路径"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    def _get_route_pattern(self, request: Request) -> str:
        """获取路由模式"""
        # 尝试获取路由模式，如果失败则返回原始路径
        try:
            route = request.scope.get("route")
            if route and hasattr(route, "path"):
                return route.path
            return request.url.path
        except Exception:
            return request.url.path


class DatabaseQueryMiddleware:
    """数据库查询监控中间件"""
    
    def __init__(self):
        self.enabled = True
    
    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """查询执行前的钩子"""
        if self.enabled:
            context._query_start_time = time.time()
    
    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """查询执行后的钩子"""
        if self.enabled and hasattr(context, '_query_start_time'):
            duration = (time.time() - context._query_start_time) * 1000
            
            # 记录查询性能
            apm_service.record_database_query(
                query=statement,
                duration=duration,
                success=True
            )
    
    def handle_error(self, exception_context):
        """处理查询错误"""
        if self.enabled:
            statement = exception_context.statement or "unknown"
            
            # 记录查询错误
            apm_service.record_database_query(
                query=statement,
                duration=0,
                success=False
            )


class ExternalAPIMiddleware:
    """外部API调用监控装饰器"""
    
    @staticmethod
    def track_api_call(api_name: str):
        """外部API调用追踪装饰器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status_code = 200
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # 如果返回结果中包含状态码，提取它
                    if hasattr(result, 'status_code'):
                        status_code = result.status_code
                    elif isinstance(result, dict) and 'status_code' in result:
                        status_code = result['status_code']
                    
                    return result
                    
                except Exception as e:
                    status_code = 500
                    raise
                    
                finally:
                    duration = (time.time() - start_time) * 1000
                    apm_service.record_external_api_call(api_name, duration, status_code)
            
            return wrapper
        return decorator


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self, name: str, tags: dict = None):
        self.name = name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (time.time() - self.start_time) * 1000
            
            # 添加错误标签
            if exc_type:
                self.tags["error"] = True
                self.tags["error_type"] = exc_type.__name__
            else:
                self.tags["error"] = False
            
            apm_service.record_custom_metric(
                self.name,
                duration,
                self.tags
            )


# 辅助函数
def profile_function(name: str, tags: dict = None):
    """函数性能分析装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with PerformanceProfiler(name, tags):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with PerformanceProfiler(name, tags):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_user_action(action: str, tags: dict = None):
    """用户行为追踪装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录用户行为
                duration = (time.time() - start_time) * 1000
                action_tags = {"action": action, "success": True}
                if tags:
                    action_tags.update(tags)
                
                apm_service.record_custom_metric(
                    "user_action",
                    duration,
                    action_tags
                )
                
                return result
                
            except Exception as e:
                # 记录失败的用户行为
                duration = (time.time() - start_time) * 1000
                action_tags = {
                    "action": action, 
                    "success": False, 
                    "error": type(e).__name__
                }
                if tags:
                    action_tags.update(tags)
                
                apm_service.record_custom_metric(
                    "user_action",
                    duration,
                    action_tags
                )
                
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录用户行为
                duration = (time.time() - start_time) * 1000
                action_tags = {"action": action, "success": True}
                if tags:
                    action_tags.update(tags)
                
                apm_service.record_custom_metric(
                    "user_action",
                    duration,
                    action_tags
                )
                
                return result
                
            except Exception as e:
                # 记录失败的用户行为
                duration = (time.time() - start_time) * 1000
                action_tags = {
                    "action": action, 
                    "success": False, 
                    "error": type(e).__name__
                }
                if tags:
                    action_tags.update(tags)
                
                apm_service.record_custom_metric(
                    "user_action",
                    duration,
                    action_tags
                )
                
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局中间件实例
database_middleware = DatabaseQueryMiddleware()
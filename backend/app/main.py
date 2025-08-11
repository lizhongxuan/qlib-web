from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.utils.qlib_manager import QlibManager
from app.middleware.apm_middleware import APMMiddleware
from app.middleware.security_middleware import SecurityMiddleware
from app.services.apm_service import apm_service
from app.services.error_logging_service import error_logging_service, ErrorCategory
from app.services.user_analytics_service import user_analytics_service, ActionType
from app.services.fault_recovery_service import fault_recovery_service
from app.services.graceful_degradation_service import graceful_degradation_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库
    logger.info("Initializing database...")
    init_db()
    
    # 启动APM服务
    logger.info("Starting APM service...")
    await apm_service.start()
    logger.success("APM service started successfully")
    
    # 启动故障恢复服务
    logger.info("Starting fault recovery service...")
    await fault_recovery_service.start_monitoring()
    logger.success("Fault recovery service started successfully")
    
    # 启动优雅降级服务
    logger.info("Starting graceful degradation service...")
    await graceful_degradation_service.start_monitoring()
    logger.success("Graceful degradation service started successfully")
    
    # 初始化Qlib
    logger.info("Initializing Qlib...")
    qlib_manager = QlibManager()
    try:
        qlib_manager.init_qlib()
        logger.success("Qlib initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Qlib: {e}")
    
    logger.success("Application startup complete")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down APM service...")
    await apm_service.stop()
    
    logger.info("Shutting down fault recovery service...")
    await fault_recovery_service.stop_monitoring()
    
    logger.info("Shutting down graceful degradation service...")
    await graceful_degradation_service.stop_monitoring()
    
    logger.info("Application shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Qlib量化投资Web平台后端API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# 添加可信主机中间件（生产环境）
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "*.qlib.ai"]
    )

# 添加APM监控中间件
app.add_middleware(APMMiddleware)

# 添加安全中间件
app.add_middleware(SecurityMiddleware)


# 请求ID和用户行为追踪中间件
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """为每个请求添加唯一ID并追踪用户行为"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # 追踪用户行为（如果是认证用户）
    user_id = getattr(request.state, 'current_user_id', None)
    if user_id and not request.url.path.startswith('/apm') and not request.url.path.startswith('/errors'):
        request_info = {
            'user_agent': request.headers.get('user-agent'),
            'ip_address': request.client.host if request.client else None,
            'request_id': request_id
        }
        
        # 根据路径判断行为类型
        action_type = ActionType.VIEW_PAGE
        if request.method == 'POST' and '/experiments' in request.url.path:
            action_type = ActionType.CREATE_EXPERIMENT
        elif request.method == 'DELETE':
            action_type = ActionType.DELETE_EXPERIMENT
        elif '/share' in request.url.path:
            action_type = ActionType.SHARE_EXPERIMENT
        elif '/download' in request.url.path:
            action_type = ActionType.DOWNLOAD_RESULT
        
        user_analytics_service.track_action(
            user_id=user_id,
            action_type=action_type,
            page=request.url.path,
            duration=process_time * 1000,  # 转换为毫秒
            request_info=request_info
        )
    
    # 记录请求日志
    logger.info(
        f"Request completed: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s "
        f"ID: {request_id}"
    )
    
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # 收集错误信息
    request_context = {
        "request_id": request_id,
        "endpoint": request.url.path,
        "method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else None
    }
    
    # 记录到错误日志服务
    error_logging_service.log_error(
        exception=exc,
        category=ErrorCategory.SYSTEM,
        request_context=request_context
    )
    
    logger.error(f"Unhandled exception in request {request_id}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "request_id": request_id
        }
    )


# 根路径
@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "success": True,
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": f"{settings.API_V1_PREFIX}/docs"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    health_data = apm_service.get_health_check()
    return health_data

# APM性能仪表盘
@app.get("/apm/dashboard")
async def apm_dashboard():
    """APM性能仪表盘"""
    return apm_service.get_performance_dashboard()

# 错误监控仪表盘
@app.get("/errors/dashboard")
async def error_dashboard():
    """错误监控仪表盘"""
    return error_logging_service.get_error_dashboard()

# 获取最近错误
@app.get("/errors/recent")
async def recent_errors(limit: int = 50, hours: int = 24):
    """获取最近错误"""
    return {
        "errors": error_logging_service.get_recent_errors(limit=limit, hours=hours)
    }

# 获取错误统计
@app.get("/errors/statistics")
async def error_statistics(hours: int = 24):
    """获取错误统计"""
    return error_logging_service.get_error_statistics(hours=hours)

# 用户行为分析仪表盘
@app.get("/analytics/dashboard")
async def analytics_dashboard(hours: int = 24):
    """用户行为分析仪表盘"""
    return user_analytics_service.get_platform_analytics(hours=hours)

# 获取用户行为洞察
@app.get("/analytics/user/{user_id}/insights")
async def user_insights(user_id: int):
    """获取特定用户的行为洞察"""
    return user_analytics_service.get_user_insights(user_id)

# 获取用户分群分析
@app.get("/analytics/user-segmentation")
async def user_segmentation():
    """获取用户分群分析"""
    return user_analytics_service.get_user_segmentation()

# 故障恢复仪表盘
@app.get("/fault-recovery/dashboard")
async def fault_recovery_dashboard():
    """故障恢复仪表盘"""
    return fault_recovery_service.get_dashboard_data()

# 获取服务状态
@app.get("/fault-recovery/services")
async def service_status(service_name: str = None):
    """获取服务状态"""
    return fault_recovery_service.get_service_status(service_name)

# 获取恢复历史
@app.get("/fault-recovery/history")
async def recovery_history(service_name: str = None):
    """获取恢复历史"""
    return fault_recovery_service.get_recovery_history(service_name)

# 优雅降级仪表盘
@app.get("/degradation/dashboard")
async def degradation_dashboard():
    """优雅降级仪表盘"""
    return graceful_degradation_service.get_dashboard_data()

# 获取服务降级状态
@app.get("/degradation/services")
async def degradation_service_status(service_name: str = None):
    """获取服务降级状态"""
    return graceful_degradation_service.get_service_status(service_name)

# 获取降级历史
@app.get("/degradation/history")
async def degradation_history(service_name: str = None):
    """获取降级历史"""
    return graceful_degradation_service.get_degradation_history(service_name)


# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on http://localhost:8000")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
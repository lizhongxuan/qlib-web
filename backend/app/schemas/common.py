from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel

DataType = TypeVar("DataType")


class APIResponse(BaseModel, Generic[DataType]):
    """统一API响应格式"""
    success: bool = True
    data: Optional[DataType] = None
    message: Optional[str] = None
    error_code: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[DataType]):
    """分页响应格式"""
    items: List[DataType]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int


class DashboardSummary(BaseModel):
    """仪表盘统计摘要"""
    total_experiments: int = 0
    running_experiments: int = 0
    completed_experiments: int = 0
    failed_experiments: int = 0
    pending_experiments: int = 0
    
    # 最近实验
    recent_experiments: List[Dict[str, Any]] = []
    
    # 系统状态
    system_status: Dict[str, Any] = {
        "cpu_usage": 0.0,
        "memory_usage": 0.0,
        "disk_usage": 0.0,
        "queue_size": 0
    }


class ConfigOptions(BaseModel):
    """配置选项响应"""
    stock_pools: List[str] = []
    models: List[str] = []
    strategies: List[str] = []


class ModelParams(BaseModel):
    """模型参数配置"""
    params: Dict[str, Dict[str, Any]] = {}


class HealthCheck(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    timestamp: str
    version: str
    uptime: float
    database: str = "connected"
    redis: str = "connected"
    qlib: str = "initialized"
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re


class DataConfigBase(BaseModel):
    """数据配置基类"""
    stock_pool: str = Field(..., description="股票池", min_length=1, max_length=50)
    start_time: str = Field(..., description="开始时间", pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_time: str = Field(..., description="结束时间", pattern=r"^\d{4}-\d{2}-\d{2}$")
    
    @validator("stock_pool")
    def validate_stock_pool(cls, v):
        allowed_pools = ["CSI300", "CSI500", "CSI800", "CSI1000", "SSE50", "SZSE100", "ChiNext"]
        if v not in allowed_pools:
            raise ValueError(f"股票池必须是以下之一: {', '.join(allowed_pools)}")
        return v
    
    @validator("end_time")
    def validate_date_range(cls, v, values):
        if "start_time" in values:
            start_date = datetime.strptime(values["start_time"], "%Y-%m-%d")
            end_date = datetime.strptime(v, "%Y-%m-%d")
            if end_date <= start_date:
                raise ValueError("结束时间必须大于开始时间")
            if (end_date - start_date).days > 3650:  # 最多10年
                raise ValueError("时间范围不能超过10年")
        return v


class ModelConfigBase(BaseModel):
    """模型配置基类"""
    name: str = Field(..., description="模型名称", min_length=1, max_length=50)
    params: Dict[str, Any] = Field(default_factory=dict, description="模型参数")
    
    @validator("name")
    def validate_model_name(cls, v):
        allowed_models = ["LightGBM", "XGBoost", "CatBoost", "LSTM", "GRU", "Transformer", "Linear", "Ridge", "Lasso"]
        if v not in allowed_models:
            raise ValueError(f"模型必须是以下之一: {', '.join(allowed_models)}")
        return v
    
    @validator("params")
    def validate_params_size(cls, v):
        if len(str(v)) > 10000:  # 限制参数大小
            raise ValueError("模型参数过大")
        return v


class StrategyConfigBase(BaseModel):
    """策略配置基类"""
    name: str = Field(..., description="策略名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="策略参数")


class BacktestConfigBase(BaseModel):
    """回测配置基类"""
    trade_cost: float = Field(0.0015, description="交易费用", ge=0, le=0.1)
    benchmark: Optional[str] = Field("CSI300", description="基准指数")
    initial_cash: float = Field(1000000, description="初始资金", gt=0)


class ExperimentConfigBase(BaseModel):
    """实验配置基类"""
    data_config: DataConfigBase
    ml_model_config: ModelConfigBase
    strategy_config: StrategyConfigBase
    backtest_config: BacktestConfigBase = Field(default_factory=BacktestConfigBase)


class ExperimentCreate(BaseModel):
    """创建实验请求"""
    name: str = Field(..., min_length=1, max_length=200, description="实验名称")
    description: Optional[str] = Field(None, max_length=1000, description="实验描述")
    config: ExperimentConfigBase = Field(..., description="实验配置")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    
    @validator("name")
    def validate_experiment_name(cls, v):
        # 检查是否包含特殊字符
        if not re.match(r"^[a-zA-Z0-9\u4e00-\u9fa5_\-\s]+$", v):
            raise ValueError("实验名称只能包含字母、数字、中文、下划线、连字符和空格")
        # 检查是否以空格开始或结束
        if v.strip() != v:
            raise ValueError("实验名称不能以空格开始或结束")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError("标签数量不能超过10个")
        for tag in v or []:
            if not isinstance(tag, str) or len(tag) > 50:
                raise ValueError("标签必须是字符串且长度不超过50")
        return v


class ExperimentUpdate(BaseModel):
    """更新实验请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="实验名称")
    description: Optional[str] = Field(None, max_length=1000, description="实验描述")
    config: Optional[ExperimentConfigBase] = Field(None, description="实验配置")
    tags: Optional[List[str]] = Field(None, description="标签")
    is_favorite: Optional[bool] = Field(None, description="是否收藏")


class PerformanceMetrics(BaseModel):
    """性能指标"""
    total_return: Optional[float] = Field(None, description="总收益率")
    annual_return: Optional[float] = Field(None, description="年化收益率")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")
    volatility: Optional[float] = Field(None, description="波动率")
    win_rate: Optional[float] = Field(None, description="胜率")
    profit_loss_ratio: Optional[float] = Field(None, description="盈亏比")


class ExperimentResults(BaseModel):
    """实验结果"""
    performance: Optional[PerformanceMetrics] = None
    positions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="持仓数据")
    trades: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="交易记录")
    benchmark_performance: Optional[Dict[str, float]] = Field(default_factory=dict, description="基准性能")


class ExperimentSummary(BaseModel):
    """实验摘要（用于列表展示）"""
    id: str
    name: str
    status: str
    progress: int = Field(ge=0, le=100)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    is_favorite: bool = False
    tags: Optional[List[str]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ExperimentResponse(BaseModel):
    """实验详细响应"""
    id: str
    name: str
    description: Optional[str] = None
    config: ExperimentConfigBase
    status: str
    progress: int = Field(ge=0, le=100)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[ExperimentResults] = None
    error_message: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    is_favorite: bool = False

    class Config:
        from_attributes = True


class ExperimentLogResponse(BaseModel):
    """实验日志响应"""
    experiment_id: str
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    total_lines: int = 0
    last_updated: Optional[datetime] = None


class ExperimentStatsResponse(BaseModel):
    """实验统计响应"""
    experiment_id: str
    runtime_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    data_points_processed: Optional[int] = None
    model_accuracy: Optional[float] = None
    prediction_count: Optional[int] = None
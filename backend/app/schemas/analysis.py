"""
分析相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..models.analysis import AnalysisType, AnalysisStatus


# 枚举类转换
class AnalysisTypeEnum(str, Enum):
    ATTRIBUTION = "attribution"
    RISK = "risk"
    SCENARIO_ANALYSIS = "scenario_analysis"
    MONTE_CARLO = "monte_carlo"
    SENSITIVITY_ANALYSIS = "sensitivity_analysis"
    FEATURE_IMPORTANCE = "feature_importance"
    MODEL_DIAGNOSIS = "model_diagnosis"
    CUSTOM_METRIC = "custom_metric"


class AnalysisStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# 分析任务相关
class AnalysisBase(BaseModel):
    """分析任务基础信息"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    analysis_type: AnalysisTypeEnum
    config: Dict[str, Any] = Field(default_factory=dict)


class AnalysisCreate(AnalysisBase):
    """创建分析任务"""
    experiment_id: str = Field(..., min_length=1)


class AnalysisUpdate(BaseModel):
    """更新分析任务"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AnalysisResponse(AnalysisBase):
    """分析任务响应"""
    id: int
    experiment_id: str
    creator_id: int
    status: AnalysisStatusEnum
    progress: int
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    """分析任务列表响应"""
    analyses: List[AnalysisResponse]
    total: int
    page: int
    size: int
    pages: int


# 归因分析相关
class AttributionConfig(BaseModel):
    """归因分析配置"""
    benchmark: str = Field(default="CSI300")
    attribution_method: str = Field(default="brinson")
    rebalance_frequency: str = Field(default="monthly")
    sector_classification: Optional[str] = "GICS"
    include_interaction: bool = Field(default=True)


class AttributionResult(BaseModel):
    """归因分析结果"""
    total_return: float
    benchmark_return: float
    active_return: float
    alpha: float
    beta: float
    tracking_error: float
    information_ratio: float
    sector_contribution: Dict[str, float]
    factor_exposure: Dict[str, float]
    attribution_summary: Dict[str, float]


# 风险分析相关
class RiskAnalysisConfig(BaseModel):
    """风险分析配置"""
    confidence_levels: List[float] = Field(default=[0.95, 0.99])
    risk_free_rate: float = Field(default=0.03)
    rolling_window: int = Field(default=252)
    include_stress_test: bool = Field(default=True)
    stress_scenarios: Optional[Dict[str, Dict[str, float]]] = None


class RiskAnalysisResult(BaseModel):
    """风险分析结果"""
    var_95: float
    var_99: float
    cvar_95: Optional[float] = None
    cvar_99: Optional[float] = None
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    correlation_with_benchmark: float
    risk_metrics_series: Optional[Dict[str, List[float]]] = None


# 特征重要性分析相关
class FeatureImportanceConfig(BaseModel):
    """特征重要性分析配置"""
    method: str = Field(default="shap", regex="^(shap|permutation|tree_importance)$")
    top_n_features: int = Field(default=20, ge=1, le=100)
    include_correlation: bool = Field(default=True)
    stability_analysis: bool = Field(default=True)


class FeatureImportanceResult(BaseModel):
    """特征重要性分析结果"""
    feature_importance: Dict[str, float]
    shap_values: Optional[Dict[str, List[float]]] = None
    top_features: List[Dict[str, Union[str, float]]]
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    feature_stability: Optional[float] = None


# IC分析相关
class ICAnalysisConfig(BaseModel):
    """IC分析配置"""
    window_size: int = Field(default=20, ge=5, le=252)
    decay_analysis: bool = Field(default=True)
    significance_test: bool = Field(default=True)
    rolling_analysis: bool = Field(default=True)


class ICAnalysisResult(BaseModel):
    """IC分析结果"""
    ic_series: List[float]
    ic_mean: float
    ic_std: float
    ic_ir: float
    positive_ic_ratio: float
    decay_rate: Optional[float] = None
    decay_significance: Optional[float] = None
    ic_distribution: Dict[str, float]


# 自定义指标相关
class CustomMetricBase(BaseModel):
    """自定义指标基础信息"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    formula: str = Field(..., min_length=1)
    formula_type: str = Field(default="python", regex="^(python|sql|javascript)$")
    variables: Optional[Dict[str, Any]] = None
    is_public: bool = Field(default=False)


class CustomMetricCreate(CustomMetricBase):
    """创建自定义指标"""
    pass


class CustomMetricUpdate(BaseModel):
    """更新自定义指标"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    formula: Optional[str] = Field(None, min_length=1)
    variables: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class CustomMetricResponse(CustomMetricBase):
    """自定义指标响应"""
    id: int
    creator_id: int
    is_active: bool
    usage_count: int
    rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomMetricListResponse(BaseModel):
    """自定义指标列表响应"""
    metrics: List[CustomMetricResponse]
    total: int
    page: int
    size: int
    pages: int


class MetricCalculationRequest(BaseModel):
    """指标计算请求"""
    metric_id: int
    experiment_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MetricCalculationResponse(BaseModel):
    """指标计算响应"""
    metric_id: int
    experiment_id: str
    result_value: float
    execution_time: Optional[float] = None
    parameters: Dict[str, Any]
    calculated_at: datetime


# 模型诊断相关
class ModelDiagnosticsConfig(BaseModel):
    """模型诊断配置"""
    include_accuracy: bool = Field(default=True)
    include_bias: bool = Field(default=True)
    include_stability: bool = Field(default=True)
    include_feature_importance: bool = Field(default=False)
    confidence_level: float = Field(default=0.95, ge=0.01, le=0.99)


class ModelDiagnosticsResult(BaseModel):
    """模型诊断结果"""
    accuracy_metrics: Dict[str, float]
    bias_analysis: Dict[str, float]
    distribution_analysis: Dict[str, Union[float, bool]]
    residual_analysis: Dict[str, Union[float, Dict[str, float]]]
    stability_score: float
    recommendations: Optional[List[str]] = None


class DiagnosticsResponse(BaseModel):
    """诊断响应"""
    id: int
    experiment_id: str
    diagnostic_type: str
    results: Dict[str, Any]
    summary: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    status: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 情景分析相关
class ScenarioConfig(BaseModel):
    """情景分析配置"""
    scenarios: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "base_case": {"market_shock": 0.0, "volatility_multiplier": 1.0},
            "bear_market": {"market_shock": -0.20, "volatility_multiplier": 1.5},
            "bull_market": {"market_shock": 0.15, "volatility_multiplier": 0.8},
            "high_volatility": {"market_shock": 0.0, "volatility_multiplier": 2.0}
        }
    )
    monte_carlo_runs: int = Field(default=1000, ge=100, le=10000)
    time_horizon_days: int = Field(default=252, ge=30, le=1000)


class ScenarioResult(BaseModel):
    """情景分析结果"""
    scenario_name: str
    adjusted_annual_return: float
    adjusted_volatility: float
    adjusted_sharpe: float
    adjusted_max_drawdown: float
    scenario_impact: Dict[str, float]


class ScenarioAnalysisResult(BaseModel):
    """情景分析完整结果"""
    scenarios: Dict[str, ScenarioResult]
    summary: Dict[str, Any]
    confidence_intervals: Optional[Dict[str, Dict[str, float]]] = None


# 蒙特卡洛模拟相关
class MonteCarloConfig(BaseModel):
    """蒙特卡洛模拟配置"""
    n_simulations: int = Field(default=10000, ge=1000, le=100000)
    time_horizon: int = Field(default=252, ge=30, le=1000)  # 交易日
    confidence_levels: List[float] = Field(default=[0.05, 0.95])
    random_seed: Optional[int] = None
    distribution_type: str = Field(default="normal")  # normal, t, historical


class MonteCarloResult(BaseModel):
    """蒙特卡洛模拟结果"""
    simulation_parameters: Dict[str, Any]
    return_distribution: Dict[str, float]
    confidence_intervals: Dict[str, Dict[str, float]]
    risk_metrics: Dict[str, float]
    scenario_probabilities: Dict[str, float]
    percentile_analysis: Dict[str, float]
    simulation_paths: Optional[List[List[float]]] = None  # 样本路径


# 敏感性分析相关
class SensitivityConfig(BaseModel):
    """敏感性分析配置"""
    base_parameters: Optional[Dict[str, float]] = None
    parameter_ranges: Optional[Dict[str, List[float]]] = None  # [min, max]
    analysis_parameters: List[str] = Field(default=["volatility", "mean_return", "correlation"])
    sensitivity_steps: int = Field(default=11, ge=5, le=21)


class ParameterSensitivity(BaseModel):
    """参数敏感性结果"""
    parameter_name: str
    base_value: float
    parameter_range: List[float]
    sensitivity_curve: List[Dict[str, float]]
    elasticity: Dict[str, float]
    risk_impact: float


class SensitivityAnalysisResult(BaseModel):
    """敏感性分析结果"""
    base_case_metrics: Dict[str, float]
    sensitivity_analysis: Dict[str, ParameterSensitivity]
    parameter_importance: List[Dict[str, Any]]
    stability_assessment: Dict[str, str]


# 增强归因分析配置
class EnhancedAttributionConfig(BaseModel):
    """增强归因分析配置"""
    benchmark: str = Field(default="CSI300")
    attribution_method: str = Field(default="brinson")
    include_industry_analysis: bool = Field(default=True)
    include_style_factors: bool = Field(default=True)
    include_stock_selection: bool = Field(default=True)
    rebalance_frequency: str = Field(default="monthly")
    sector_classification: str = Field(default="GICS")


class EnhancedAttributionResult(BaseModel):
    """增强归因分析结果"""
    portfolio_return: float
    benchmark_return: float
    active_return: float
    alpha: float
    beta: float
    tracking_error: float
    information_ratio: float
    industry_contribution: Dict[str, Dict[str, float]]
    style_factor_analysis: Dict[str, Dict[str, float]]
    stock_selection_effect: Dict[str, Any]
    attribution_summary: Dict[str, float]


# 高级风险分析配置
class AdvancedRiskConfig(BaseModel):
    """高级风险分析配置"""
    confidence_levels: List[float] = Field(default=[0.95, 0.99])
    risk_free_rate: float = Field(default=0.03)
    include_monte_carlo_var: bool = Field(default=True)
    include_correlation_analysis: bool = Field(default=True)
    include_stress_tests: bool = Field(default=True)
    include_tail_risk: bool = Field(default=True)
    include_liquidity_risk: bool = Field(default=True)
    monte_carlo_simulations: int = Field(default=10000)


class AdvancedRiskResult(BaseModel):
    """高级风险分析结果"""
    annual_return: float
    annual_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    monte_carlo_var: Dict[str, Any]
    correlation_analysis: Dict[str, Any]
    stress_tests: Dict[str, Dict[str, float]]
    tail_risk: Dict[str, Any]
    liquidity_risk: Dict[str, Any]


# API响应包装
class AnalysisApiResponse(BaseModel):
    """分析API响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Union[AnalysisResponse, Dict[str, Any]]] = None


class AnalysisExecutionRequest(BaseModel):
    """分析执行请求"""
    analysis_id: int
    async_execution: bool = Field(default=True)


class AnalysisExecutionResponse(BaseModel):
    """分析执行响应"""
    analysis_id: int
    status: AnalysisStatusEnum
    estimated_duration: Optional[int] = None  # 预估执行时间（秒）
    task_id: Optional[str] = None  # 异步任务ID


# 分析模板相关
class AnalysisTemplateBase(BaseModel):
    """分析模板基础信息"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    analysis_type: AnalysisTypeEnum
    category: Optional[str] = None
    config_template: Dict[str, Any]
    default_params: Optional[Dict[str, Any]] = None
    is_public: bool = Field(default=False)


class AnalysisTemplateCreate(AnalysisTemplateBase):
    """创建分析模板"""
    pass


class AnalysisTemplateResponse(AnalysisTemplateBase):
    """分析模板响应"""
    id: int
    creator_id: int
    is_active: bool
    usage_count: int
    rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisTemplateListResponse(BaseModel):
    """分析模板列表响应"""
    templates: List[AnalysisTemplateResponse]
    total: int
    page: int
    size: int
    pages: int


# 批量操作
class BatchAnalysisRequest(BaseModel):
    """批量分析请求"""
    experiment_ids: List[str]
    analysis_template_id: int
    custom_config: Optional[Dict[str, Any]] = None


class BatchAnalysisResponse(BaseModel):
    """批量分析响应"""
    created_analyses: List[int]  # 创建的分析任务ID列表
    failed_experiments: List[str]  # 失败的实验ID列表
    total_created: int
    total_failed: int


# 分析统计
class AnalysisStatistics(BaseModel):
    """分析统计"""
    total_analyses: int
    analyses_by_type: Dict[str, int]
    analyses_by_status: Dict[str, int]
    avg_execution_time: Optional[float] = None
    success_rate: float
    popular_templates: List[Dict[str, Union[str, int]]]
    recent_activity: List[Dict[str, Any]]
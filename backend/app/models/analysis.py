"""
高级分析相关数据库模型
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class AnalysisType(enum.Enum):
    """分析类型枚举"""
    ATTRIBUTION = "attribution"           # 归因分析
    RISK = "risk"                        # 风险分析
    SCENARIO = "scenario"                # 情景分析
    FEATURE_IMPORTANCE = "feature_importance"  # 特征重要性
    MODEL_DIAGNOSIS = "model_diagnosis"   # 模型诊断
    CUSTOM_METRIC = "custom_metric"       # 自定义指标


class AnalysisStatus(enum.Enum):
    """分析状态枚举"""
    PENDING = "pending"       # 等待中
    RUNNING = "running"       # 运行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


class AdvancedAnalysis(Base):
    """高级分析任务模型"""
    __tablename__ = "advanced_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 分析配置
    analysis_type = Column(String(30), nullable=False)  # 分析类型
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)  # 分析参数配置
    
    # 执行状态
    status = Column(String(20), default=AnalysisStatus.PENDING.value)
    progress = Column(Integer, default=0)  # 进度百分比
    
    # 结果数据
    results = Column(JSON, nullable=True)  # 分析结果
    error_message = Column(Text, nullable=True)  # 错误信息
    metrics = Column(JSON, nullable=True)  # 计算的指标
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    experiment = relationship("Experiment", back_populates="advanced_analyses")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<AdvancedAnalysis(id={self.id}, type='{self.analysis_type}', status='{self.status}')>"


class CustomMetric(Base):
    """自定义指标模型"""
    __tablename__ = "custom_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 指标定义
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # 指标分类
    
    # 计算公式
    formula = Column(Text, nullable=False)  # 计算公式
    formula_type = Column(String(20), default="python")  # 公式类型：python, sql等
    variables = Column(JSON, nullable=True)  # 变量定义
    
    # 指标属性
    is_public = Column(Boolean, default=False)  # 是否公开
    is_active = Column(Boolean, default=True)   # 是否启用
    usage_count = Column(Integer, default=0)    # 使用次数
    rating = Column(Float, nullable=True)       # 评分
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    creator = relationship("User")
    usages = relationship("MetricUsage", back_populates="metric", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CustomMetric(id={self.id}, name='{self.name}', creator_id={self.creator_id})>"


class MetricUsage(Base):
    """指标使用记录模型"""
    __tablename__ = "metric_usages"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("custom_metrics.id"), nullable=False)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 使用信息
    parameters = Column(JSON, nullable=True)  # 使用时的参数
    result_value = Column(Float, nullable=True)  # 计算结果值
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    
    # 时间信息
    used_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    metric = relationship("CustomMetric", back_populates="usages")
    experiment = relationship("Experiment")
    user = relationship("User")
    
    def __repr__(self):
        return f"<MetricUsage(id={self.id}, metric_id={self.metric_id}, value={self.result_value})>"


class AnalysisTemplate(Base):
    """分析模板模型"""
    __tablename__ = "analysis_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 模板信息
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    analysis_type = Column(String(30), nullable=False)
    category = Column(String(100), nullable=True)
    
    # 模板配置
    config_template = Column(JSON, nullable=False)  # 配置模板
    default_params = Column(JSON, nullable=True)    # 默认参数
    required_fields = Column(JSON, nullable=True)   # 必填字段
    
    # 模板属性
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    creator = relationship("User")
    
    def __repr__(self):
        return f"<AnalysisTemplate(id={self.id}, name='{self.name}', type='{self.analysis_type}')>"


class ModelDiagnostics(Base):
    """模型诊断结果模型"""
    __tablename__ = "model_diagnostics"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("advanced_analyses.id"), nullable=True)
    
    # 诊断类型
    diagnostic_type = Column(String(50), nullable=False)  # ic_decay, feature_importance, stability等
    
    # 诊断结果
    results = Column(JSON, nullable=False)  # 详细结果数据
    summary = Column(JSON, nullable=True)   # 结果摘要
    recommendations = Column(JSON, nullable=True)  # 建议
    
    # 诊断指标
    score = Column(Float, nullable=True)    # 整体评分
    status = Column(String(20), nullable=True)  # 状态：good, warning, critical
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    experiment = relationship("Experiment")
    analysis = relationship("AdvancedAnalysis")
    
    def __repr__(self):
        return f"<ModelDiagnostics(id={self.id}, type='{self.diagnostic_type}', score={self.score})>"


# 更新实验模型关系
def update_experiment_analysis_relationship():
    """更新实验模型的分析关系"""
    from .experiment import Experiment
    
    # 添加分析关系
    Experiment.advanced_analyses = relationship(
        "AdvancedAnalysis", 
        back_populates="experiment", 
        cascade="all, delete-orphan"
    )


# 调用函数更新关系
update_experiment_analysis_relationship()
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import TABLE_PREFIX


class Experiment(Base):
    """实验模型"""
    __tablename__ = f"{TABLE_PREFIX}experiments"
    
    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 用户关联
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 暂时允许为空以兼容现有数据
    
    # 配置信息
    config = Column(JSON, nullable=False)  # 完整的实验配置
    
    # 状态信息
    status = Column(String(20), default="pending", index=True)
    progress = Column(Integer, default=0)  # 进度百分比
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 结果数据
    results = Column(JSON, nullable=True)  # 实验结果
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 文件路径
    result_file_path = Column(String(500), nullable=True)
    log_file_path = Column(String(500), nullable=True)
    
    # 性能指标
    total_return = Column(Float, nullable=True)
    annual_return = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    
    # 元数据
    tags = Column(JSON, nullable=True)  # 标签
    is_favorite = Column(Boolean, default=False)  # 是否收藏
    is_deleted = Column(Boolean, default=False)  # 软删除标记
    
    # 关系
    creator = relationship("User", back_populates="experiments")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": self.results,
            "error_message": self.error_message,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "tags": self.tags,
            "is_favorite": self.is_favorite,
        }
    
    def to_summary_dict(self):
        """转换为摘要字典（用于列表展示）"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "is_favorite": self.is_favorite,
        }
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import TABLE_PREFIX


class Task(Base):
    """异步任务模型"""
    __tablename__ = f"{TABLE_PREFIX}tasks"
    
    id = Column(String, primary_key=True, index=True)  # Celery任务ID
    experiment_id = Column(String, nullable=False, index=True)  # 关联的实验ID
    
    # 任务信息
    task_type = Column(String(50), nullable=False)  # 任务类型：backtest, training等
    task_name = Column(String(200), nullable=False)
    
    # 状态信息
    status = Column(String(20), default="pending", index=True)
    progress = Column(Integer, default=0)  # 进度百分比
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 结果和错误信息
    result = Column(JSON, nullable=True)  # 任务结果
    error_message = Column(Text, nullable=True)  # 错误信息
    traceback = Column(Text, nullable=True)  # 错误堆栈
    
    # 执行信息
    worker_id = Column(String(100), nullable=True)  # 执行任务的worker ID
    retry_count = Column(Integer, default=0)  # 重试次数
    max_retries = Column(Integer, default=3)  # 最大重试次数
    
    # 元数据
    task_metadata = Column(JSON, nullable=True)  # 任务元数据
    is_cancelled = Column(Boolean, default=False)  # 是否被取消
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "task_type": self.task_type,
            "task_name": self.task_name,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error_message": self.error_message,
            "worker_id": self.worker_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "task_metadata": self.task_metadata,
            "is_cancelled": self.is_cancelled,
        }
"""
实验模板数据库模型
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class ExperimentTemplate(Base):
    """实验模板模型"""
    __tablename__ = "experiment_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)  # 模板分类: 预设/用户自定义
    
    # 模板配置
    config = Column(JSON, nullable=False)  # 实验配置模板
    default_params = Column(JSON)  # 默认参数
    
    # 模板元数据
    author = Column(String(100))  # 模板作者
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 创建者ID
    version = Column(String(20), default="1.0.0")
    tags = Column(JSON)  # 标签列表
    
    # 使用统计
    usage_count = Column(Integer, default=0)  # 使用次数
    rating = Column(Integer, default=0)  # 评分 (0-5)
    rating_count = Column(Integer, default=0)  # 评分次数
    
    # 状态管理
    is_public = Column(Boolean, default=False)  # 是否公开
    is_featured = Column(Boolean, default=False)  # 是否推荐
    is_active = Column(Boolean, default=True)  # 是否活跃
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship("User", back_populates="templates")
    
    def __repr__(self):
        return f"<ExperimentTemplate(id='{self.id}', name='{self.name}', category='{self.category}')>"


class TemplateUsage(Base):
    """模板使用记录"""
    __tablename__ = "template_usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String, ForeignKey("experiment_templates.id"), nullable=False)
    experiment_id = Column(String, ForeignKey("experiments.id"))
    
    # 使用信息
    user_id = Column(String(50))  # 用户ID (暂时用字符串，后续可扩展)
    usage_type = Column(String(20), default="create")  # 使用类型: create/copy/modify
    
    # 统计信息
    success = Column(Boolean)  # 是否成功
    error_message = Column(Text)  # 错误信息
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    template = relationship("ExperimentTemplate", back_populates="usage_records")
    
    def __repr__(self):
        return f"<TemplateUsage(template_id='{self.template_id}', success={self.success})>"


# 添加关系
ExperimentTemplate.usage_records = relationship("TemplateUsage", back_populates="template")


class TemplateCategory(Base):
    """模板分类"""
    __tablename__ = "template_categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # 图标名称
    sort_order = Column(Integer, default=0)  # 排序
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TemplateCategory(name='{self.name}', display_name='{self.display_name}')>"
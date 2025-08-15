"""
评论和讨论相关数据库模型
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class CommentType(enum.Enum):
    """评论类型枚举"""
    EXPERIMENT = "experiment"     # 实验评论
    SHARE = "share"              # 分享评论
    TEMPLATE = "template"        # 模板评论


class ExperimentComment(Base):
    """实验评论模型"""
    __tablename__ = "experiment_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("experiment_comments.id"), nullable=True)  # 父评论ID，支持回复
    
    # 评论内容
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text, markdown, html
    
    # 提及功能
    mentioned_users = Column(JSON, nullable=True)  # 被@的用户ID列表
    
    # 状态管理
    is_edited = Column(Boolean, default=False)       # 是否已编辑
    is_deleted = Column(Boolean, default=False)      # 软删除标记
    is_pinned = Column(Boolean, default=False)       # 是否置顶
    
    # 互动统计
    likes_count = Column(Integer, default=0)         # 点赞数
    replies_count = Column(Integer, default=0)       # 回复数
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    experiment = relationship("Experiment", back_populates="comments")
    author = relationship("User", back_populates="comments")
    parent = relationship("ExperimentComment", remote_side=[id], back_populates="replies")
    replies = relationship("ExperimentComment", back_populates="parent", cascade="all, delete-orphan")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExperimentComment(id={self.id}, experiment_id='{self.experiment_id}', author_id={self.author_id})>"


class CommentLike(Base):
    """评论点赞模型"""
    __tablename__ = "comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("experiment_comments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    comment = relationship("ExperimentComment", back_populates="likes")
    user = relationship("User")
    
    def __repr__(self):
        return f"<CommentLike(comment_id={self.comment_id}, user_id={self.user_id})>"


class ExperimentLike(Base):
    """实验点赞模型"""
    __tablename__ = "experiment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    experiment = relationship("Experiment", back_populates="likes")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ExperimentLike(experiment_id='{self.experiment_id}', user_id={self.user_id})>"


class ExperimentFavorite(Base):
    """实验收藏模型"""
    __tablename__ = "experiment_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 收藏信息
    folder_name = Column(String(100), nullable=True)  # 收藏夹名称
    notes = Column(Text, nullable=True)               # 收藏备注
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    experiment = relationship("Experiment", back_populates="favorites")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ExperimentFavorite(experiment_id='{self.experiment_id}', user_id={self.user_id})>"


class TeamActivity(Base):
    """团队活动动态模型"""
    __tablename__ = "team_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 活动信息
    activity_type = Column(String(50), nullable=False)  # 活动类型：create_experiment, share_experiment, comment, like等
    target_type = Column(String(50), nullable=False)    # 目标类型：experiment, template, comment等
    target_id = Column(String(255), nullable=False)     # 目标ID
    
    # 活动内容
    title = Column(String(200), nullable=False)         # 活动标题
    description = Column(Text, nullable=True)           # 活动描述
    activity_metadata = Column(JSON, nullable=True)     # 额外的元数据
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    team = relationship("Team")
    user = relationship("User")
    
    def __repr__(self):
        return f"<TeamActivity(id={self.id}, team_id={self.team_id}, activity_type='{self.activity_type}')>"


class ExperimentRating(Base):
    """实验评分模型"""
    __tablename__ = "experiment_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 评分信息
    rating = Column(Integer, nullable=False)  # 评分 1-5
    review = Column(Text, nullable=True)      # 评价内容
    
    # 评分维度（可选）
    technical_score = Column(Integer, nullable=True)    # 技术分
    innovation_score = Column(Integer, nullable=True)   # 创新分
    practical_score = Column(Integer, nullable=True)    # 实用分
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    experiment = relationship("Experiment", back_populates="ratings")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ExperimentRating(experiment_id='{self.experiment_id}', user_id={self.user_id}, rating={self.rating})>"


# 更新现有模型的关系
def update_model_relationships():
    """更新现有模型的关系"""
    from .experiment import Experiment
    from .user import User
    
    # 为实验模型添加关系
    Experiment.comments = relationship("ExperimentComment", back_populates="experiment", cascade="all, delete-orphan")
    Experiment.likes = relationship("ExperimentLike", back_populates="experiment", cascade="all, delete-orphan")
    Experiment.favorites = relationship("ExperimentFavorite", back_populates="experiment", cascade="all, delete-orphan")
    Experiment.ratings = relationship("ExperimentRating", back_populates="experiment", cascade="all, delete-orphan")
    
    # 为用户模型添加关系
    User.comments = relationship("ExperimentComment", back_populates="author", cascade="all, delete-orphan")


# 调用函数更新关系
update_model_relationships()
"""
分享相关数据库模型
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
import secrets

from ..core.database import Base


class ShareType(enum.Enum):
    """分享类型枚举"""
    EXPERIMENT = "experiment"     # 实验分享
    TEMPLATE = "template"         # 模板分享


class SharePermission(enum.Enum):
    """分享权限枚举"""
    VIEW = "view"                 # 只读权限
    COMMENT = "comment"           # 评论权限
    COPY = "copy"                 # 复制权限


class ExperimentShare(Base):
    """实验分享模型"""
    __tablename__ = "experiment_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(255), ForeignKey("qlib_experiments.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 分享配置
    share_token = Column(String(64), unique=True, index=True, nullable=False)
    is_public = Column(Boolean, default=False)  # 是否公开分享
    is_active = Column(Boolean, default=True)   # 分享是否激活
    
    # 权限控制
    permissions = Column(String(20), default=SharePermission.VIEW.value)  # 分享权限
    password = Column(String(255), nullable=True)  # 访问密码（可选）
    
    # 限制条件
    max_views = Column(Integer, nullable=True)    # 最大访问次数
    current_views = Column(Integer, default=0)    # 当前访问次数
    expires_at = Column(DateTime, nullable=True)   # 过期时间
    
    # 描述信息
    title = Column(String(200), nullable=True)    # 分享标题
    description = Column(Text, nullable=True)     # 分享描述
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_accessed_at = Column(DateTime, nullable=True)
    
    # 关系
    experiment = relationship("Experiment", back_populates="shares")
    owner = relationship("User")
    share_logs = relationship("ShareAccessLog", back_populates="share", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.share_token:
            self.share_token = self.generate_share_token()
    
    @staticmethod
    def generate_share_token(length: int = 32) -> str:
        """生成分享令牌"""
        return secrets.token_urlsafe(length)
    
    def is_accessible(self) -> bool:
        """检查分享是否可访问"""
        if not self.is_active:
            return False
        
        # 检查过期时间
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
        
        # 检查访问次数限制
        if self.max_views and self.current_views >= self.max_views:
            return False
        
        return True
    
    def __repr__(self):
        return f"<ExperimentShare(id={self.id}, experiment_id='{self.experiment_id}', token='{self.share_token[:10]}...')>"


class ShareAccessLog(Base):
    """分享访问日志模型"""
    __tablename__ = "share_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(Integer, ForeignKey("experiment_shares.id"), nullable=False)
    
    # 访问信息
    ip_address = Column(String(45), nullable=True)     # IP地址
    user_agent = Column(Text, nullable=True)           # 用户代理
    referrer = Column(String(500), nullable=True)      # 来源页面
    
    # 用户信息（如果已登录）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 访问详情
    access_type = Column(String(20), default="view")   # 访问类型：view, copy, download
    success = Column(Boolean, default=True)            # 是否访问成功
    error_message = Column(String(500), nullable=True) # 错误信息
    
    # 时间信息
    accessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    share = relationship("ExperimentShare", back_populates="share_logs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ShareAccessLog(id={self.id}, share_id={self.share_id}, ip='{self.ip_address}')>"


class ShareInvitation(Base):
    """分享邀请模型"""
    __tablename__ = "share_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(Integer, ForeignKey("experiment_shares.id"), nullable=False)
    
    # 邀请信息
    email = Column(String(100), nullable=True)         # 邀请邮箱
    invited_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 被邀请的用户ID
    invitation_token = Column(String(64), unique=True, index=True, nullable=False)
    
    # 邀请状态
    is_accepted = Column(Boolean, default=False)       # 是否已接受
    is_expired = Column(Boolean, default=False)        # 是否已过期
    
    # 权限
    permissions = Column(String(20), default=SharePermission.VIEW.value)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)      # 邀请过期时间
    accepted_at = Column(DateTime, nullable=True)      # 接受时间
    
    # 关系
    share = relationship("ExperimentShare")
    invited_user = relationship("User")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.invitation_token:
            self.invitation_token = secrets.token_urlsafe(32)
    
    def is_valid(self) -> bool:
        """检查邀请是否有效"""
        if self.is_accepted or self.is_expired:
            return False
        
        if self.expires_at < datetime.now(timezone.utc):
            return False
        
        return True
    
    def __repr__(self):
        return f"<ShareInvitation(id={self.id}, email='{self.email}', accepted={self.is_accepted})>"


# 更新实验模型关系
def update_experiment_relationship():
    """更新实验模型的关系"""
    from .experiment import Experiment
    
    # 添加分享关系
    Experiment.shares = relationship("ExperimentShare", back_populates="experiment", cascade="all, delete-orphan")


# 调用函数更新关系
update_experiment_relationship()
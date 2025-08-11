"""
用户相关数据库模型
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class UserRole(enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"           # 管理员
    MANAGER = "manager"       # 团队管理员
    ANALYST = "analyst"       # 分析师
    VIEWER = "viewer"         # 只读用户


class UserStatus(enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"         # 激活
    INACTIVE = "inactive"     # 未激活
    SUSPENDED = "suspended"   # 暂停
    DELETED = "deleted"       # 已删除


# 用户和团队的多对多关系表
user_team_association = Table(
    'user_team_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True),
    Column('role', Enum(UserRole), default=UserRole.ANALYST),
    Column('joined_at', DateTime, default=lambda: datetime.now(timezone.utc))
)


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 用户信息
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    company = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    
    # 状态信息
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.INACTIVE, nullable=False)
    is_email_verified = Column(Boolean, default=False)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # 关系
    experiments = relationship("Experiment", back_populates="creator", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="creator", cascade="all, delete-orphan")
    teams = relationship("Team", secondary=user_team_association, back_populates="members")
    owned_teams = relationship("Team", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Team(Base):
    """团队模型"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 团队设置
    is_public = Column(Boolean, default=False)  # 是否公开团队
    max_members = Column(Integer, default=10)   # 最大成员数
    
    # 管理信息
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("User", secondary=user_team_association, back_populates="teams")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    
    # 会话信息
    ip_address = Column(String(45), nullable=True)  # 支持IPv6
    user_agent = Column(Text, nullable=True)
    device_info = Column(String(255), nullable=True)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, token='{self.session_token[:10]}...')>"


class PasswordResetToken(Base):
    """密码重置令牌模型"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # 状态
    is_used = Column(Boolean, default=False)
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"


class EmailVerificationToken(Base):
    """邮箱验证令牌模型"""
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    
    # 时间信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    
    # 状态
    is_verified = Column(Boolean, default=False)
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id}, is_verified={self.is_verified})>"
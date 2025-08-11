"""
用户相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

from ..models.user import UserRole, UserStatus


# 基础用户信息
class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


# 用户创建
class UserCreate(UserBase):
    """用户注册信息"""
    password: str = Field(..., min_length=8, max_length=50)
    confirm_password: str = Field(..., min_length=8, max_length=50)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v
    
    @validator('password')
    def password_complexity(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


# 用户更新
class UserUpdate(BaseModel):
    """用户信息更新"""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


# 密码相关
class PasswordChange(BaseModel):
    """密码修改"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=50)
    confirm_password: str = Field(..., min_length=8, max_length=50)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v
    
    @validator('new_password')
    def password_complexity(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class PasswordReset(BaseModel):
    """密码重置"""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=50)
    confirm_password: str = Field(..., min_length=8, max_length=50)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v


# 登录相关
class UserLogin(BaseModel):
    """用户登录"""
    username_or_email: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=50)
    remember_me: bool = False


class Token(BaseModel):
    """JWT令牌"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """令牌数据"""
    user_id: Optional[int] = None
    username: Optional[str] = None


# 用户响应
class UserResponse(UserBase):
    """用户响应信息"""
    id: int
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """用户摘要信息"""
    id: int
    username: str
    full_name: str
    avatar_url: Optional[str] = None
    role: UserRole
    status: UserStatus
    
    class Config:
        from_attributes = True


# 团队相关
class TeamBase(BaseModel):
    """团队基础信息"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: bool = False
    max_members: int = Field(default=10, ge=1, le=100)


class TeamCreate(TeamBase):
    """创建团队"""
    pass


class TeamUpdate(BaseModel):
    """团队更新"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    max_members: Optional[int] = Field(None, ge=1, le=100)


class TeamResponse(TeamBase):
    """团队响应"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    owner: UserSummary
    members: List[UserSummary] = []
    member_count: int = 0
    
    class Config:
        from_attributes = True


class TeamMember(BaseModel):
    """团队成员"""
    user_id: int
    role: UserRole
    joined_at: datetime
    
    # 用户信息
    user: UserSummary
    
    class Config:
        from_attributes = True


# 邮箱验证
class EmailVerification(BaseModel):
    """邮箱验证"""
    token: str = Field(..., min_length=1)


class EmailResend(BaseModel):
    """重新发送验证邮件"""
    email: EmailStr


# 搜索和筛选
class UserSearchParams(BaseModel):
    """用户搜索参数"""
    q: Optional[str] = None  # 搜索关键词
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    company: Optional[str] = None
    department: Optional[str] = None


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


# 用户统计
class UserStatistics(BaseModel):
    """用户统计"""
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    user_distribution: dict  # 按角色/状态分布


# API响应包装
class UserApiResponse(BaseModel):
    """用户API响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[UserResponse] = None


class TokenApiResponse(BaseModel):
    """令牌API响应"""
    success: bool = True
    message: str = "登录成功"
    data: Optional[Token] = None
"""
分享相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from ..models.share import SharePermission


# 基础分享信息
class ShareBase(BaseModel):
    """分享基础信息"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_public: bool = True
    permissions: SharePermission = SharePermission.VIEW
    password: Optional[str] = Field(None, min_length=4, max_length=50)
    max_views: Optional[int] = Field(None, ge=1, le=10000)
    expires_at: Optional[datetime] = None


# 创建分享
class ShareCreate(ShareBase):
    """创建分享请求"""
    experiment_id: str = Field(..., min_length=1)
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('过期时间必须是未来时间')
        return v


# 更新分享
class ShareUpdate(BaseModel):
    """更新分享请求"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[SharePermission] = None
    password: Optional[str] = Field(None, min_length=4, max_length=50)
    max_views: Optional[int] = Field(None, ge=1, le=10000)
    expires_at: Optional[datetime] = None
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('过期时间必须是未来时间')
        return v


# 分享访问请求
class ShareAccess(BaseModel):
    """分享访问请求"""
    password: Optional[str] = None


# 分享响应
class ShareResponse(ShareBase):
    """分享响应"""
    id: int
    experiment_id: str
    owner_id: int
    share_token: str
    is_active: bool
    current_views: int
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShareSummary(BaseModel):
    """分享摘要"""
    id: int
    experiment_id: str
    title: Optional[str]
    share_token: str
    is_public: bool
    is_active: bool
    permissions: SharePermission
    current_views: int
    max_views: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# 分享访问日志
class ShareAccessLogResponse(BaseModel):
    """分享访问日志响应"""
    id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]
    user_id: Optional[int]
    access_type: str
    success: bool
    error_message: Optional[str]
    accessed_at: datetime
    
    # 用户信息（如果存在）
    user: Optional[dict] = None
    
    class Config:
        from_attributes = True


# 分享邀请
class ShareInvitationCreate(BaseModel):
    """创建分享邀请"""
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    invited_user_id: Optional[int] = None
    permissions: SharePermission = SharePermission.VIEW
    expires_in_days: int = Field(7, ge=1, le=30)  # 邀请有效期（天数）
    
    @validator('email', 'invited_user_id')
    def validate_email_or_user_id(cls, v, values):
        email = values.get('email')
        invited_user_id = values.get('invited_user_id')
        
        if not email and not invited_user_id:
            raise ValueError('必须提供邮箱地址或用户ID')
        
        return v


class ShareInvitationResponse(BaseModel):
    """分享邀请响应"""
    id: int
    share_id: int
    email: Optional[str]
    invited_user_id: Optional[int]
    invitation_token: str
    is_accepted: bool
    is_expired: bool
    permissions: SharePermission
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]
    
    # 被邀请用户信息
    invited_user: Optional[dict] = None
    
    class Config:
        from_attributes = True


# 分享统计
class ShareStatistics(BaseModel):
    """分享统计"""
    share_id: int
    total_views: int
    unique_visitors: int
    views_today: int
    views_this_week: int
    views_this_month: int
    top_referrers: List[dict]
    view_timeline: List[dict]  # 访问时间线
    geographic_distribution: List[dict]  # 地理分布（如果有IP定位）


# API响应包装
class ShareApiResponse(BaseModel):
    """分享API响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[ShareResponse] = None


class ShareListResponse(BaseModel):
    """分享列表响应"""
    shares: List[ShareSummary]
    total: int
    page: int
    size: int
    pages: int


# 公开分享信息（用于匿名访问）
class PublicShareInfo(BaseModel):
    """公开分享信息"""
    id: int
    title: Optional[str]
    description: Optional[str]
    permissions: SharePermission
    requires_password: bool
    current_views: int
    max_views: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime
    
    # 实验基本信息
    experiment: dict
    
    # 分享者信息（脱敏）
    owner: dict


class ShareAccessResult(BaseModel):
    """分享访问结果"""
    success: bool
    message: str
    data: Optional[dict] = None
    requires_password: bool = False
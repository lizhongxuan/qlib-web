"""
评论和互动相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from ..schemas.user import UserSummary


# 评论相关
class CommentBase(BaseModel):
    """评论基础信息"""
    content: str = Field(..., min_length=1, max_length=2000)
    content_type: str = Field(default="text", regex="^(text|markdown|html)$")
    mentioned_users: Optional[List[int]] = None


class CommentCreate(CommentBase):
    """创建评论"""
    experiment_id: str = Field(..., min_length=1)
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    """更新评论"""
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    content_type: Optional[str] = Field(None, regex="^(text|markdown|html)$")
    mentioned_users: Optional[List[int]] = None


class CommentResponse(CommentBase):
    """评论响应"""
    id: int
    experiment_id: str
    author_id: int
    parent_id: Optional[int]
    is_edited: bool
    is_deleted: bool
    is_pinned: bool
    likes_count: int
    replies_count: int
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    author: UserSummary
    replies: Optional[List["CommentResponse"]] = []
    is_liked_by_user: Optional[bool] = None  # 当前用户是否点赞
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentResponse]
    total: int
    page: int
    size: int
    pages: int


# 点赞相关
class LikeAction(BaseModel):
    """点赞操作"""
    target_type: str = Field(..., regex="^(experiment|comment)$")
    target_id: str


class LikeResponse(BaseModel):
    """点赞响应"""
    success: bool
    liked: bool
    likes_count: int


# 收藏相关
class FavoriteCreate(BaseModel):
    """创建收藏"""
    experiment_id: str = Field(..., min_length=1)
    folder_name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: int
    experiment_id: str
    folder_name: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    # 实验信息
    experiment: Optional[dict] = None
    
    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    favorites: List[FavoriteResponse]
    total: int
    page: int
    size: int
    pages: int


# 评分相关
class RatingCreate(BaseModel):
    """创建评分"""
    experiment_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = Field(None, max_length=1000)
    technical_score: Optional[int] = Field(None, ge=1, le=5)
    innovation_score: Optional[int] = Field(None, ge=1, le=5)
    practical_score: Optional[int] = Field(None, ge=1, le=5)


class RatingUpdate(BaseModel):
    """更新评分"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = Field(None, max_length=1000)
    technical_score: Optional[int] = Field(None, ge=1, le=5)
    innovation_score: Optional[int] = Field(None, ge=1, le=5)
    practical_score: Optional[int] = Field(None, ge=1, le=5)


class RatingResponse(BaseModel):
    """评分响应"""
    id: int
    experiment_id: str
    user_id: int
    rating: int
    review: Optional[str]
    technical_score: Optional[int]
    innovation_score: Optional[int]
    practical_score: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # 用户信息
    user: UserSummary
    
    class Config:
        from_attributes = True


class RatingStatistics(BaseModel):
    """评分统计"""
    experiment_id: str
    average_rating: float
    total_ratings: int
    rating_distribution: dict  # {1: 10, 2: 5, 3: 20, 4: 30, 5: 35}
    average_technical_score: Optional[float]
    average_innovation_score: Optional[float]
    average_practical_score: Optional[float]


# 团队活动相关
class ActivityCreate(BaseModel):
    """创建活动"""
    team_id: int
    activity_type: str = Field(..., min_length=1, max_length=50)
    target_type: str = Field(..., min_length=1, max_length=50)
    target_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    metadata: Optional[dict] = None


class ActivityResponse(BaseModel):
    """活动响应"""
    id: int
    team_id: int
    user_id: int
    activity_type: str
    target_type: str
    target_id: str
    title: str
    description: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    
    # 用户信息
    user: UserSummary
    
    class Config:
        from_attributes = True


class ActivityListResponse(BaseModel):
    """活动列表响应"""
    activities: List[ActivityResponse]
    total: int
    page: int
    size: int
    pages: int


# 热门实验相关
class PopularExperiment(BaseModel):
    """热门实验"""
    experiment_id: str
    name: str
    description: Optional[str]
    creator_name: str
    likes_count: int
    comments_count: int
    views_count: int
    favorites_count: int
    average_rating: Optional[float]
    created_at: datetime
    
    # 热度评分
    popularity_score: float
    trending_score: float  # 趋势分数


class PopularExperimentList(BaseModel):
    """热门实验列表"""
    experiments: List[PopularExperiment]
    category: str  # most_liked, most_commented, trending等
    updated_at: datetime


# API响应包装
class CommentApiResponse(BaseModel):
    """评论API响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[CommentResponse] = None


class ActivityApiResponse(BaseModel):
    """活动API响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[ActivityResponse] = None


# 解决前向引用
CommentResponse.model_rebuild()
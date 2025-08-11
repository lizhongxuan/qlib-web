"""
实验模板数据模式
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.schemas.experiment import ExperimentConfigBase


class TemplateCategory(str, Enum):
    """模板分类枚举"""
    PRESET = "preset"  # 预设模板
    USER = "user"      # 用户自定义
    SHARED = "shared"  # 共享模板
    FEATURED = "featured"  # 推荐模板


class TemplateUsageType(str, Enum):
    """模板使用类型"""
    CREATE = "create"
    COPY = "copy"
    MODIFY = "modify"
    PREVIEW = "preview"


class ExperimentTemplateBase(BaseModel):
    """实验模板基类"""
    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, max_length=1000, description="模板描述")
    category: TemplateCategory = Field(..., description="模板分类")
    config: ExperimentConfigBase = Field(..., description="实验配置模板")
    default_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="默认参数")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    
    @validator("tags")
    def validate_tags(cls, v):
        if v and len(v) > 20:
            raise ValueError("标签数量不能超过20个")
        for tag in v or []:
            if not isinstance(tag, str) or len(tag) > 50:
                raise ValueError("标签必须是字符串且长度不超过50")
        return v


class ExperimentTemplateCreate(ExperimentTemplateBase):
    """创建模板请求"""
    author: Optional[str] = Field(None, max_length=100, description="作者")
    version: str = Field("1.0.0", description="版本号")
    is_public: bool = Field(False, description="是否公开")


class ExperimentTemplateUpdate(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    config: Optional[ExperimentConfigBase] = None
    default_params: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class ExperimentTemplateResponse(BaseModel):
    """模板响应"""
    id: str
    name: str
    description: Optional[str] = None
    category: TemplateCategory
    config: ExperimentConfigBase
    default_params: Optional[Dict[str, Any]] = None
    
    # 元数据
    author: Optional[str] = None
    version: str
    tags: List[str] = Field(default_factory=list)
    
    # 统计信息
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    
    # 状态
    is_public: bool = False
    is_featured: bool = False
    is_active: bool = True
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExperimentTemplateSummary(BaseModel):
    """模板摘要（用于列表展示）"""
    id: str
    name: str
    description: Optional[str] = None
    category: TemplateCategory
    author: Optional[str] = None
    version: str
    tags: List[str] = Field(default_factory=list)
    
    # 统计信息
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    
    # 状态
    is_public: bool = False
    is_featured: bool = False
    
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TemplateUsageCreate(BaseModel):
    """模板使用记录创建"""
    template_id: str = Field(..., description="模板ID")
    experiment_id: Optional[str] = Field(None, description="实验ID")
    usage_type: TemplateUsageType = Field(TemplateUsageType.CREATE, description="使用类型")
    user_id: Optional[str] = Field(None, description="用户ID")


class TemplateUsageResponse(BaseModel):
    """模板使用记录响应"""
    id: str
    template_id: str
    experiment_id: Optional[str] = None
    usage_type: TemplateUsageType
    user_id: Optional[str] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TemplateCategoryResponse(BaseModel):
    """模板分类响应"""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    template_count: Optional[int] = 0  # 分类下的模板数量
    
    class Config:
        from_attributes = True


class TemplateRatingRequest(BaseModel):
    """模板评分请求"""
    template_id: str = Field(..., description="模板ID")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    user_id: Optional[str] = Field(None, description="用户ID")


class TemplateSearchRequest(BaseModel):
    """模板搜索请求"""
    keyword: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[TemplateCategory] = Field(None, description="分类筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    author: Optional[str] = Field(None, description="作者筛选")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_featured: Optional[bool] = Field(None, description="是否推荐")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="最低评分")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方式")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
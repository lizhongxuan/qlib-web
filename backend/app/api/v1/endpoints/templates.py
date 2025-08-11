"""
实验模板 API 端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.template_service import TemplateService
from app.schemas.template import (
    ExperimentTemplateCreate,
    ExperimentTemplateUpdate,
    ExperimentTemplateResponse,
    ExperimentTemplateSummary,
    TemplateUsageCreate,
    TemplateUsageResponse,
    TemplateCategoryResponse,
    TemplateRatingRequest,
    TemplateSearchRequest
)
from app.schemas.common import APIResponse, PaginatedResponse

router = APIRouter()
template_service = TemplateService()


@router.post("", response_model=APIResponse[ExperimentTemplateResponse])
async def create_template(
    template_data: ExperimentTemplateCreate,
    db: Session = Depends(get_db)
):
    """创建实验模板"""
    try:
        template = await template_service.create_template(db, template_data)
        return APIResponse(
            success=True,
            data=ExperimentTemplateResponse.from_orm(template),
            message="模板创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.get("", response_model=APIResponse[PaginatedResponse[ExperimentTemplateSummary]])
async def get_templates(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    author: Optional[str] = Query(None, description="作者筛选"),
    tags: Optional[str] = Query(None, description="标签筛选（逗号分隔）"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    is_featured: Optional[bool] = Query(None, description="是否推荐"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
):
    """获取模板列表"""
    try:
        # 构建搜索请求
        search_request = TemplateSearchRequest(
            keyword=keyword,
            category=category,
            tags=tags.split(",") if tags else None,
            author=author,
            is_public=is_public,
            is_featured=is_featured,
            min_rating=min_rating,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        
        templates, total = await template_service.get_templates(db, search_request)
        
        # 转换为摘要格式
        template_summaries = [
            ExperimentTemplateSummary.from_orm(template) for template in templates
        ]
        
        return APIResponse(
            success=True,
            data=PaginatedResponse(
                items=template_summaries,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/featured", response_model=APIResponse[List[ExperimentTemplateSummary]])
async def get_featured_templates(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取推荐模板"""
    try:
        templates = await template_service.get_featured_templates(db, limit)
        template_summaries = [
            ExperimentTemplateSummary.from_orm(template) for template in templates
        ]
        return APIResponse(
            success=True,
            data=template_summaries,
            message=f"获取到 {len(template_summaries)} 个推荐模板"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐模板失败: {str(e)}")


@router.get("/popular", response_model=APIResponse[List[ExperimentTemplateSummary]])
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取热门模板"""
    try:
        templates = await template_service.get_popular_templates(db, limit)
        template_summaries = [
            ExperimentTemplateSummary.from_orm(template) for template in templates
        ]
        return APIResponse(
            success=True,
            data=template_summaries,
            message=f"获取到 {len(template_summaries)} 个热门模板"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门模板失败: {str(e)}")


@router.get("/categories", response_model=APIResponse[List[TemplateCategoryResponse]])
async def get_template_categories(db: Session = Depends(get_db)):
    """获取模板分类"""
    try:
        categories = await template_service.get_categories(db)
        return APIResponse(
            success=True,
            data=[TemplateCategoryResponse.from_orm(cat) for cat in categories]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")


@router.get("/{template_id}", response_model=APIResponse[ExperimentTemplateResponse])
async def get_template(template_id: str, db: Session = Depends(get_db)):
    """获取模板详情"""
    template = await template_service.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return APIResponse(
        success=True,
        data=ExperimentTemplateResponse.from_orm(template)
    )


@router.put("/{template_id}", response_model=APIResponse[ExperimentTemplateResponse])
async def update_template(
    template_id: str,
    update_data: ExperimentTemplateUpdate,
    db: Session = Depends(get_db)
):
    """更新模板"""
    template = await template_service.update_template(db, template_id, update_data)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return APIResponse(
        success=True,
        data=ExperimentTemplateResponse.from_orm(template),
        message="模板更新成功"
    )


@router.delete("/{template_id}", response_model=APIResponse[None])
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    """删除模板"""
    success = await template_service.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return APIResponse(success=True, message="模板删除成功")


@router.post("/{template_id}/clone", response_model=APIResponse[ExperimentTemplateResponse])
async def clone_template(
    template_id: str,
    new_name: str = Body(..., embed=True),
    user_id: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """克隆模板"""
    cloned_template = await template_service.clone_template(db, template_id, new_name, user_id)
    if not cloned_template:
        raise HTTPException(status_code=404, detail="源模板不存在")
    
    return APIResponse(
        success=True,
        data=ExperimentTemplateResponse.from_orm(cloned_template),
        message="模板克隆成功"
    )


@router.post("/{template_id}/usage", response_model=APIResponse[TemplateUsageResponse])
async def record_template_usage(
    template_id: str,
    usage_data: TemplateUsageCreate,
    db: Session = Depends(get_db)
):
    """记录模板使用"""
    try:
        usage_data.template_id = template_id  # 确保ID一致
        usage = await template_service.record_usage(db, usage_data)
        return APIResponse(
            success=True,
            data=TemplateUsageResponse.from_orm(usage),
            message="使用记录保存成功"
        )
    except Exception as e:
        # 记录失败的使用
        await template_service.record_usage(db, usage_data, success=False, error_message=str(e))
        raise HTTPException(status_code=500, detail=f"记录使用失败: {str(e)}")


@router.post("/{template_id}/rate", response_model=APIResponse[None])
async def rate_template(
    template_id: str,
    rating_request: TemplateRatingRequest,
    db: Session = Depends(get_db)
):
    """模板评分"""
    rating_request.template_id = template_id  # 确保ID一致
    success = await template_service.rate_template(
        db, 
        template_id, 
        rating_request.rating, 
        rating_request.user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return APIResponse(success=True, message="评分成功")


@router.post("/init-presets", response_model=APIResponse[List[ExperimentTemplateSummary]])
async def init_preset_templates(db: Session = Depends(get_db)):
    """初始化预设模板"""
    try:
        templates = await template_service.create_preset_templates(db)
        template_summaries = [
            ExperimentTemplateSummary.from_orm(template) for template in templates
        ]
        return APIResponse(
            success=True,
            data=template_summaries,
            message=f"成功创建 {len(template_summaries)} 个预设模板"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化预设模板失败: {str(e)}")
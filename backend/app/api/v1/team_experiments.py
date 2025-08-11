"""
团队实验管理API端点
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user, permission_checker
from ...models.user import User, Team
from ...models.experiment import Experiment
from ...services.user import team_service
from ...services.experiment_service import ExperimentService
from ...schemas.experiment import ExperimentSummary
from ...schemas.common import APIResponse, PaginatedResponse

router = APIRouter()
experiment_service = ExperimentService()


@router.get("/{team_id}/experiments", response_model=APIResponse[PaginatedResponse[ExperimentSummary]])
async def get_team_experiments(
    team_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取团队实验列表
    """
    try:
        # 检查团队是否存在
        team = team_service.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查是否是团队成员或管理员
        is_member = any(member.id == current_user.id for member in team.members)
        if not is_member and current_user.role.value != "admin":
            # 如果是公开团队，允许查看
            if not team.is_public:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
        
        # 获取团队成员的实验
        team_member_ids = [member.id for member in team.members]
        
        # 构建查询
        query = db.query(Experiment).filter(
            Experiment.creator_id.in_(team_member_ids),
            Experiment.is_deleted == False
        )
        
        # 状态筛选
        if status:
            query = query.filter(Experiment.status == status)
        
        # 搜索筛选
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Experiment.name.ilike(search_term)
            )
        
        # 排序
        query = query.order_by(Experiment.created_at.desc())
        
        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        experiments = query.offset(offset).limit(page_size).all()
        
        experiment_summaries = [
            ExperimentSummary(**exp.to_summary_dict())
            for exp in experiments
        ]
        
        return APIResponse(
            success=True,
            data=PaginatedResponse(
                items=experiment_summaries,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取团队实验列表失败: {str(e)}"
        )


@router.get("/{team_id}/statistics")
async def get_team_experiment_statistics(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取团队实验统计信息
    """
    try:
        # 检查团队是否存在
        team = team_service.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查是否是团队成员或管理员
        is_member = any(member.id == current_user.id for member in team.members)
        if not is_member and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 获取团队成员的实验统计
        team_member_ids = [member.id for member in team.members]
        
        # 总实验数
        total_experiments = db.query(Experiment).filter(
            Experiment.creator_id.in_(team_member_ids),
            Experiment.is_deleted == False
        ).count()
        
        # 按状态统计
        status_stats = {}
        statuses = ["pending", "running", "completed", "failed"]
        for exp_status in statuses:
            count = db.query(Experiment).filter(
                Experiment.creator_id.in_(team_member_ids),
                Experiment.status == exp_status,
                Experiment.is_deleted == False
            ).count()
            status_stats[exp_status] = count
        
        # 成员贡献统计
        member_stats = []
        for member in team.members:
            member_exp_count = db.query(Experiment).filter(
                Experiment.creator_id == member.id,
                Experiment.is_deleted == False
            ).count()
            
            member_stats.append({
                "user_id": member.id,
                "username": member.username,
                "full_name": member.full_name,
                "avatar_url": member.avatar_url,
                "experiment_count": member_exp_count
            })
        
        # 按实验数排序
        member_stats.sort(key=lambda x: x["experiment_count"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "team_id": team_id,
                "team_name": team.name,
                "member_count": len(team.members),
                "total_experiments": total_experiments,
                "status_statistics": status_stats,
                "member_statistics": member_stats
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取团队统计信息失败: {str(e)}"
        )


@router.get("/{team_id}/members/{user_id}/experiments")
async def get_team_member_experiments(
    team_id: int,
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取团队成员的实验列表
    """
    try:
        # 检查团队是否存在
        team = team_service.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查目标用户是否是团队成员
        target_member = None
        for member in team.members:
            if member.id == user_id:
                target_member = member
                break
        
        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不是团队成员"
            )
        
        # 检查权限（团队成员或管理员可以查看）
        is_team_member = any(member.id == current_user.id for member in team.members)
        if not is_team_member and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 获取该成员的实验
        query = db.query(Experiment).filter(
            Experiment.creator_id == user_id,
            Experiment.is_deleted == False
        ).order_by(Experiment.created_at.desc())
        
        total = query.count()
        offset = (page - 1) * page_size
        experiments = query.offset(offset).limit(page_size).all()
        
        experiment_summaries = [
            ExperimentSummary(**exp.to_summary_dict())
            for exp in experiments
        ]
        
        return {
            "success": True,
            "data": {
                "member": {
                    "id": target_member.id,
                    "username": target_member.username,
                    "full_name": target_member.full_name,
                    "avatar_url": target_member.avatar_url
                },
                "experiments": {
                    "items": experiment_summaries,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取团队成员实验列表失败: {str(e)}"
        )
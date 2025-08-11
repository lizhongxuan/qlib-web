"""
用户管理相关API端点
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user, get_current_admin, get_current_manager_or_admin
from ...models.user import User, UserRole, UserStatus
from ...schemas.user import (
    UserResponse, UserListResponse, UserSearchParams, UserStatistics,
    UserSummary, TeamCreate, TeamUpdate, TeamResponse
)
from ...services.user import user_service, team_service

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def get_users(
    q: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[UserRole] = Query(None, description="角色筛选"),
    status: Optional[UserStatus] = Query(None, description="状态筛选"),
    company: Optional[str] = Query(None, description="公司筛选"),
    department: Optional[str] = Query(None, description="部门筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户列表（需要管理员或团队管理员权限）
    """
    try:
        search_params = UserSearchParams(
            q=q,
            role=role,
            status=status,
            company=company,
            department=department
        )
        
        return user_service.search_users(db, search_params, page, size)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/statistics", response_model=UserStatistics)
async def get_user_statistics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户统计信息（需要管理员权限）
    """
    try:
        return user_service.get_user_statistics(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    根据ID获取用户信息
    """
    try:
        # 只能查看自己的信息，或者管理员可以查看所有用户
        if user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        user = user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新用户角色（需要管理员权限）
    """
    try:
        updated_user = user_service.update_user_role(db, user_id, role, current_user.id)
        return {
            "success": True,
            "message": "用户角色更新成功",
            "data": UserResponse.from_orm(updated_user)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户角色失败: {str(e)}"
        )


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: int,
    user_status: UserStatus,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新用户状态（需要管理员权限）
    """
    try:
        updated_user = user_service.update_user_status(db, user_id, user_status, current_user.id)
        return {
            "success": True,
            "message": "用户状态更新成功",
            "data": UserResponse.from_orm(updated_user)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户状态失败: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """
    删除用户（需要管理员权限）
    """
    try:
        user_service.delete_user(db, user_id, current_user.id)
        return {"success": True, "message": "用户删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


@router.get("/{user_id}/experiments")
async def get_user_experiments(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户的实验列表
    """
    try:
        # 只能查看自己的实验，或者管理员可以查看所有用户的实验
        if user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        experiments_data = user_service.get_user_experiments(db, user_id, page, size)
        return {"success": True, "data": experiments_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户实验列表失败: {str(e)}"
        )


@router.get("/{user_id}/templates")
async def get_user_templates(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户的模板列表
    """
    try:
        # 只能查看自己的模板，或者管理员可以查看所有用户的模板
        if user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        templates_data = user_service.get_user_templates(db, user_id, page, size)
        return {"success": True, "data": templates_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户模板列表失败: {str(e)}"
        )


# 团队管理相关端点
@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建团队
    """
    try:
        team = team_service.create_team(db, team_data, current_user.id)
        return TeamResponse.from_orm(team)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建团队失败: {str(e)}"
        )


@router.get("/teams")
async def get_user_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户的团队列表
    """
    try:
        teams = team_service.get_user_teams(db, current_user.id)
        return {"success": True, "data": teams}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取团队列表失败: {str(e)}"
        )


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team_by_id(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取团队详情
    """
    try:
        team = team_service.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查是否是团队成员或管理员
        is_member = any(member.id == current_user.id for member in team.members)
        if not is_member and current_user.role != UserRole.ADMIN:
            # 如果是公开团队，允许查看
            if not team.is_public:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
        
        return TeamResponse.from_orm(team)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取团队详情失败: {str(e)}"
        )


@router.put("/teams/{team_id}")
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新团队信息
    """
    try:
        team = team_service.update_team(db, team_id, team_update, current_user.id)
        return {
            "success": True,
            "message": "团队信息更新成功",
            "data": TeamResponse.from_orm(team)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新团队信息失败: {str(e)}"
        )


@router.post("/teams/{team_id}/members/{user_id}")
async def add_team_member(
    team_id: int,
    user_id: int,
    role: UserRole = UserRole.ANALYST,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    添加团队成员
    """
    try:
        team = team_service.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查权限（团队所有者或管理员）
        if team.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        team_service.add_team_member(db, team_id, user_id, role)
        return {"success": True, "message": "团队成员添加成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加团队成员失败: {str(e)}"
        )


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    移除团队成员
    """
    try:
        team_service.remove_team_member(db, team_id, user_id, current_user.id)
        return {"success": True, "message": "团队成员移除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除团队成员失败: {str(e)}"
        )


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    删除团队
    """
    try:
        team_service.delete_team(db, team_id, current_user.id)
        return {"success": True, "message": "团队删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除团队失败: {str(e)}"
        )
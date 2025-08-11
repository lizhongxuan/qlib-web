"""
用户管理服务
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc, and_
from fastapi import HTTPException, status

from ..models.user import User, Team, user_team_association, UserRole, UserStatus
from ..models.experiment import Experiment
from ..models.template import ExperimentTemplate
from ..schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserSummary, UserListResponse, 
    UserSearchParams, UserStatistics, TeamCreate, TeamUpdate, TeamResponse,
    TeamMember
)
from ..services.auth import auth_service
from ..utils.validators import SafeDataProcessor


class UserService:
    """用户管理服务"""
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(
            User.id == user_id,
            User.status != UserStatus.DELETED
        ).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(
            User.username == username,
            User.status != UserStatus.DELETED
        ).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(
            User.email == email,
            User.status != UserStatus.DELETED
        ).first()
    
    def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> User:
        """更新用户信息"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新字段
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        return user
    
    def update_user_status(self, db: Session, user_id: int, status: UserStatus,
                          operator_id: int) -> User:
        """更新用户状态（管理员操作）"""
        # 检查操作权限
        operator = self.get_user_by_id(db, operator_id)
        if not operator or operator.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不能修改自己的状态
        if user_id == operator_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改自己的状态"
            )
        
        user.status = status
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        return user
    
    def update_user_role(self, db: Session, user_id: int, role: UserRole,
                        operator_id: int) -> User:
        """更新用户角色（管理员操作）"""
        # 检查操作权限
        operator = self.get_user_by_id(db, operator_id)
        if not operator or operator.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不能修改自己的角色
        if user_id == operator_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改自己的角色"
            )
        
        user.role = role
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        return user
    
    def search_users(self, db: Session, search_params: UserSearchParams,
                    page: int = 1, size: int = 20) -> UserListResponse:
        """搜索用户"""
        query = db.query(User).filter(User.status != UserStatus.DELETED)
        
        # 关键词搜索
        if search_params.q:
            search_term = f"%{search_params.q}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.company.ilike(search_term),
                    User.department.ilike(search_term)
                )
            )
        
        # 角色筛选
        if search_params.role:
            query = query.filter(User.role == search_params.role)
        
        # 状态筛选
        if search_params.status:
            query = query.filter(User.status == search_params.status)
        
        # 公司筛选
        if search_params.company:
            query = query.filter(User.company.ilike(f"%{search_params.company}%"))
        
        # 部门筛选
        if search_params.department:
            query = query.filter(User.department.ilike(f"%{search_params.department}%"))
        
        # 排序
        query = query.order_by(desc(User.created_at))
        
        # 分页
        total = query.count()
        offset = (page - 1) * size
        users = query.offset(offset).limit(size).all()
        
        pages = (total + size - 1) // size
        
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    def get_user_statistics(self, db: Session) -> UserStatistics:
        """获取用户统计信息"""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 总用户数
        total_users = db.query(User).filter(User.status != UserStatus.DELETED).count()
        
        # 活跃用户数
        active_users = db.query(User).filter(
            User.status == UserStatus.ACTIVE
        ).count()
        
        # 今日新用户
        new_users_today = db.query(User).filter(
            User.created_at >= today_start,
            User.status != UserStatus.DELETED
        ).count()
        
        # 本周新用户
        new_users_this_week = db.query(User).filter(
            User.created_at >= week_start,
            User.status != UserStatus.DELETED
        ).count()
        
        # 本月新用户
        new_users_this_month = db.query(User).filter(
            User.created_at >= month_start,
            User.status != UserStatus.DELETED
        ).count()
        
        # 用户分布
        role_distribution = dict(
            db.query(User.role, func.count(User.id))
            .filter(User.status != UserStatus.DELETED)
            .group_by(User.role)
            .all()
        )
        
        status_distribution = dict(
            db.query(User.status, func.count(User.id))
            .filter(User.status != UserStatus.DELETED)
            .group_by(User.status)
            .all()
        )
        
        return UserStatistics(
            total_users=total_users,
            active_users=active_users,
            new_users_today=new_users_today,
            new_users_this_week=new_users_this_week,
            new_users_this_month=new_users_this_month,
            user_distribution={
                "by_role": {str(k): v for k, v in role_distribution.items()},
                "by_status": {str(k): v for k, v in status_distribution.items()}
            }
        )
    
    def get_user_experiments(self, db: Session, user_id: int, page: int = 1, 
                           size: int = 20) -> dict:
        """获取用户的实验列表"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        query = db.query(Experiment).filter(
            Experiment.creator_id == user_id,
            Experiment.is_deleted == False
        ).order_by(desc(Experiment.created_at))
        
        total = query.count()
        offset = (page - 1) * size
        experiments = query.offset(offset).limit(size).all()
        
        pages = (total + size - 1) // size
        
        return {
            "experiments": [exp.to_summary_dict() for exp in experiments],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def get_user_templates(self, db: Session, user_id: int, page: int = 1,
                          size: int = 20) -> dict:
        """获取用户的模板列表"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        query = db.query(ExperimentTemplate).filter(
            ExperimentTemplate.creator_id == user_id,
            ExperimentTemplate.is_active == True
        ).order_by(desc(ExperimentTemplate.created_at))
        
        total = query.count()
        offset = (page - 1) * size
        templates = query.offset(offset).limit(size).all()
        
        pages = (total + size - 1) // size
        
        return {
            "templates": [
                {
                    "id": tpl.id,
                    "name": tpl.name,
                    "description": tpl.description,
                    "category": tpl.category,
                    "usage_count": tpl.usage_count,
                    "rating": tpl.rating,
                    "is_public": tpl.is_public,
                    "created_at": tpl.created_at.isoformat()
                }
                for tpl in templates
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def delete_user(self, db: Session, user_id: int, operator_id: int) -> bool:
        """删除用户（软删除）"""
        # 检查操作权限
        operator = self.get_user_by_id(db, operator_id)
        if not operator or operator.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不能删除自己
        if user_id == operator_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己"
            )
        
        # 软删除
        user.status = UserStatus.DELETED
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return True


class TeamService:
    """团队管理服务"""
    
    def __init__(self):
        self.user_service = UserService()
    
    def create_team(self, db: Session, team_data: TeamCreate, owner_id: int) -> Team:
        """创建团队"""
        owner = self.user_service.get_user_by_id(db, owner_id)
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查团队名称是否已存在
        existing_team = db.query(Team).filter(Team.name == team_data.name).first()
        if existing_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="团队名称已存在"
            )
        
        team = Team(
            name=team_data.name,
            description=team_data.description,
            is_public=team_data.is_public,
            max_members=team_data.max_members,
            owner_id=owner_id
        )
        
        db.add(team)
        db.commit()
        db.refresh(team)
        
        # 将创建者添加为团队成员
        self.add_team_member(db, team.id, owner_id, UserRole.MANAGER)
        
        return team
    
    def get_team_by_id(self, db: Session, team_id: int) -> Optional[Team]:
        """根据ID获取团队"""
        return db.query(Team).options(
            joinedload(Team.owner),
            joinedload(Team.members)
        ).filter(Team.id == team_id).first()
    
    def update_team(self, db: Session, team_id: int, team_update: TeamUpdate,
                   operator_id: int) -> Team:
        """更新团队信息"""
        team = self.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查权限（只有团队所有者可以修改）
        if team.owner_id != operator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有团队所有者可以修改团队信息"
            )
        
        # 更新字段
        update_data = team_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(team, field):
                setattr(team, field, value)
        
        team.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(team)
        
        return team
    
    def add_team_member(self, db: Session, team_id: int, user_id: int,
                       role: UserRole = UserRole.ANALYST) -> bool:
        """添加团队成员"""
        team = self.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        user = self.user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查是否已经是团队成员
        existing = db.query(user_team_association).filter(
            and_(
                user_team_association.c.user_id == user_id,
                user_team_association.c.team_id == team_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已经是团队成员"
            )
        
        # 检查团队成员数量限制
        current_members = len(team.members)
        if current_members >= team.max_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="团队成员已达上限"
            )
        
        # 添加成员
        stmt = user_team_association.insert().values(
            user_id=user_id,
            team_id=team_id,
            role=role,
            joined_at=datetime.now(timezone.utc)
        )
        db.execute(stmt)
        db.commit()
        
        return True
    
    def remove_team_member(self, db: Session, team_id: int, user_id: int,
                          operator_id: int) -> bool:
        """移除团队成员"""
        team = self.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查权限（团队所有者或用户自己）
        if team.owner_id != operator_id and user_id != operator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 不能移除团队所有者
        if user_id == team.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能移除团队所有者"
            )
        
        # 移除成员
        result = db.execute(
            user_team_association.delete().where(
                and_(
                    user_team_association.c.user_id == user_id,
                    user_team_association.c.team_id == team_id
                )
            )
        )
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不是团队成员"
            )
        
        return True
    
    def get_user_teams(self, db: Session, user_id: int) -> List[TeamResponse]:
        """获取用户的团队列表"""
        user = self.user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        teams = db.query(Team).options(
            joinedload(Team.owner),
            joinedload(Team.members)
        ).join(user_team_association).filter(
            user_team_association.c.user_id == user_id
        ).all()
        
        result = []
        for team in teams:
            team_response = TeamResponse.from_orm(team)
            team_response.member_count = len(team.members)
            result.append(team_response)
        
        return result
    
    def delete_team(self, db: Session, team_id: int, operator_id: int) -> bool:
        """删除团队"""
        team = self.get_team_by_id(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        
        # 检查权限（只有团队所有者可以删除）
        if team.owner_id != operator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有团队所有者可以删除团队"
            )
        
        # 删除团队成员关联
        db.execute(
            user_team_association.delete().where(
                user_team_association.c.team_id == team_id
            )
        )
        
        # 删除团队
        db.delete(team)
        db.commit()
        
        return True


# 创建全局服务实例
user_service = UserService()
team_service = TeamService()
"""
分享管理服务
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from fastapi import HTTPException, status
from passlib.context import CryptContext

from ..models.share import ExperimentShare, ShareAccessLog, ShareInvitation, SharePermission
from ..models.experiment import Experiment
from ..models.user import User
from ..schemas.share import (
    ShareCreate, ShareUpdate, ShareResponse, ShareSummary, ShareListResponse,
    ShareInvitationCreate, ShareAccessLogResponse, ShareStatistics,
    PublicShareInfo, ShareAccessResult
)
from ..core.auth import permission_checker
from ..utils.validators import SafeDataProcessor


class ShareService:
    """分享管理服务"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_quick_share(self, db: Session, experiment_id: str, owner_id: int, 
                          permissions: SharePermission = SharePermission.VIEW,
                          expires_in_hours: int = 24) -> ExperimentShare:
        """快速创建分享（一键分享）"""
        from datetime import timedelta
        
        # 检查实验是否存在
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实验不存在"
            )
        
        # 检查权限
        owner = db.query(User).filter(User.id == owner_id).first()
        if not permission_checker.can_access_experiment(owner, experiment):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 检查是否已有活跃的分享，如果有则返回现有的
        existing_share = db.query(ExperimentShare).filter(
            and_(
                ExperimentShare.experiment_id == experiment_id,
                ExperimentShare.owner_id == owner_id,
                ExperimentShare.is_active == True
            )
        ).first()
        
        if existing_share and existing_share.is_accessible():
            return existing_share
        
        # 创建快速分享
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        
        share = ExperimentShare(
            experiment_id=experiment_id,
            owner_id=owner_id,
            title=f"{experiment.name} - 快速分享",
            description="通过一键分享创建",
            is_public=True,
            permissions=permissions.value,
            expires_at=expires_at,
            max_views=100  # 默认最大访问100次
        )
        
        db.add(share)
        db.commit()
        db.refresh(share)
        
        return share

    def create_share(self, db: Session, share_data: ShareCreate, owner_id: int) -> ExperimentShare:
        """创建分享"""
        # 检查实验是否存在
        experiment = db.query(Experiment).filter(Experiment.id == share_data.experiment_id).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实验不存在"
            )
        
        # 检查权限
        owner = db.query(User).filter(User.id == owner_id).first()
        if not permission_checker.can_access_experiment(owner, experiment):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 检查是否已有分享
        existing_share = db.query(ExperimentShare).filter(
            and_(
                ExperimentShare.experiment_id == share_data.experiment_id,
                ExperimentShare.owner_id == owner_id,
                ExperimentShare.is_active == True
            )
        ).first()
        
        if existing_share:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该实验已有活跃的分享链接"
            )
        
        # 创建分享
        share = ExperimentShare(
            experiment_id=share_data.experiment_id,
            owner_id=owner_id,
            title=share_data.title,
            description=share_data.description,
            is_public=share_data.is_public,
            permissions=share_data.permissions.value,
            password=self._hash_password(share_data.password) if share_data.password else None,
            max_views=share_data.max_views,
            expires_at=share_data.expires_at
        )
        
        db.add(share)
        db.commit()
        db.refresh(share)
        
        return share
    
    def get_share_by_token(self, db: Session, share_token: str) -> Optional[ExperimentShare]:
        """根据分享令牌获取分享"""
        return db.query(ExperimentShare).filter(
            ExperimentShare.share_token == share_token
        ).first()
    
    def get_user_shares(self, db: Session, user_id: int, page: int = 1, size: int = 20) -> ShareListResponse:
        """获取用户的分享列表"""
        query = db.query(ExperimentShare).filter(
            ExperimentShare.owner_id == user_id
        ).order_by(desc(ExperimentShare.created_at))
        
        total = query.count()
        offset = (page - 1) * size
        shares = query.offset(offset).limit(size).all()
        
        share_summaries = [
            ShareSummary(
                id=share.id,
                experiment_id=share.experiment_id,
                title=share.title,
                share_token=share.share_token,
                is_public=share.is_public,
                is_active=share.is_active,
                permissions=SharePermission(share.permissions),
                current_views=share.current_views,
                max_views=share.max_views,
                expires_at=share.expires_at,
                created_at=share.created_at
            )
            for share in shares
        ]
        
        pages = (total + size - 1) // size
        
        return ShareListResponse(
            shares=share_summaries,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    def update_share(self, db: Session, share_id: int, share_update: ShareUpdate, 
                    user_id: int) -> ExperimentShare:
        """更新分享"""
        share = db.query(ExperimentShare).filter(ExperimentShare.id == share_id).first()
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在"
            )
        
        # 检查权限
        if share.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 更新字段
        update_data = share_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password" and value:
                setattr(share, field, self._hash_password(value))
            elif field == "permissions" and value:
                setattr(share, field, value.value)
            elif hasattr(share, field):
                setattr(share, field, value)
        
        share.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(share)
        
        return share
    
    def delete_share(self, db: Session, share_id: int, user_id: int) -> bool:
        """删除分享"""
        share = db.query(ExperimentShare).filter(ExperimentShare.id == share_id).first()
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在"
            )
        
        # 检查权限
        if share.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        db.delete(share)
        db.commit()
        
        return True
    
    def access_share(self, db: Session, share_token: str, password: Optional[str] = None,
                    ip_address: str = None, user_agent: str = None, 
                    user_id: Optional[int] = None) -> ShareAccessResult:
        """访问分享"""
        share = self.get_share_by_token(db, share_token)
        if not share:
            return ShareAccessResult(
                success=False,
                message="分享不存在或已失效"
            )
        
        # 检查分享是否可访问
        if not share.is_accessible():
            return ShareAccessResult(
                success=False,
                message="分享已过期或达到访问限制"
            )
        
        # 检查密码
        if share.password:
            if not password:
                return ShareAccessResult(
                    success=False,
                    message="需要密码访问",
                    requires_password=True
                )
            
            if not self._verify_password(password, share.password):
                # 记录失败的访问
                self._log_access(db, share.id, ip_address, user_agent, user_id, 
                               "view", False, "密码错误")
                return ShareAccessResult(
                    success=False,
                    message="密码错误",
                    requires_password=True
                )
        
        # 增加访问计数
        share.current_views += 1
        share.last_accessed_at = datetime.now(timezone.utc)
        
        # 记录访问日志
        self._log_access(db, share.id, ip_address, user_agent, user_id, "view", True)
        
        # 获取实验信息
        experiment = db.query(Experiment).filter(Experiment.id == share.experiment_id).first()
        
        # 获取分享者信息（脱敏）
        owner = db.query(User).filter(User.id == share.owner_id).first()
        
        db.commit()
        
        return ShareAccessResult(
            success=True,
            message="访问成功",
            data={
                "share": {
                    "id": share.id,
                    "title": share.title,
                    "description": share.description,
                    "permissions": share.permissions,
                    "current_views": share.current_views,
                    "created_at": share.created_at.isoformat()
                },
                "experiment": experiment.to_dict() if experiment else None,
                "owner": {
                    "username": owner.username,
                    "full_name": owner.full_name,
                    "avatar_url": owner.avatar_url
                } if owner else None
            }
        )
    
    def get_public_share_info(self, db: Session, share_token: str) -> Optional[PublicShareInfo]:
        """获取公开分享信息（不记录访问）"""
        share = self.get_share_by_token(db, share_token)
        if not share or not share.is_public:
            return None
        
        experiment = db.query(Experiment).filter(Experiment.id == share.experiment_id).first()
        owner = db.query(User).filter(User.id == share.owner_id).first()
        
        return PublicShareInfo(
            id=share.id,
            title=share.title,
            description=share.description,
            permissions=SharePermission(share.permissions),
            requires_password=bool(share.password),
            current_views=share.current_views,
            max_views=share.max_views,
            expires_at=share.expires_at,
            created_at=share.created_at,
            experiment={
                "id": experiment.id,
                "name": experiment.name,
                "description": experiment.description,
                "status": experiment.status,
                "created_at": experiment.created_at.isoformat()
            } if experiment else {},
            owner={
                "username": owner.username,
                "full_name": owner.full_name,
                "avatar_url": owner.avatar_url
            } if owner else {}
        )
    
    def get_share_statistics(self, db: Session, share_id: int, user_id: int) -> ShareStatistics:
        """获取分享统计信息"""
        share = db.query(ExperimentShare).filter(ExperimentShare.id == share_id).first()
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在"
            )
        
        # 检查权限
        if share.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 总访问量
        total_views = db.query(ShareAccessLog).filter(
            ShareAccessLog.share_id == share_id,
            ShareAccessLog.success == True
        ).count()
        
        # 独立访客数
        unique_visitors = db.query(ShareAccessLog.ip_address).filter(
            ShareAccessLog.share_id == share_id,
            ShareAccessLog.success == True
        ).distinct().count()
        
        # 今日访问量
        views_today = db.query(ShareAccessLog).filter(
            ShareAccessLog.share_id == share_id,
            ShareAccessLog.success == True,
            ShareAccessLog.accessed_at >= today_start
        ).count()
        
        # 本周访问量
        views_this_week = db.query(ShareAccessLog).filter(
            ShareAccessLog.share_id == share_id,
            ShareAccessLog.success == True,
            ShareAccessLog.accessed_at >= week_start
        ).count()
        
        # 本月访问量
        views_this_month = db.query(ShareAccessLog).filter(
            ShareAccessLog.share_id == share_id,
            ShareAccessLog.success == True,
            ShareAccessLog.accessed_at >= month_start
        ).count()
        
        # 访问来源统计
        referrer_stats = db.query(
            ShareAccessLog.referrer,
            func.count(ShareAccessLog.id).label('count')
        ).filter(
            ShareAccessLog.share_id == share_id,
            ShareAccessLog.success == True,
            ShareAccessLog.referrer.isnot(None)
        ).group_by(ShareAccessLog.referrer).order_by(desc('count')).limit(10).all()
        
        top_referrers = [
            {"referrer": ref, "count": count}
            for ref, count in referrer_stats
        ]
        
        # 访问时间线（按天统计）
        timeline_stats = db.query(
            func.date(ShareAccessLog.accessed_at).label('date'),
            func.count(ShareAccessLog.id).label('count')
        ).filter(
            ShareAccessLog.share_id == share_id,
            ShareAccessLog.success == True,
            ShareAccessLog.accessed_at >= month_start
        ).group_by(func.date(ShareAccessLog.accessed_at)).order_by('date').all()
        
        view_timeline = [
            {"date": str(date), "count": count}
            for date, count in timeline_stats
        ]
        
        return ShareStatistics(
            share_id=share_id,
            total_views=total_views,
            unique_visitors=unique_visitors,
            views_today=views_today,
            views_this_week=views_this_week,
            views_this_month=views_this_month,
            top_referrers=top_referrers,
            view_timeline=view_timeline,
            geographic_distribution=[]  # TODO: 实现IP定位功能
        )
    
    def get_share_access_logs(self, db: Session, share_id: int, user_id: int,
                             page: int = 1, size: int = 50) -> dict:
        """获取分享访问日志"""
        share = db.query(ExperimentShare).filter(ExperimentShare.id == share_id).first()
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在"
            )
        
        # 检查权限
        if share.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        query = db.query(ShareAccessLog).filter(
            ShareAccessLog.share_id == share_id
        ).order_by(desc(ShareAccessLog.accessed_at))
        
        total = query.count()
        offset = (page - 1) * size
        logs = query.offset(offset).limit(size).all()
        
        log_responses = []
        for log in logs:
            log_data = ShareAccessLogResponse.from_orm(log)
            
            # 添加用户信息（如果有）
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    log_data.user = {
                        "id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "avatar_url": user.avatar_url
                    }
            
            log_responses.append(log_data)
        
        pages = (total + size - 1) // size
        
        return {
            "logs": log_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return self.pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    def _log_access(self, db: Session, share_id: int, ip_address: str = None,
                   user_agent: str = None, user_id: int = None,
                   access_type: str = "view", success: bool = True,
                   error_message: str = None):
        """记录访问日志"""
        log = ShareAccessLog(
            share_id=share_id,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            access_type=access_type,
            success=success,
            error_message=error_message
        )
        
        db.add(log)
        # 注意：这里不commit，让调用方决定何时commit


# 创建全局分享服务实例
share_service = ShareService()
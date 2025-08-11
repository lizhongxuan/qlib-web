"""
评论和互动管理服务
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, or_
from fastapi import HTTPException, status

from ..models.comment import (
    ExperimentComment, CommentLike, ExperimentLike, ExperimentFavorite,
    TeamActivity, ExperimentRating
)
from ..models.experiment import Experiment
from ..models.user import User, Team
from ..schemas.comment import (
    CommentCreate, CommentUpdate, CommentResponse, CommentListResponse,
    FavoriteCreate, FavoriteResponse, FavoriteListResponse,
    RatingCreate, RatingUpdate, RatingResponse, RatingStatistics,
    ActivityCreate, ActivityResponse, ActivityListResponse,
    PopularExperiment, PopularExperimentList, LikeResponse
)
from ..schemas.user import UserSummary
from ..core.auth import permission_checker


class CommentService:
    """评论管理服务"""
    
    def create_comment(self, db: Session, comment_data: CommentCreate, author_id: int) -> ExperimentComment:
        """创建评论"""
        # 检查实验是否存在
        experiment = db.query(Experiment).filter(Experiment.id == comment_data.experiment_id).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实验不存在"
            )
        
        # 检查访问权限
        author = db.query(User).filter(User.id == author_id).first()
        if not permission_checker.can_access_experiment(author, experiment):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 检查父评论是否存在
        if comment_data.parent_id:
            parent_comment = db.query(ExperimentComment).filter(
                ExperimentComment.id == comment_data.parent_id
            ).first()
            if not parent_comment or parent_comment.experiment_id != comment_data.experiment_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="父评论不存在"
                )
        
        # 创建评论
        comment = ExperimentComment(
            experiment_id=comment_data.experiment_id,
            author_id=author_id,
            parent_id=comment_data.parent_id,
            content=comment_data.content,
            content_type=comment_data.content_type,
            mentioned_users=comment_data.mentioned_users
        )
        
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        # 更新父评论的回复数
        if comment_data.parent_id:
            db.query(ExperimentComment).filter(
                ExperimentComment.id == comment_data.parent_id
            ).update({"replies_count": ExperimentComment.replies_count + 1})
            db.commit()
        
        # 创建团队活动记录（如果用户在团队中）
        self._create_team_activity(db, author_id, "comment", "experiment", 
                                 comment_data.experiment_id, f"评论了实验: {experiment.name}")
        
        return comment
    
    def get_experiment_comments(self, db: Session, experiment_id: str, 
                              page: int = 1, size: int = 20,
                              user_id: Optional[int] = None) -> CommentListResponse:
        """获取实验评论列表"""
        # 获取顶级评论
        query = db.query(ExperimentComment).options(
            joinedload(ExperimentComment.author),
            joinedload(ExperimentComment.replies).joinedload(ExperimentComment.author)
        ).filter(
            ExperimentComment.experiment_id == experiment_id,
            ExperimentComment.parent_id.is_(None),
            ExperimentComment.is_deleted == False
        ).order_by(desc(ExperimentComment.created_at))
        
        total = query.count()
        offset = (page - 1) * size
        comments = query.offset(offset).limit(size).all()
        
        # 转换为响应格式
        comment_responses = []
        for comment in comments:
            comment_response = self._build_comment_response(comment, db, user_id)
            comment_responses.append(comment_response)
        
        pages = (total + size - 1) // size
        
        return CommentListResponse(
            comments=comment_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    def update_comment(self, db: Session, comment_id: int, comment_update: CommentUpdate,
                      user_id: int) -> ExperimentComment:
        """更新评论"""
        comment = db.query(ExperimentComment).filter(ExperimentComment.id == comment_id).first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在"
            )
        
        # 检查权限（只有作者可以编辑）
        if comment.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能编辑自己的评论"
            )
        
        # 更新评论
        update_data = comment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(comment, field, value)
        
        comment.is_edited = True
        comment.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(comment)
        
        return comment
    
    def delete_comment(self, db: Session, comment_id: int, user_id: int) -> bool:
        """删除评论（软删除）"""
        comment = db.query(ExperimentComment).filter(ExperimentComment.id == comment_id).first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在"
            )
        
        # 检查权限（作者或管理员可以删除）
        user = db.query(User).filter(User.id == user_id).first()
        if comment.author_id != user_id and user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 软删除
        comment.is_deleted = True
        comment.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True
    
    def toggle_comment_like(self, db: Session, comment_id: int, user_id: int) -> LikeResponse:
        """切换评论点赞状态"""
        comment = db.query(ExperimentComment).filter(ExperimentComment.id == comment_id).first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在"
            )
        
        # 检查是否已点赞
        existing_like = db.query(CommentLike).filter(
            and_(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == user_id
            )
        ).first()
        
        if existing_like:
            # 取消点赞
            db.delete(existing_like)
            comment.likes_count = max(0, comment.likes_count - 1)
            liked = False
        else:
            # 添加点赞
            like = CommentLike(comment_id=comment_id, user_id=user_id)
            db.add(like)
            comment.likes_count += 1
            liked = True
        
        db.commit()
        
        return LikeResponse(
            success=True,
            liked=liked,
            likes_count=comment.likes_count
        )
    
    def toggle_experiment_like(self, db: Session, experiment_id: str, user_id: int) -> LikeResponse:
        """切换实验点赞状态"""
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实验不存在"
            )
        
        # 检查是否已点赞
        existing_like = db.query(ExperimentLike).filter(
            and_(
                ExperimentLike.experiment_id == experiment_id,
                ExperimentLike.user_id == user_id
            )
        ).first()
        
        likes_count = db.query(ExperimentLike).filter(
            ExperimentLike.experiment_id == experiment_id
        ).count()
        
        if existing_like:
            # 取消点赞
            db.delete(existing_like)
            likes_count -= 1
            liked = False
        else:
            # 添加点赞
            like = ExperimentLike(experiment_id=experiment_id, user_id=user_id)
            db.add(like)
            likes_count += 1
            liked = True
            
            # 创建团队活动记录
            self._create_team_activity(db, user_id, "like", "experiment", 
                                     experiment_id, f"点赞了实验: {experiment.name}")
        
        db.commit()
        
        return LikeResponse(
            success=True,
            liked=liked,
            likes_count=likes_count
        )
    
    def add_to_favorites(self, db: Session, favorite_data: FavoriteCreate, user_id: int) -> ExperimentFavorite:
        """添加到收藏"""
        # 检查实验是否存在
        experiment = db.query(Experiment).filter(Experiment.id == favorite_data.experiment_id).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实验不存在"
            )
        
        # 检查是否已收藏
        existing_favorite = db.query(ExperimentFavorite).filter(
            and_(
                ExperimentFavorite.experiment_id == favorite_data.experiment_id,
                ExperimentFavorite.user_id == user_id
            )
        ).first()
        
        if existing_favorite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="实验已在收藏夹中"
            )
        
        # 创建收藏
        favorite = ExperimentFavorite(
            experiment_id=favorite_data.experiment_id,
            user_id=user_id,
            folder_name=favorite_data.folder_name,
            notes=favorite_data.notes
        )
        
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        
        # 创建团队活动记录
        self._create_team_activity(db, user_id, "favorite", "experiment", 
                                 favorite_data.experiment_id, f"收藏了实验: {experiment.name}")
        
        return favorite
    
    def get_user_favorites(self, db: Session, user_id: int, page: int = 1, 
                          size: int = 20) -> FavoriteListResponse:
        """获取用户收藏列表"""
        query = db.query(ExperimentFavorite).options(
            joinedload(ExperimentFavorite.experiment)
        ).filter(
            ExperimentFavorite.user_id == user_id
        ).order_by(desc(ExperimentFavorite.created_at))
        
        total = query.count()
        offset = (page - 1) * size
        favorites = query.offset(offset).limit(size).all()
        
        favorite_responses = []
        for favorite in favorites:
            favorite_response = FavoriteResponse.from_orm(favorite)
            if favorite.experiment:
                favorite_response.experiment = favorite.experiment.to_summary_dict()
            favorite_responses.append(favorite_response)
        
        pages = (total + size - 1) // size
        
        return FavoriteListResponse(
            favorites=favorite_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    def _build_comment_response(self, comment: ExperimentComment, db: Session,
                               user_id: Optional[int] = None) -> CommentResponse:
        """构建评论响应"""
        # 检查当前用户是否点赞了该评论
        is_liked = False
        if user_id:
            like = db.query(CommentLike).filter(
                and_(
                    CommentLike.comment_id == comment.id,
                    CommentLike.user_id == user_id
                )
            ).first()
            is_liked = like is not None
        
        # 构建回复列表
        replies = []
        for reply in comment.replies:
            if not reply.is_deleted:
                reply_response = self._build_comment_response(reply, db, user_id)
                replies.append(reply_response)
        
        return CommentResponse(
            id=comment.id,
            experiment_id=comment.experiment_id,
            author_id=comment.author_id,
            parent_id=comment.parent_id,
            content=comment.content,
            content_type=comment.content_type,
            mentioned_users=comment.mentioned_users,
            is_edited=comment.is_edited,
            is_deleted=comment.is_deleted,
            is_pinned=comment.is_pinned,
            likes_count=comment.likes_count,
            replies_count=comment.replies_count,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            author=UserSummary.from_orm(comment.author),
            replies=replies,
            is_liked_by_user=is_liked
        )
    
    def _create_team_activity(self, db: Session, user_id: int, activity_type: str,
                            target_type: str, target_id: str, title: str):
        """创建团队活动记录"""
        # 获取用户所在的团队
        user = db.query(User).options(joinedload(User.teams)).filter(User.id == user_id).first()
        if not user or not user.teams:
            return
        
        # 为每个团队创建活动记录
        for team in user.teams:
            activity = TeamActivity(
                team_id=team.id,
                user_id=user_id,
                activity_type=activity_type,
                target_type=target_type,
                target_id=target_id,
                title=title
            )
            db.add(activity)
        
        db.commit()


class ActivityService:
    """活动管理服务"""
    
    def get_team_activities(self, db: Session, team_id: int, page: int = 1, 
                           size: int = 20) -> ActivityListResponse:
        """获取团队活动列表"""
        query = db.query(TeamActivity).options(
            joinedload(TeamActivity.user)
        ).filter(
            TeamActivity.team_id == team_id
        ).order_by(desc(TeamActivity.created_at))
        
        total = query.count()
        offset = (page - 1) * size
        activities = query.offset(offset).limit(size).all()
        
        activity_responses = [
            ActivityResponse(
                id=activity.id,
                team_id=activity.team_id,
                user_id=activity.user_id,
                activity_type=activity.activity_type,
                target_type=activity.target_type,
                target_id=activity.target_id,
                title=activity.title,
                description=activity.description,
                metadata=activity.metadata,
                created_at=activity.created_at,
                user=UserSummary.from_orm(activity.user)
            )
            for activity in activities
        ]
        
        pages = (total + size - 1) // size
        
        return ActivityListResponse(
            activities=activity_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class RecommendationService:
    """推荐服务"""
    
    def get_popular_experiments(self, db: Session, category: str = "trending", 
                               limit: int = 10) -> PopularExperimentList:
        """获取热门实验"""
        now = datetime.now(timezone.utc)
        
        if category == "most_liked":
            # 最多点赞
            query = db.query(
                Experiment.id,
                Experiment.name,
                Experiment.description,
                Experiment.created_at,
                User.username.label('creator_name'),
                func.count(ExperimentLike.id).label('likes_count')
            ).join(
                User, Experiment.creator_id == User.id
            ).outerjoin(
                ExperimentLike, Experiment.id == ExperimentLike.experiment_id
            ).filter(
                Experiment.is_deleted == False
            ).group_by(
                Experiment.id, User.username
            ).order_by(desc('likes_count')).limit(limit)
            
        elif category == "most_commented":
            # 最多评论
            query = db.query(
                Experiment.id,
                Experiment.name,
                Experiment.description,
                Experiment.created_at,
                User.username.label('creator_name'),
                func.count(ExperimentComment.id).label('comments_count')
            ).join(
                User, Experiment.creator_id == User.id
            ).outerjoin(
                ExperimentComment, and_(
                    Experiment.id == ExperimentComment.experiment_id,
                    ExperimentComment.is_deleted == False
                )
            ).filter(
                Experiment.is_deleted == False
            ).group_by(
                Experiment.id, User.username
            ).order_by(desc('comments_count')).limit(limit)
            
        else:  # trending
            # 趋势实验（基于最近7天的活动）
            week_ago = now - timedelta(days=7)
            query = db.query(
                Experiment.id,
                Experiment.name,
                Experiment.description,
                Experiment.created_at,
                User.username.label('creator_name')
            ).join(
                User, Experiment.creator_id == User.id
            ).filter(
                Experiment.is_deleted == False,
                Experiment.created_at >= week_ago
            ).order_by(desc(Experiment.created_at)).limit(limit)
        
        experiments = query.all()
        
        # 为每个实验计算详细统计
        popular_experiments = []
        for exp in experiments:
            # 获取统计数据
            likes_count = db.query(ExperimentLike).filter(
                ExperimentLike.experiment_id == exp.id
            ).count()
            
            comments_count = db.query(ExperimentComment).filter(
                ExperimentComment.experiment_id == exp.id,
                ExperimentComment.is_deleted == False
            ).count()
            
            favorites_count = db.query(ExperimentFavorite).filter(
                ExperimentFavorite.experiment_id == exp.id
            ).count()
            
            # TODO: 添加浏览量统计
            views_count = 0
            
            # TODO: 添加评分统计
            average_rating = None
            
            # 计算热度分数
            popularity_score = self._calculate_popularity_score(
                likes_count, comments_count, favorites_count, views_count
            )
            
            trending_score = self._calculate_trending_score(
                exp.created_at, likes_count, comments_count
            )
            
            popular_experiments.append(PopularExperiment(
                experiment_id=exp.id,
                name=exp.name,
                description=exp.description,
                creator_name=exp.creator_name,
                likes_count=likes_count,
                comments_count=comments_count,
                views_count=views_count,
                favorites_count=favorites_count,
                average_rating=average_rating,
                created_at=exp.created_at,
                popularity_score=popularity_score,
                trending_score=trending_score
            ))
        
        return PopularExperimentList(
            experiments=popular_experiments,
            category=category,
            updated_at=now
        )
    
    def _calculate_popularity_score(self, likes: int, comments: int, 
                                  favorites: int, views: int) -> float:
        """计算热度分数"""
        # 权重配置
        weights = {
            'likes': 3.0,
            'comments': 2.0,
            'favorites': 4.0,
            'views': 0.1
        }
        
        score = (
            likes * weights['likes'] +
            comments * weights['comments'] +
            favorites * weights['favorites'] +
            views * weights['views']
        )
        
        return round(score, 2)
    
    def _calculate_trending_score(self, created_at: datetime, likes: int, 
                                comments: int) -> float:
        """计算趋势分数（考虑时间衰减）"""
        now = datetime.now(timezone.utc)
        days_old = (now - created_at).days + 1
        
        # 时间衰减因子
        time_decay = 1.0 / (1 + days_old * 0.1)
        
        # 基础活跃度
        activity = likes * 2 + comments * 3
        
        trending_score = activity * time_decay
        
        return round(trending_score, 2)


# 创建全局服务实例
comment_service = CommentService()
activity_service = ActivityService()
recommendation_service = RecommendationService()
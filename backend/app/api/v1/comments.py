"""
评论和社区功能API端点
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user, get_current_user_optional
from ...models.user import User
from ...schemas.comment import (
    CommentCreate, CommentUpdate, CommentResponse, CommentListResponse,
    CommentApiResponse, FavoriteCreate, FavoriteResponse, FavoriteListResponse,
    LikeAction, LikeResponse, PopularExperimentList
)
from ...services.comment import comment_service, recommendation_service

router = APIRouter()


# 评论相关端点
@router.post("/", response_model=CommentApiResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建评论
    """
    try:
        comment = comment_service.create_comment(db, comment_data, current_user.id)
        
        # 构建响应
        comment_response = comment_service._build_comment_response(comment, db, current_user.id)
        
        return CommentApiResponse(
            success=True,
            message="评论创建成功",
            data=comment_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建评论失败: {str(e)}"
        )


@router.get("/experiment/{experiment_id}", response_model=CommentListResponse)
async def get_experiment_comments(
    experiment_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取实验评论列表
    """
    try:
        user_id = current_user.id if current_user else None
        return comment_service.get_experiment_comments(db, experiment_id, page, size, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评论列表失败: {str(e)}"
        )


@router.put("/{comment_id}", response_model=CommentApiResponse)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新评论
    """
    try:
        comment = comment_service.update_comment(db, comment_id, comment_update, current_user.id)
        
        # 构建响应
        comment_response = comment_service._build_comment_response(comment, db, current_user.id)
        
        return CommentApiResponse(
            success=True,
            message="评论更新成功",
            data=comment_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新评论失败: {str(e)}"
        )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    删除评论
    """
    try:
        comment_service.delete_comment(db, comment_id, current_user.id)
        return {"success": True, "message": "评论删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除评论失败: {str(e)}"
        )


# 点赞相关端点
@router.post("/like", response_model=LikeResponse)
async def toggle_like(
    like_action: LikeAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    切换点赞状态
    """
    try:
        if like_action.target_type == "comment":
            return comment_service.toggle_comment_like(db, int(like_action.target_id), current_user.id)
        elif like_action.target_type == "experiment":
            return comment_service.toggle_experiment_like(db, like_action.target_id, current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的点赞类型"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"点赞操作失败: {str(e)}"
        )


# 收藏相关端点
@router.post("/favorites", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    添加到收藏
    """
    try:
        favorite = comment_service.add_to_favorites(db, favorite_data, current_user.id)
        
        return FavoriteResponse.from_orm(favorite)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加收藏失败: {str(e)}"
        )


@router.get("/favorites", response_model=FavoriteListResponse)
async def get_user_favorites(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户收藏列表
    """
    try:
        return comment_service.get_user_favorites(db, current_user.id, page, size)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取收藏列表失败: {str(e)}"
        )


@router.delete("/favorites/{experiment_id}")
async def remove_from_favorites(
    experiment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    从收藏中移除
    """
    try:
        from ...models.comment import ExperimentFavorite
        from sqlalchemy import and_
        
        favorite = db.query(ExperimentFavorite).filter(
            and_(
                ExperimentFavorite.experiment_id == experiment_id,
                ExperimentFavorite.user_id == current_user.id
            )
        ).first()
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="收藏不存在"
            )
        
        db.delete(favorite)
        db.commit()
        
        return {"success": True, "message": "已从收藏中移除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除收藏失败: {str(e)}"
        )


# 社区功能端点
@router.get("/popular", response_model=PopularExperimentList)
async def get_popular_experiments(
    category: str = Query("trending", regex="^(trending|most_liked|most_commented)$", description="分类"),
    limit: int = Query(10, ge=1, le=50, description="数量限制"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取热门实验
    """
    try:
        return recommendation_service.get_popular_experiments(db, category, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取热门实验失败: {str(e)}"
        )


@router.get("/experiment/{experiment_id}/stats")
async def get_experiment_stats(
    experiment_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取实验统计信息
    """
    try:
        from ...models.comment import ExperimentLike, ExperimentComment, ExperimentFavorite
        from sqlalchemy import and_
        
        # 统计各种互动数据
        likes_count = db.query(ExperimentLike).filter(
            ExperimentLike.experiment_id == experiment_id
        ).count()
        
        comments_count = db.query(ExperimentComment).filter(
            ExperimentComment.experiment_id == experiment_id,
            ExperimentComment.is_deleted == False
        ).count()
        
        favorites_count = db.query(ExperimentFavorite).filter(
            ExperimentFavorite.experiment_id == experiment_id
        ).count()
        
        return {
            "success": True,
            "data": {
                "experiment_id": experiment_id,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "favorites_count": favorites_count,
                "views_count": 0  # TODO: 实现浏览量统计
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实验统计失败: {str(e)}"
        )


@router.get("/user/{user_id}/activity")
async def get_user_activity_summary(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户活动摘要
    """
    try:
        from datetime import timedelta
        from ...models.comment import ExperimentComment, ExperimentLike, ExperimentFavorite
        
        # 检查权限（只能查看自己的或公开的）
        if current_user and user_id != current_user.id:
            # TODO: 添加隐私设置检查
            pass
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 统计用户活动
        comments_count = db.query(ExperimentComment).filter(
            ExperimentComment.author_id == user_id,
            ExperimentComment.created_at >= start_date,
            ExperimentComment.is_deleted == False
        ).count()
        
        likes_count = db.query(ExperimentLike).filter(
            ExperimentLike.user_id == user_id,
            ExperimentLike.created_at >= start_date
        ).count()
        
        favorites_count = db.query(ExperimentFavorite).filter(
            ExperimentFavorite.user_id == user_id,
            ExperimentFavorite.created_at >= start_date
        ).count()
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "period_days": days,
                "comments_count": comments_count,
                "likes_count": likes_count,
                "favorites_count": favorites_count,
                "total_activity": comments_count + likes_count + favorites_count
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户活动摘要失败: {str(e)}"
        )
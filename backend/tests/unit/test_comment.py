"""
评论和社区功能的单元测试
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from app.services.comment import comment_service, recommendation_service
from app.models.comment import (
    ExperimentComment, CommentLike, ExperimentLike, 
    ExperimentFavorite, TeamActivity
)
from app.schemas.comment import CommentCreate, CommentUpdate, FavoriteCreate


class TestCommentService:
    """评论服务测试"""
    
    def test_create_comment_success(self, db_session, test_user, test_experiment):
        """测试成功创建评论"""
        comment_data = CommentCreate(
            experiment_id=test_experiment.id,
            content="这是一个测试评论",
            content_type="text"
        )
        
        comment = comment_service.create_comment(db_session, comment_data, test_user.id)
        
        assert comment.experiment_id == test_experiment.id
        assert comment.author_id == test_user.id
        assert comment.content == "这是一个测试评论"
        assert comment.content_type == "text"
        assert comment.parent_id is None
        assert comment.is_deleted is False
        assert comment.likes_count == 0
        assert comment.replies_count == 0
    
    def test_create_reply_comment(self, db_session, test_user, test_experiment, test_comment):
        """测试创建回复评论"""
        reply_data = CommentCreate(
            experiment_id=test_experiment.id,
            parent_id=test_comment.id,
            content="这是一个回复",
            content_type="text"
        )
        
        reply = comment_service.create_comment(db_session, reply_data, test_user.id)
        
        assert reply.parent_id == test_comment.id
        assert reply.content == "这是一个回复"
        
        # 验证父评论的回复数增加
        db_session.refresh(test_comment)
        assert test_comment.replies_count == 1
    
    def test_create_comment_invalid_parent(self, db_session, test_user, test_experiment):
        """测试创建评论时父评论无效"""
        comment_data = CommentCreate(
            experiment_id=test_experiment.id,
            parent_id=99999,  # 不存在的评论ID
            content="这是一个回复",
            content_type="text"
        )
        
        with pytest.raises(Exception) as exc_info:
            comment_service.create_comment(db_session, comment_data, test_user.id)
        
        assert "父评论不存在" in str(exc_info.value)
    
    def test_create_comment_with_mentions(self, db_session, test_user, test_experiment, test_user2):
        """测试创建带提及的评论"""
        comment_data = CommentCreate(
            experiment_id=test_experiment.id,
            content=f"@{test_user2.username} 请看这个实验",
            content_type="text",
            mentioned_users=[test_user2.id]
        )
        
        comment = comment_service.create_comment(db_session, comment_data, test_user.id)
        
        assert comment.mentioned_users == [test_user2.id]
        assert f"@{test_user2.username}" in comment.content
    
    def test_get_experiment_comments(self, db_session, test_experiment, test_comment):
        """测试获取实验评论列表"""
        comment_list = comment_service.get_experiment_comments(
            db_session, 
            test_experiment.id,
            page=1,
            size=20
        )
        
        assert comment_list.total >= 1
        assert len(comment_list.comments) >= 1
        assert comment_list.page == 1
        assert comment_list.size == 20
        
        # 验证评论信息
        found_comment = next(
            (c for c in comment_list.comments if c.id == test_comment.id),
            None
        )
        assert found_comment is not None
        assert found_comment.content == test_comment.content
        assert found_comment.author is not None
    
    def test_update_comment_success(self, db_session, test_user, test_comment):
        """测试成功更新评论"""
        comment_update = CommentUpdate(
            content="更新后的评论内容",
            content_type="markdown"
        )
        
        updated_comment = comment_service.update_comment(
            db_session, 
            test_comment.id, 
            comment_update, 
            test_user.id
        )
        
        assert updated_comment.content == "更新后的评论内容"
        assert updated_comment.content_type == "markdown"
        assert updated_comment.is_edited is True
        assert updated_comment.updated_at > test_comment.updated_at
    
    def test_update_comment_unauthorized(self, db_session, test_comment, test_user2):
        """测试无权限用户更新评论"""
        comment_update = CommentUpdate(content="恶意修改")
        
        with pytest.raises(Exception) as exc_info:
            comment_service.update_comment(
                db_session, 
                test_comment.id, 
                comment_update, 
                test_user2.id
            )
        
        assert "只能编辑自己的评论" in str(exc_info.value)
    
    def test_delete_comment_success(self, db_session, test_user, test_comment):
        """测试成功删除评论（作者操作）"""
        result = comment_service.delete_comment(db_session, test_comment.id, test_user.id)
        
        assert result is True
        
        # 验证评论被软删除
        db_session.refresh(test_comment)
        assert test_comment.is_deleted is True
        assert test_comment.updated_at > test_comment.created_at
    
    def test_delete_comment_by_admin(self, db_session, test_comment, test_admin_user):
        """测试管理员删除评论"""
        result = comment_service.delete_comment(db_session, test_comment.id, test_admin_user.id)
        
        assert result is True
        
        # 验证评论被软删除
        db_session.refresh(test_comment)
        assert test_comment.is_deleted is True
    
    def test_delete_comment_unauthorized(self, db_session, test_comment, test_user2):
        """测试无权限用户删除评论"""
        with pytest.raises(Exception) as exc_info:
            comment_service.delete_comment(db_session, test_comment.id, test_user2.id)
        
        assert "权限不足" in str(exc_info.value)
    
    def test_toggle_comment_like(self, db_session, test_user, test_comment):
        """测试评论点赞功能"""
        # 第一次点赞
        result = comment_service.toggle_comment_like(db_session, test_comment.id, test_user.id)
        
        assert result.success is True
        assert result.liked is True
        assert result.likes_count == 1
        
        # 验证数据库中的记录
        like = db_session.query(CommentLike).filter(
            CommentLike.comment_id == test_comment.id,
            CommentLike.user_id == test_user.id
        ).first()
        assert like is not None
        
        # 第二次点赞（取消点赞）
        result = comment_service.toggle_comment_like(db_session, test_comment.id, test_user.id)
        
        assert result.success is True
        assert result.liked is False
        assert result.likes_count == 0
        
        # 验证数据库中的记录已删除
        like = db_session.query(CommentLike).filter(
            CommentLike.comment_id == test_comment.id,
            CommentLike.user_id == test_user.id
        ).first()
        assert like is None
    
    def test_toggle_experiment_like(self, db_session, test_user, test_experiment):
        """测试实验点赞功能"""
        # 第一次点赞
        result = comment_service.toggle_experiment_like(
            db_session, 
            test_experiment.id, 
            test_user.id
        )
        
        assert result.success is True
        assert result.liked is True
        assert result.likes_count == 1
        
        # 验证数据库中的记录
        like = db_session.query(ExperimentLike).filter(
            ExperimentLike.experiment_id == test_experiment.id,
            ExperimentLike.user_id == test_user.id
        ).first()
        assert like is not None
        
        # 第二次点赞（取消点赞）
        result = comment_service.toggle_experiment_like(
            db_session, 
            test_experiment.id, 
            test_user.id
        )
        
        assert result.success is True
        assert result.liked is False
        assert result.likes_count == 0
    
    def test_add_to_favorites(self, db_session, test_user, test_experiment):
        """测试添加收藏"""
        favorite_data = FavoriteCreate(
            experiment_id=test_experiment.id,
            folder_name="我的收藏",
            notes="这是一个有趣的实验"
        )
        
        favorite = comment_service.add_to_favorites(db_session, favorite_data, test_user.id)
        
        assert favorite.experiment_id == test_experiment.id
        assert favorite.user_id == test_user.id
        assert favorite.folder_name == "我的收藏"
        assert favorite.notes == "这是一个有趣的实验"
    
    def test_add_duplicate_favorite(self, db_session, test_user, test_experiment):
        """测试添加重复收藏"""
        favorite_data = FavoriteCreate(experiment_id=test_experiment.id)
        
        # 第一次添加
        comment_service.add_to_favorites(db_session, favorite_data, test_user.id)
        
        # 第二次添加应该失败
        with pytest.raises(Exception) as exc_info:
            comment_service.add_to_favorites(db_session, favorite_data, test_user.id)
        
        assert "实验已在收藏夹中" in str(exc_info.value)
    
    def test_get_user_favorites(self, db_session, test_user, test_favorite):
        """测试获取用户收藏列表"""
        favorite_list = comment_service.get_user_favorites(
            db_session, 
            test_user.id,
            page=1,
            size=20
        )
        
        assert favorite_list.total >= 1
        assert len(favorite_list.favorites) >= 1
        assert favorite_list.page == 1
        assert favorite_list.size == 20
        
        # 验证收藏信息
        found_favorite = next(
            (f for f in favorite_list.favorites if f.id == test_favorite.id),
            None
        )
        assert found_favorite is not None
        assert found_favorite.experiment_id == test_favorite.experiment_id


class TestRecommendationService:
    """推荐服务测试"""
    
    def test_get_popular_experiments_trending(self, db_session, test_experiment_with_likes):
        """测试获取趋势实验"""
        popular_list = recommendation_service.get_popular_experiments(
            db_session,
            category="trending",
            limit=10
        )
        
        assert len(popular_list.experiments) >= 0
        assert popular_list.category == "trending"
        assert popular_list.updated_at is not None
        
        if popular_list.experiments:
            exp = popular_list.experiments[0]
            assert exp.experiment_id is not None
            assert exp.name is not None
            assert exp.popularity_score >= 0
            assert exp.trending_score >= 0
    
    def test_get_popular_experiments_most_liked(self, db_session, test_experiment_with_likes):
        """测试获取最多点赞实验"""
        popular_list = recommendation_service.get_popular_experiments(
            db_session,
            category="most_liked",
            limit=5
        )
        
        assert len(popular_list.experiments) >= 0
        assert popular_list.category == "most_liked"
        
        if len(popular_list.experiments) > 1:
            # 验证按点赞数排序
            for i in range(len(popular_list.experiments) - 1):
                assert (popular_list.experiments[i].likes_count >= 
                       popular_list.experiments[i + 1].likes_count)
    
    def test_get_popular_experiments_most_commented(self, db_session, test_experiment_with_comments):
        """测试获取最多评论实验"""
        popular_list = recommendation_service.get_popular_experiments(
            db_session,
            category="most_commented",
            limit=5
        )
        
        assert len(popular_list.experiments) >= 0
        assert popular_list.category == "most_commented"
    
    def test_calculate_popularity_score(self):
        """测试热度分数计算"""
        score = recommendation_service._calculate_popularity_score(
            likes=10,
            comments=5,
            favorites=3,
            views=100
        )
        
        expected_score = (10 * 3.0) + (5 * 2.0) + (3 * 4.0) + (100 * 0.1)
        assert score == round(expected_score, 2)
    
    def test_calculate_trending_score(self):
        """测试趋势分数计算"""
        now = datetime.now(timezone.utc)
        recent_date = now - timedelta(days=1)
        old_date = now - timedelta(days=30)
        
        # 最近创建的实验应该有更高的趋势分数
        recent_score = recommendation_service._calculate_trending_score(
            created_at=recent_date,
            likes=10,
            comments=5
        )
        
        old_score = recommendation_service._calculate_trending_score(
            created_at=old_date,
            likes=10,
            comments=5
        )
        
        assert recent_score > old_score
        assert recent_score > 0
        assert old_score > 0
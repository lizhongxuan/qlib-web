"""
分享功能的单元测试
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from app.services.share import share_service
from app.models.share import ExperimentShare, SharePermission, ShareAccessLog
from app.schemas.share import ShareCreate, ShareUpdate


class TestShareService:
    """分享服务测试"""
    
    def test_create_quick_share(self, db_session, test_user, test_experiment):
        """测试快速分享创建"""
        share = share_service.create_quick_share(
            db=db_session,
            experiment_id=test_experiment.id,
            owner_id=test_user.id,
            permissions=SharePermission.VIEW,
            expires_in_hours=24
        )
        
        assert share.experiment_id == test_experiment.id
        assert share.owner_id == test_user.id
        assert share.is_public is True
        assert share.is_active is True
        assert share.permissions == SharePermission.VIEW.value
        assert share.max_views == 100
        assert share.share_token is not None
        assert len(share.share_token) > 0
        
        # 验证过期时间
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        assert abs((share.expires_at - expected_expiry).total_seconds()) < 60  # 允许1分钟误差
    
    def test_create_quick_share_existing_active(self, db_session, test_user, test_experiment):
        """测试已有活跃分享时创建快速分享"""
        # 先创建一个分享
        first_share = share_service.create_quick_share(
            db=db_session,
            experiment_id=test_experiment.id,
            owner_id=test_user.id
        )
        
        # 再次创建应该返回已存在的分享
        second_share = share_service.create_quick_share(
            db=db_session,
            experiment_id=test_experiment.id,
            owner_id=test_user.id
        )
        
        assert first_share.id == second_share.id
        assert first_share.share_token == second_share.share_token
    
    def test_create_share_with_password(self, db_session, test_user, test_experiment):
        """测试创建带密码的分享"""
        share_data = ShareCreate(
            experiment_id=test_experiment.id,
            title="Test Share",
            description="Test Description",
            is_public=True,
            permissions=SharePermission.COPY,
            password="sharepassword",
            max_views=50,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        share = share_service.create_share(db_session, share_data, test_user.id)
        
        assert share.title == "Test Share"
        assert share.description == "Test Description"
        assert share.permissions == SharePermission.COPY.value
        assert share.password is not None
        assert share.password != "sharepassword"  # 应该被哈希
        assert share.max_views == 50
    
    def test_get_share_by_token(self, db_session, test_share):
        """测试通过令牌获取分享"""
        found_share = share_service.get_share_by_token(db_session, test_share.share_token)
        
        assert found_share is not None
        assert found_share.id == test_share.id
        assert found_share.share_token == test_share.share_token
    
    def test_get_share_by_invalid_token(self, db_session):
        """测试通过无效令牌获取分享"""
        found_share = share_service.get_share_by_token(db_session, "invalid_token")
        
        assert found_share is None
    
    def test_update_share(self, db_session, test_user, test_share):
        """测试更新分享"""
        share_update = ShareUpdate(
            title="Updated Title",
            description="Updated Description",
            is_active=False,
            max_views=200
        )
        
        updated_share = share_service.update_share(db_session, test_share.id, share_update, test_user.id)
        
        assert updated_share.title == "Updated Title"
        assert updated_share.description == "Updated Description"
        assert updated_share.is_active is False
        assert updated_share.max_views == 200
        assert updated_share.updated_at > test_share.updated_at
    
    def test_update_share_unauthorized(self, db_session, test_share):
        """测试无权限用户更新分享"""
        unauthorized_user_id = test_share.owner_id + 1
        share_update = ShareUpdate(title="Hacked Title")
        
        with pytest.raises(Exception) as exc_info:
            share_service.update_share(db_session, test_share.id, share_update, unauthorized_user_id)
        
        assert "权限不足" in str(exc_info.value)
    
    def test_delete_share(self, db_session, test_user, test_share):
        """测试删除分享"""
        result = share_service.delete_share(db_session, test_share.id, test_user.id)
        
        assert result is True
        
        # 验证分享已从数据库删除
        deleted_share = db_session.query(ExperimentShare).filter(
            ExperimentShare.id == test_share.id
        ).first()
        assert deleted_share is None
    
    def test_delete_share_unauthorized(self, db_session, test_share):
        """测试无权限用户删除分享"""
        unauthorized_user_id = test_share.owner_id + 1
        
        with pytest.raises(Exception) as exc_info:
            share_service.delete_share(db_session, test_share.id, unauthorized_user_id)
        
        assert "权限不足" in str(exc_info.value)
    
    def test_access_share_success(self, db_session, test_share_with_experiment):
        """测试成功访问分享"""
        result = share_service.access_share(
            db=db_session,
            share_token=test_share_with_experiment.share_token,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert result.success is True
        assert result.message == "访问成功"
        assert result.data is not None
        assert result.data["share"]["id"] == test_share_with_experiment.id
        assert result.data["experiment"] is not None
        
        # 验证访问计数增加
        db_session.refresh(test_share_with_experiment)
        assert test_share_with_experiment.current_views == 1
        assert test_share_with_experiment.last_accessed_at is not None
        
        # 验证访问日志创建
        access_log = db_session.query(ShareAccessLog).filter(
            ShareAccessLog.share_id == test_share_with_experiment.id
        ).first()
        assert access_log is not None
        assert access_log.success is True
        assert access_log.ip_address == "127.0.0.1"
        assert access_log.user_agent == "Test Browser"
    
    def test_access_share_with_password_success(self, db_session, test_share_with_password):
        """测试使用正确密码访问分享"""
        result = share_service.access_share(
            db=db_session,
            share_token=test_share_with_password.share_token,
            password="testpassword",
            ip_address="127.0.0.1"
        )
        
        assert result.success is True
        assert result.message == "访问成功"
    
    def test_access_share_with_wrong_password(self, db_session, test_share_with_password):
        """测试使用错误密码访问分享"""
        result = share_service.access_share(
            db=db_session,
            share_token=test_share_with_password.share_token,
            password="wrongpassword",
            ip_address="127.0.0.1"
        )
        
        assert result.success is False
        assert result.message == "密码错误"
        assert result.requires_password is True
        
        # 验证失败的访问被记录
        access_log = db_session.query(ShareAccessLog).filter(
            ShareAccessLog.share_id == test_share_with_password.id,
            ShareAccessLog.success == False
        ).first()
        assert access_log is not None
        assert access_log.error_message == "密码错误"
    
    def test_access_share_missing_password(self, db_session, test_share_with_password):
        """测试访问需要密码的分享但未提供密码"""
        result = share_service.access_share(
            db=db_session,
            share_token=test_share_with_password.share_token,
            ip_address="127.0.0.1"
        )
        
        assert result.success is False
        assert result.message == "需要密码访问"
        assert result.requires_password is True
    
    def test_access_expired_share(self, db_session, test_expired_share):
        """测试访问过期分享"""
        result = share_service.access_share(
            db=db_session,
            share_token=test_expired_share.share_token,
            ip_address="127.0.0.1"
        )
        
        assert result.success is False
        assert result.message == "分享已过期或达到访问限制"
    
    def test_access_share_max_views_reached(self, db_session, test_share_max_views):
        """测试访问达到最大访问次数的分享"""
        result = share_service.access_share(
            db=db_session,
            share_token=test_share_max_views.share_token,
            ip_address="127.0.0.1"
        )
        
        assert result.success is False
        assert result.message == "分享已过期或达到访问限制"
    
    def test_access_invalid_share(self, db_session):
        """测试访问不存在的分享"""
        result = share_service.access_share(
            db=db_session,
            share_token="invalid_token",
            ip_address="127.0.0.1"
        )
        
        assert result.success is False
        assert result.message == "分享不存在或已失效"
    
    def test_get_public_share_info(self, db_session, test_share_with_experiment):
        """测试获取公开分享信息"""
        share_info = share_service.get_public_share_info(
            db_session, 
            test_share_with_experiment.share_token
        )
        
        assert share_info is not None
        assert share_info.id == test_share_with_experiment.id
        assert share_info.title == test_share_with_experiment.title
        assert share_info.permissions == SharePermission(test_share_with_experiment.permissions)
        assert share_info.requires_password is False
        assert share_info.experiment is not None
        assert share_info.owner is not None
    
    def test_get_public_share_info_private(self, db_session, test_private_share):
        """测试获取私有分享信息"""
        share_info = share_service.get_public_share_info(
            db_session, 
            test_private_share.share_token
        )
        
        assert share_info is None
    
    def test_get_user_shares(self, db_session, test_user, test_share):
        """测试获取用户分享列表"""
        share_list = share_service.get_user_shares(db_session, test_user.id, page=1, size=20)
        
        assert share_list.total >= 1
        assert len(share_list.shares) >= 1
        assert share_list.page == 1
        assert share_list.size == 20
        
        # 验证分享信息
        found_share = next(
            (s for s in share_list.shares if s.id == test_share.id), 
            None
        )
        assert found_share is not None
        assert found_share.experiment_id == test_share.experiment_id
    
    def test_share_accessibility(self, test_share):
        """测试分享可访问性检查"""
        # 测试正常分享
        assert test_share.is_accessible() is True
        
        # 测试非活跃分享
        test_share.is_active = False
        assert test_share.is_accessible() is False
        
        # 重置状态
        test_share.is_active = True
        
        # 测试过期分享
        test_share.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert test_share.is_accessible() is False
        
        # 重置过期时间
        test_share.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # 测试达到访问限制的分享
        test_share.max_views = 5
        test_share.current_views = 5
        assert test_share.is_accessible() is False
        
        # 测试未达到限制
        test_share.current_views = 3
        assert test_share.is_accessible() is True
    
    def test_generate_share_token(self):
        """测试分享令牌生成"""
        token1 = ExperimentShare.generate_share_token()
        token2 = ExperimentShare.generate_share_token()
        
        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0
        
        # 测试指定长度
        token3 = ExperimentShare.generate_share_token(16)
        assert len(token3) > 0
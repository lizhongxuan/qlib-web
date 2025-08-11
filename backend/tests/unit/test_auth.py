"""
认证相关功能的单元测试
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from app.services.auth import auth_service
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserLogin, PasswordChange


class TestAuthService:
    """认证服务测试"""
    
    def test_hash_password(self):
        """测试密码哈希"""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("WrongPassword", hashed)
    
    def test_generate_token(self):
        """测试令牌生成"""
        user_id = 1
        username = "testuser"
        
        # 测试访问令牌
        access_token = auth_service.generate_token(user_id, username, "access")
        assert access_token is not None
        assert isinstance(access_token, str)
        
        # 测试刷新令牌
        refresh_token = auth_service.generate_token(user_id, username, "refresh")
        assert refresh_token is not None
        assert isinstance(refresh_token, str)
        assert access_token != refresh_token
    
    def test_verify_token(self):
        """测试令牌验证"""
        user_id = 1
        username = "testuser"
        
        token = auth_service.generate_token(user_id, username, "access")
        token_data = auth_service.verify_token(token, "access")
        
        assert token_data is not None
        assert token_data.user_id == user_id
        assert token_data.username == username
    
    def test_verify_invalid_token(self):
        """测试无效令牌验证"""
        invalid_token = "invalid.token.string"
        token_data = auth_service.verify_token(invalid_token, "access")
        
        assert token_data is None
    
    @patch('app.services.auth.auth_service._send_email')
    def test_register_user(self, mock_send_email, db_session):
        """测试用户注册"""
        mock_send_email.return_value = True
        
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="Password123",
            confirm_password="Password123"
        )
        
        user = auth_service.register_user(db_session, user_data)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.status == UserStatus.INACTIVE  # 需要邮箱验证
        assert user.is_email_verified is False
        
        # 验证密码已哈希
        assert user.hashed_password != "Password123"
        assert auth_service.verify_password("Password123", user.hashed_password)
    
    def test_register_duplicate_username(self, db_session, test_user):
        """测试注册重复用户名"""
        user_data = UserCreate(
            username=test_user.username,  # 使用已存在的用户名
            email="another@example.com",
            full_name="Another User",
            password="Password123",
            confirm_password="Password123"
        )
        
        with pytest.raises(Exception) as exc_info:
            auth_service.register_user(db_session, user_data)
        
        assert "用户名已存在" in str(exc_info.value)
    
    def test_register_duplicate_email(self, db_session, test_user):
        """测试注册重复邮箱"""
        user_data = UserCreate(
            username="newuser",
            email=test_user.email,  # 使用已存在的邮箱
            full_name="New User",
            password="Password123",
            confirm_password="Password123"
        )
        
        with pytest.raises(Exception) as exc_info:
            auth_service.register_user(db_session, user_data)
        
        assert "邮箱已存在" in str(exc_info.value)
    
    def test_authenticate_user_success(self, db_session, test_user):
        """测试用户认证成功"""
        # 设置用户为活跃状态
        test_user.status = UserStatus.ACTIVE
        db_session.commit()
        
        login_data = UserLogin(
            username_or_email=test_user.username,
            password="testpassword"
        )
        
        authenticated_user = auth_service.authenticate_user(db_session, login_data)
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        assert authenticated_user.username == test_user.username
        assert authenticated_user.last_login_at is not None
    
    def test_authenticate_user_with_email(self, db_session, test_user):
        """测试使用邮箱认证用户"""
        test_user.status = UserStatus.ACTIVE
        db_session.commit()
        
        login_data = UserLogin(
            username_or_email=test_user.email,  # 使用邮箱
            password="testpassword"
        )
        
        authenticated_user = auth_service.authenticate_user(db_session, login_data)
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
    
    def test_authenticate_user_wrong_password(self, db_session, test_user):
        """测试错误密码认证"""
        test_user.status = UserStatus.ACTIVE
        db_session.commit()
        
        login_data = UserLogin(
            username_or_email=test_user.username,
            password="wrongpassword"
        )
        
        authenticated_user = auth_service.authenticate_user(db_session, login_data)
        
        assert authenticated_user is None
    
    def test_authenticate_suspended_user(self, db_session, test_user):
        """测试暂停用户认证"""
        test_user.status = UserStatus.SUSPENDED
        db_session.commit()
        
        login_data = UserLogin(
            username_or_email=test_user.username,
            password="testpassword"
        )
        
        with pytest.raises(Exception) as exc_info:
            auth_service.authenticate_user(db_session, login_data)
        
        assert "账户已被暂停" in str(exc_info.value)
    
    def test_create_tokens(self, test_user):
        """测试创建令牌"""
        tokens = auth_service.create_tokens(test_user)
        
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 30 * 60  # 30分钟
    
    def test_change_password_success(self, db_session, test_user):
        """测试修改密码成功"""
        password_data = PasswordChange(
            current_password="testpassword",
            new_password="NewPassword123"
        )
        
        result = auth_service.change_password(db_session, test_user, password_data)
        
        assert result is True
        
        # 验证新密码
        db_session.refresh(test_user)
        assert auth_service.verify_password("NewPassword123", test_user.hashed_password)
        assert not auth_service.verify_password("testpassword", test_user.hashed_password)
    
    def test_change_password_wrong_current(self, db_session, test_user):
        """测试修改密码时当前密码错误"""
        password_data = PasswordChange(
            current_password="wrongpassword",
            new_password="NewPassword123"
        )
        
        with pytest.raises(Exception) as exc_info:
            auth_service.change_password(db_session, test_user, password_data)
        
        assert "当前密码不正确" in str(exc_info.value)
    
    @patch('app.services.auth.auth_service._send_email')
    def test_create_password_reset_token(self, mock_send_email, db_session, test_user):
        """测试创建密码重置令牌"""
        mock_send_email.return_value = True
        
        result = auth_service.create_password_reset_token(db_session, test_user.email)
        
        assert result is True
        mock_send_email.assert_called_once()
        
        # 验证数据库中创建了重置令牌
        from app.models.user import PasswordResetToken
        reset_token = db_session.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == test_user.id
        ).first()
        
        assert reset_token is not None
        assert reset_token.is_used is False
        assert reset_token.expires_at > datetime.now(timezone.utc)
    
    def test_create_password_reset_token_nonexistent_email(self, db_session):
        """测试为不存在的邮箱创建重置令牌"""
        # 为了安全，即使邮箱不存在也应该返回成功
        result = auth_service.create_password_reset_token(db_session, "nonexistent@example.com")
        
        assert result is True
    
    @patch('app.services.auth.auth_service._send_email')
    def test_verify_email_success(self, mock_send_email, db_session, test_user):
        """测试邮箱验证成功"""
        # 先创建验证令牌
        auth_service.send_verification_email(db_session, test_user)
        
        from app.models.user import EmailVerificationToken
        verification_token = db_session.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == test_user.id
        ).first()
        
        # 验证邮箱
        result = auth_service.verify_email(db_session, verification_token.token)
        
        assert result is True
        
        # 验证用户状态更新
        db_session.refresh(test_user)
        assert test_user.status == UserStatus.ACTIVE
        assert test_user.is_email_verified is True
        assert test_user.email_verified_at is not None
    
    def test_verify_email_invalid_token(self, db_session):
        """测试无效的邮箱验证令牌"""
        with pytest.raises(Exception) as exc_info:
            auth_service.verify_email(db_session, "invalid_token")
        
        assert "无效或已过期的验证令牌" in str(exc_info.value)
    
    def test_generate_random_token(self):
        """测试生成随机令牌"""
        token1 = auth_service.generate_random_token()
        token2 = auth_service.generate_random_token()
        
        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0
        
        # 测试指定长度
        token3 = auth_service.generate_random_token(16)
        assert len(token3) > 0
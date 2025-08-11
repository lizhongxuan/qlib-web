"""
用户认证服务
"""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from passlib.context import CryptContext
import jwt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from ..models.user import User, UserSession, PasswordResetToken, EmailVerificationToken, UserStatus
from ..schemas.user import UserCreate, UserLogin, Token, TokenData, PasswordChange, PasswordReset
from ..core.config import settings
from ..utils.validators import SafeDataProcessor


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    def generate_token(self, user_id: int, username: str, token_type: str = "access") -> str:
        """生成JWT令牌"""
        now = datetime.now(timezone.utc)
        if token_type == "access":
            expire = now + timedelta(minutes=self.access_token_expire_minutes)
        else:  # refresh token
            expire = now + timedelta(days=self.refresh_token_expire_days)
        
        to_encode = {
            "sub": str(user_id),
            "username": username,
            "type": token_type,
            "exp": expire,
            "iat": now
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: int = int(payload.get("sub"))
            username: str = payload.get("username")
            type_check: str = payload.get("type")
            
            if user_id is None or username is None or type_check != token_type:
                return None
            
            return TokenData(user_id=user_id, username=username)
        except jwt.PyJWTError:
            return None
    
    def generate_random_token(self, length: int = 32) -> str:
        """生成随机令牌"""
        return secrets.token_urlsafe(length)
    
    def register_user(self, db: Session, user_data: UserCreate) -> User:
        """用户注册"""
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 创建用户
        hashed_password = self.hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            avatar_url=user_data.avatar_url,
            bio=user_data.bio,
            company=user_data.company,
            department=user_data.department,
            position=user_data.position,
            status=UserStatus.INACTIVE  # 需要验证邮箱后激活
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 发送验证邮件
        self.send_verification_email(db, user)
        
        return user
    
    def authenticate_user(self, db: Session, login_data: UserLogin) -> Optional[User]:
        """用户认证"""
        # 支持用户名或邮箱登录
        user = db.query(User).filter(
            or_(
                User.username == login_data.username_or_email,
                User.email == login_data.username_or_email
            )
        ).first()
        
        if not user:
            return None
        
        if not self.verify_password(login_data.password, user.hashed_password):
            return None
        
        # 检查用户状态
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被暂停"
            )
        
        if user.status == UserStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        
        return user
    
    def create_tokens(self, user: User) -> Token:
        """创建访问令牌和刷新令牌"""
        access_token = self.generate_token(user.id, user.username, "access")
        refresh_token = self.generate_token(user.id, user.username, "refresh")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> Token:
        """刷新访问令牌"""
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return self.create_tokens(user)
    
    def change_password(self, db: Session, user: User, password_data: PasswordChange) -> bool:
        """修改密码"""
        if not self.verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码不正确"
            )
        
        # 更新密码
        user.hashed_password = self.hash_password(password_data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return True
    
    def create_password_reset_token(self, db: Session, email: str) -> bool:
        """创建密码重置令牌"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # 为了安全，即使邮箱不存在也返回成功
            return True
        
        # 删除之前的重置令牌
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).delete()
        
        # 创建新令牌
        token = self.generate_random_token(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)  # 1小时有效
        )
        
        db.add(reset_token)
        db.commit()
        
        # 发送重置邮件
        self.send_password_reset_email(user, token)
        
        return True
    
    def reset_password(self, db: Session, reset_data: PasswordReset) -> bool:
        """重置密码"""
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == reset_data.token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效或已过期的重置令牌"
            )
        
        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新密码
        user.hashed_password = self.hash_password(reset_data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        # 标记令牌为已使用
        reset_token.is_used = True
        reset_token.used_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True
    
    def send_verification_email(self, db: Session, user: User) -> bool:
        """发送邮箱验证邮件"""
        try:
            # 删除之前的验证令牌
            db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.is_verified == False
            ).delete()
            
            # 创建新令牌
            token = self.generate_random_token(32)
            verification_token = EmailVerificationToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # 7天有效
            )
            
            db.add(verification_token)
            db.commit()
            
            # 构建验证链接
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            # 发送邮件
            subject = "验证您的邮箱地址"
            body = f"""
            <html>
            <body>
            <h2>欢迎使用Qlib Web平台</h2>
            <p>Hi {user.full_name},</p>
            <p>请点击以下链接来验证您的邮箱地址：</p>
            <p><a href="{verification_url}">验证邮箱</a></p>
            <p>如果您无法点击链接，请复制以下URL到浏览器地址栏：</p>
            <p>{verification_url}</p>
            <p>此链接7天内有效。</p>
            <p>如果您没有注册账户，请忽略此邮件。</p>
            <br>
            <p>Qlib Web团队</p>
            </body>
            </html>
            """
            
            self._send_email(user.email, subject, body)
            return True
            
        except Exception as e:
            print(f"发送验证邮件失败: {e}")
            return False
    
    def verify_email(self, db: Session, token: str) -> bool:
        """验证邮箱"""
        verification_token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.is_verified == False,
            EmailVerificationToken.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not verification_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效或已过期的验证令牌"
            )
        
        user = db.query(User).filter(User.id == verification_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户状态
        user.status = UserStatus.ACTIVE
        user.is_email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        
        # 标记令牌为已验证
        verification_token.is_verified = True
        verification_token.verified_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True
    
    def send_password_reset_email(self, user: User, token: str) -> bool:
        """发送密码重置邮件"""
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            subject = "重置您的密码"
            body = f"""
            <html>
            <body>
            <h2>密码重置请求</h2>
            <p>Hi {user.full_name},</p>
            <p>我们收到了您的密码重置请求。请点击以下链接来重置您的密码：</p>
            <p><a href="{reset_url}">重置密码</a></p>
            <p>如果您无法点击链接，请复制以下URL到浏览器地址栏：</p>
            <p>{reset_url}</p>
            <p>此链接1小时内有效。</p>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
            <br>
            <p>Qlib Web团队</p>
            </body>
            </html>
            """
            
            self._send_email(user.email, subject, body)
            return True
            
        except Exception as e:
            print(f"发送密码重置邮件失败: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """发送邮件的通用方法"""
        try:
            # 这里应该配置实际的邮件服务器
            # 现在只是打印邮件内容用于测试
            print(f"发送邮件到 {to_email}")
            print(f"主题: {subject}")
            print(f"内容: {body}")
            return True
            
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False
    
    def create_session(self, db: Session, user: User, ip_address: str = None, 
                      user_agent: str = None) -> UserSession:
        """创建用户会话"""
        session_token = self.generate_random_token(64)
        
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        )
        
        db.add(session)
        db.commit()
        
        return session
    
    def get_current_user_from_token(self, db: Session, token: str) -> Optional[User]:
        """从令牌获取当前用户"""
        token_data = self.verify_token(token, "access")
        if not token_data:
            return None
        
        user = db.query(User).filter(User.id == token_data.user_id).first()
        return user


# 创建全局认证服务实例
auth_service = AuthService()
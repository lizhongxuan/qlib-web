"""
认证相关依赖项和中间件
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User, UserRole, UserStatus
from ..services.auth import auth_service
from ..schemas.user import TokenData


# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


class AuthDependency:
    """认证依赖项类"""
    
    def __init__(self, required: bool = True, roles: list = None):
        self.required = required
        self.roles = roles or []
    
    def __call__(self, 
                 credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                 db: Session = Depends(get_db)) -> Optional[User]:
        """认证依赖项"""
        
        if not credentials and not self.required:
            return None
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要认证",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 验证令牌
        token_data = auth_service.verify_token(credentials.credentials)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 获取用户
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
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
        
        if user.status == UserStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户未激活，请先验证邮箱"
            )
        
        # 检查角色权限
        if self.roles and user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return user


# 预定义的认证依赖项
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户（必须登录）"""
    return AuthDependency(required=True)(credentials, db)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选登录）"""
    return AuthDependency(required=False)(credentials, db)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前管理员用户"""
    return AuthDependency(required=True, roles=[UserRole.ADMIN])(credentials, db)


def get_current_manager_or_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前管理员或团队管理员用户"""
    return AuthDependency(required=True, roles=[UserRole.ADMIN, UserRole.MANAGER])(credentials, db)


def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前活跃用户"""
    user = AuthDependency(required=True)(credentials, db)
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )
    return user


class PermissionChecker:
    """权限检查器"""
    
    @staticmethod
    def can_access_experiment(user: User, experiment) -> bool:
        """检查用户是否可以访问实验"""
        # 管理员可以访问所有实验
        if user.role == UserRole.ADMIN:
            return True
        
        # 实验创建者可以访问
        if experiment.creator_id == user.id:
            return True
        
        # 团队成员可以访问团队实验（待实现团队实验功能）
        # TODO: 实现团队实验权限检查
        
        return False
    
    @staticmethod
    def can_modify_experiment(user: User, experiment) -> bool:
        """检查用户是否可以修改实验"""
        # 管理员可以修改所有实验
        if user.role == UserRole.ADMIN:
            return True
        
        # 实验创建者可以修改
        if experiment.creator_id == user.id:
            return True
        
        # 团队管理员可以修改团队实验（待实现）
        # TODO: 实现团队实验权限检查
        
        return False
    
    @staticmethod
    def can_delete_experiment(user: User, experiment) -> bool:
        """检查用户是否可以删除实验"""
        # 管理员可以删除所有实验
        if user.role == UserRole.ADMIN:
            return True
        
        # 实验创建者可以删除
        if experiment.creator_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_access_template(user: User, template) -> bool:
        """检查用户是否可以访问模板"""
        # 公开模板所有人都可以访问
        if template.is_public:
            return True
        
        # 管理员可以访问所有模板
        if user.role == UserRole.ADMIN:
            return True
        
        # 模板创建者可以访问
        if template.creator_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_modify_template(user: User, template) -> bool:
        """检查用户是否可以修改模板"""
        # 管理员可以修改所有模板
        if user.role == UserRole.ADMIN:
            return True
        
        # 模板创建者可以修改
        if template.creator_id == user.id:
            return True
        
        return False
    
    @staticmethod
    def can_manage_user(operator: User, target_user: User) -> bool:
        """检查是否可以管理目标用户"""
        # 管理员可以管理所有用户（除了自己的某些操作）
        if operator.role == UserRole.ADMIN:
            return True
        
        # 团队管理员可以管理团队成员（待实现）
        if operator.role == UserRole.MANAGER:
            # TODO: 实现团队管理权限检查
            pass
        
        return False
    
    @staticmethod
    def can_manage_team(user: User, team) -> bool:
        """检查是否可以管理团队"""
        # 管理员可以管理所有团队
        if user.role == UserRole.ADMIN:
            return True
        
        # 团队所有者可以管理
        if team.owner_id == user.id:
            return True
        
        return False


# 权限检查器实例
permission_checker = PermissionChecker()


def check_experiment_permission(permission_type: str = "access"):
    """实验权限检查装饰器"""
    def decorator(user: User = Depends(get_current_user)):
        def check_permission(experiment):
            if permission_type == "access":
                return permission_checker.can_access_experiment(user, experiment)
            elif permission_type == "modify":
                return permission_checker.can_modify_experiment(user, experiment)
            elif permission_type == "delete":
                return permission_checker.can_delete_experiment(user, experiment)
            return False
        return check_permission
    return decorator


def check_template_permission(permission_type: str = "access"):
    """模板权限检查装饰器"""
    def decorator(user: User = Depends(get_current_user)):
        def check_permission(template):
            if permission_type == "access":
                return permission_checker.can_access_template(user, template)
            elif permission_type == "modify":
                return permission_checker.can_modify_template(user, template)
            return False
        return check_permission
    return decorator


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """获取用户代理字符串"""
    return request.headers.get("User-Agent", "unknown")
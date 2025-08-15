"""
认证相关API端点
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user, get_client_ip, get_user_agent
from ...models.user import User
from ...schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, TokenApiResponse, UserApiResponse,
    PasswordChange, PasswordReset, EmailVerification, EmailResend
)
from ...services.auth import auth_service
from ...services.user import user_service

router = APIRouter()


@router.post("/register", response_model=UserApiResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    用户注册
    """
    try:
        user = auth_service.register_user(db, user_data)
        
        return UserApiResponse(
            success=True,
            message="注册成功，请检查邮箱并验证邮箱地址",
            data=UserResponse.from_orm(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=TokenApiResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    用户登录
    """
    try:
        user = auth_service.authenticate_user(db, user_credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误"
            )
        
        # 创建令牌
        tokens = auth_service.create_tokens(user)
        
        # 创建会话记录
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        auth_service.create_session(db, user, ip_address, user_agent)
        
        return TokenApiResponse(
            success=True,
            message="登录成功",
            data=tokens
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/refresh", response_model=TokenApiResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    刷新访问令牌
    """
    try:
        tokens = auth_service.refresh_access_token(db, refresh_token)
        return TokenApiResponse(
            success=True,
            message="令牌刷新成功",
            data=tokens
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    用户登出
    """
    # TODO: 实现令牌黑名单机制
    return {"success": True, "message": "登出成功"}


@router.get("/me", response_model=UserApiResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取当前用户信息
    """
    return UserApiResponse(
        success=True,
        message="获取用户信息成功",
        data=UserResponse.from_orm(current_user)
    )


@router.put("/me", response_model=UserApiResponse)
async def update_current_user(
    user_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新当前用户信息
    """
    try:
        # 过滤敏感字段
        allowed_fields = {'full_name', 'avatar_url', 'bio', 'company', 'department', 'position'}
        filtered_update = {k: v for k, v in user_update.items() if k in allowed_fields}
        
        if not filtered_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有有效的更新字段"
            )
        
        # 更新用户信息
        for field, value in filtered_update.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        current_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(current_user)
        
        return UserApiResponse(
            success=True,
            message="用户信息更新成功",
            data=UserResponse.from_orm(current_user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    修改密码
    """
    try:
        auth_service.change_password(db, current_user, password_data)
        return {"success": True, "message": "密码修改成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


@router.post("/forgot-password")
async def forgot_password(
    email_data: EmailResend,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    忘记密码
    """
    try:
        auth_service.create_password_reset_token(db, email_data.email)
        return {"success": True, "message": "密码重置邮件已发送"}
    except Exception as e:
        # 为了安全，即使邮箱不存在也返回成功
        return {"success": True, "message": "如果邮箱存在，密码重置邮件已发送"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    """
    重置密码
    """
    try:
        auth_service.reset_password(db, reset_data)
        return {"success": True, "message": "密码重置成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码重置失败: {str(e)}"
        )


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    db: Session = Depends(get_db)
) -> Any:
    """
    验证邮箱
    """
    try:
        auth_service.verify_email(db, verification_data.token)
        return {"success": True, "message": "邮箱验证成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"邮箱验证失败: {str(e)}"
        )


@router.post("/resend-verification")
async def resend_verification_email(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    重新发送验证邮件
    """
    try:
        if current_user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已验证"
            )
        
        auth_service.send_verification_email(db, current_user)
        return {"success": True, "message": "验证邮件已重新发送"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送验证邮件失败: {str(e)}"
        )


@router.get("/check-username/{username}")
async def check_username_availability(
    username: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    检查用户名是否可用
    """
    try:
        user = user_service.get_user_by_username(db, username)
        available = user is None
        
        return {
            "success": True,
            "data": {
                "username": username,
                "available": available,
                "message": "用户名可用" if available else "用户名已被占用"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户名失败: {str(e)}"
        )


@router.get("/check-email/{email}")
async def check_email_availability(
    email: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    检查邮箱是否可用
    """
    try:
        user = user_service.get_user_by_email(db, email)
        available = user is None
        
        return {
            "success": True,
            "data": {
                "email": email,
                "available": available,
                "message": "邮箱可用" if available else "邮箱已被注册"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查邮箱失败: {str(e)}"
        )


@router.get("/session-info")
async def get_session_info(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取会话信息
    """
    try:
        return {
            "success": True,
            "data": {
                "user_id": current_user.id,
                "username": current_user.username,
                "ip_address": get_client_ip(request),
                "user_agent": get_user_agent(request),
                "login_time": current_user.last_login_at.isoformat() if current_user.last_login_at else None
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话信息失败: {str(e)}"
        )
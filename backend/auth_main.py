#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import hashlib
import jwt
import os
from loguru import logger

# 配置
SECRET_KEY = "qlib-web-secret-key-for-development-only"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时

# 内存存储（生产环境应该用数据库）
fake_users_db: Dict[str, Dict[str, Any]] = {}

# 创建FastAPI应用
app = FastAPI(
    title="Qlib Web Console API with Auth",
    version="1.0.0",
    description="Qlib量化投资Web平台后端API - 带认证功能"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic模型
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

# 安全相关函数
security = HTTPBearer()

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(username: str) -> Optional[dict]:
    """根据用户名获取用户"""
    return fake_users_db.get(username)

def get_user_by_email(email: str) -> Optional[dict]:
    """根据邮箱获取用户"""
    for user in fake_users_db.values():
        if user["email"] == email:
            return user
    return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """获取当前用户"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = get_user_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 基础路由
@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "success": True,
        "message": "Welcome to Qlib Web Console API with Auth",
        "version": "1.0.0",
        "status": "running",
        "features": ["user_registration", "user_authentication", "jwt_tokens"]
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "users_count": len(fake_users_db)
    }

# 认证路由
@app.post("/api/v1/auth/register", response_model=Token)
async def register_user(user_data: UserRegister):
    """用户注册"""
    # 检查用户名是否已存在
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已存在
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建用户
    user_id = len(fake_users_db) + 1
    hashed_password = hash_password(user_data.password)
    
    user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    fake_users_db[user_data.username] = user
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": user_data.username})
    
    # 返回用户信息和令牌
    user_response = UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        is_active=user["is_active"],
        created_at=user["created_at"]
    )
    
    logger.info(f"User registered successfully: {user_data.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_response
    }

@app.post("/api/v1/auth/login", response_model=Token)
async def login_user(user_data: UserLogin):
    """用户登录"""
    user = get_user_by_username(user_data.username)
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": user["username"]})
    
    # 返回用户信息和令牌
    user_response = UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        is_active=user["is_active"],
        created_at=user["created_at"]
    )
    
    logger.info(f"User logged in successfully: {user_data.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_response
    }

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"]
    )

@app.post("/api/v1/auth/logout")
async def logout_user(current_user: dict = Depends(get_current_user)):
    """用户登出（在实际应用中可以将token加入黑名单）"""
    logger.info(f"User logged out: {current_user['username']}")
    return {
        "success": True,
        "message": "Successfully logged out"
    }

# 用户管理路由
@app.get("/api/v1/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user)):
    """获取用户列表（需要认证）"""
    users = []
    for user in fake_users_db.values():
        users.append(UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        ))
    return users

# API信息路由
@app.get("/api/v1/info")
async def api_info():
    """API信息"""
    return {
        "success": True,
        "message": "Qlib Web Console API with Authentication",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "register": "POST /api/v1/auth/register",
                "login": "POST /api/v1/auth/login", 
                "me": "GET /api/v1/auth/me",
                "logout": "POST /api/v1/auth/logout"
            },
            "users": {
                "list": "GET /api/v1/users"
            }
        },
        "total_users": len(fake_users_db)
    }

if __name__ == "__main__":
    logger.info("Starting Qlib Web Console API server with authentication...")
    uvicorn.run(
        "auth_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
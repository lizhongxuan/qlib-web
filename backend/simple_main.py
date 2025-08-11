#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timedelta
import uvicorn
import random

# 内存存储实验数据
fake_experiments_db = {}

# 创建FastAPI应用
app = FastAPI(
    title="Qlib Web Console API",
    version="1.0.0",
    description="Qlib量化投资Web平台后端API - 简化版本"
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
class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None

class DashboardSummary(BaseModel):
    totalExperiments: int = 0
    runningExperiments: int = 0
    completedExperiments: int = 0
    failedExperiments: int = 0

class ExperimentStatus(BaseModel):
    id: str
    name: str
    status: str
    progress: int
    createdAt: str
    completedAt: Optional[str] = None

# 初始化Mock数据
def init_mock_data():
    """初始化Mock数据"""
    statuses = ["pending", "running", "completed", "failed"]
    experiment_names = [
        "动量策略优化实验", "Alpha360多因子模型", "均值回归策略回测", 
        "LSTM价格预测模型", "风险平价组合优化", "成长价值轮动策略",
        "行业轮动策略", "市值因子分析", "技术指标组合策略", "量化择时模型"
    ]
    
    for i in range(1, 21):
        experiment_id = f"exp_{i:03d}"
        name = experiment_names[(i-1) % len(experiment_names)]
        status = random.choice(statuses)
        progress = 100 if status == "completed" else (random.randint(10, 90) if status == "running" else 0)
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        completed_at = created_at + timedelta(hours=random.randint(1, 24)) if status == "completed" else None
        
        fake_experiments_db[experiment_id] = {
            "id": experiment_id,
            "name": f"{name}_{i}",
            "status": status,
            "progress": progress,
            "created_at": created_at.isoformat(),
            "completed_at": completed_at.isoformat() if completed_at else None,
            "total_return": round(random.uniform(-0.2, 0.3), 4) if status == "completed" else None,
        }

@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "success": True,
        "message": "Welcome to Qlib Web Console API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "experiments_count": len(fake_experiments_db)
    }

# Dashboard路由
@app.get("/api/v1/dashboard/summary", response_model=APIResponse)
async def get_dashboard_summary():
    """获取仪表盘统计摘要"""
    try:
        total_experiments = len(fake_experiments_db)
        running_experiments = len([exp for exp in fake_experiments_db.values() if exp["status"] == "running"])
        completed_experiments = len([exp for exp in fake_experiments_db.values() if exp["status"] == "completed"])
        failed_experiments = len([exp for exp in fake_experiments_db.values() if exp["status"] == "failed"])
        
        summary = DashboardSummary(
            totalExperiments=total_experiments,
            runningExperiments=running_experiments,
            completedExperiments=completed_experiments,
            failedExperiments=failed_experiments
        )
        
        return APIResponse(success=True, data=summary)
    except Exception as e:
        return APIResponse(success=False, message=f"获取仪表盘摘要失败: {str(e)}")

@app.get("/api/v1/dashboard/recent", response_model=APIResponse)
async def get_recent_experiments():
    """获取最近的实验列表"""
    try:
        sorted_experiments = sorted(
            fake_experiments_db.values(), 
            key=lambda x: x["created_at"], 
            reverse=True
        )[:10]
        
        recent_experiments = [
            ExperimentStatus(
                id=exp["id"],
                name=exp["name"],
                status=exp["status"],
                progress=exp["progress"],
                createdAt=exp["created_at"],
                completedAt=exp["completed_at"]
            ) for exp in sorted_experiments
        ]
        
        return APIResponse(success=True, data=recent_experiments)
    except Exception as e:
        return APIResponse(success=False, message=f"获取最近实验失败: {str(e)}")

# 实验相关路由
@app.get("/api/v1/experiments", response_model=APIResponse)
async def get_experiments(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    status: Optional[str] = None
):
    """获取实验列表"""
    try:
        experiments = list(fake_experiments_db.values())
        
        if status:
            experiments = [exp for exp in experiments if exp["status"] == status]
        
        experiments.sort(key=lambda x: x["created_at"], reverse=True)
        
        total = len(experiments)
        start = (page - 1) * pageSize
        end = start + pageSize
        paginated_experiments = experiments[start:end]
        
        return APIResponse(
            success=True,
            data={
                "items": paginated_experiments,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "totalPages": (total + pageSize - 1) // pageSize
            }
        )
    except Exception as e:
        return APIResponse(success=False, message=f"获取实验列表失败: {str(e)}")

@app.get("/api/v1/experiments/{experiment_id}", response_model=APIResponse)
async def get_experiment_detail(experiment_id: str):
    """获取实验详情"""
    try:
        experiment = fake_experiments_db.get(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        experiment_detail = experiment.copy()
        experiment_detail.update({
            "description": f"这是{experiment['name']}的详细描述",
            "config": {"model": "LightGBM", "dataset": "CSI300"},
        })
        
        return APIResponse(success=True, data=experiment_detail)
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(success=False, message=f"获取实验详情失败: {str(e)}")

@app.get("/api/v1/experiments/{experiment_id}/performance", response_model=APIResponse)
async def get_experiment_performance(experiment_id: str):
    """获取实验性能数据"""
    try:
        experiment = fake_experiments_db.get(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        if experiment["status"] != "completed":
            return APIResponse(success=True, data={"message": "实验尚未完成"})
        
        # 生成模拟性能数据
        dates = []
        returns = []
        benchmark = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(30):
            dates.append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            returns.append(round(random.uniform(-0.03, 0.03), 4))
            benchmark.append(round(random.uniform(-0.02, 0.02), 4))
        
        performance_data = {
            "performance_metrics": {
                "daily_returns": [
                    {"date": date, "return": ret, "benchmark": bench}
                    for date, ret, bench in zip(dates, returns, benchmark)
                ]
            }
        }
        
        return APIResponse(success=True, data=performance_data)
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(success=False, message=f"获取性能数据失败: {str(e)}")

@app.get("/api/v1/experiments/{experiment_id}/positions", response_model=APIResponse)
async def get_experiment_positions(experiment_id: str):
    """获取实验持仓数据"""
    try:
        experiment = fake_experiments_db.get(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        if experiment["status"] != "completed":
            return APIResponse(success=True, data={"positions": []})
        
        stocks = ["000001.XSHE", "000002.XSHE", "600000.XSHG", "600036.XSHG"]
        positions = [
            {
                "symbol": stock,
                "name": f"股票{i+1}",
                "weight": round(random.uniform(0.05, 0.25), 4),
                "return": round(random.uniform(-0.1, 0.2), 4)
            }
            for i, stock in enumerate(stocks)
        ]
        
        return APIResponse(success=True, data={"positions": positions})
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(success=False, message=f"获取持仓数据失败: {str(e)}")

@app.get("/api/v1/experiments/{experiment_id}/logs", response_model=APIResponse)
async def get_experiment_logs(experiment_id: str):
    """获取实验日志"""
    try:
        experiment = fake_experiments_db.get(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        logs = [
            "开始执行实验...",
            "加载数据完成",
            "开始模型训练",
            "模型训练完成",
            "开始策略回测",
            "回测完成，生成报告",
            "实验执行完成" if experiment["status"] == "completed" else "实验执行中..."
        ]
        
        return APIResponse(success=True, data=logs)
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(success=False, message=f"获取日志失败: {str(e)}")

@app.delete("/api/v1/experiments/{experiment_id}", response_model=APIResponse)
async def delete_experiment(experiment_id: str):
    """删除实验"""
    try:
        if experiment_id not in fake_experiments_db:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        del fake_experiments_db[experiment_id]
        return APIResponse(success=True, message="实验删除成功")
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(success=False, message=f"删除实验失败: {str(e)}")

@app.post("/api/v1/experiments", response_model=APIResponse)
async def create_experiment(config: dict):
    """创建新实验"""
    try:
        experiment_id = f"exp_{len(fake_experiments_db) + 1:03d}"
        experiment = {
            "id": experiment_id,
            "name": config.get("name", "新实验"),
            "status": "pending",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "total_return": None,
            "config": config
        }
        
        fake_experiments_db[experiment_id] = experiment
        
        return APIResponse(success=True, data={"id": experiment_id}, message="实验创建成功")
    except Exception as e:
        return APIResponse(success=False, message=f"创建实验失败: {str(e)}")

# 认证相关API（简化版）
fake_users_db = {}

class UserData(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/api/v1/auth/register", response_model=APIResponse)
async def register(user_data: UserData):
    """用户注册"""
    try:
        if user_data.username in fake_users_db:
            return APIResponse(success=False, message="用户名已存在")
        
        user = {
            "id": len(fake_users_db) + 1,
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": "user",
            "created_at": datetime.utcnow().isoformat()
        }
        
        fake_users_db[user_data.username] = {
            **user,
            "password": user_data.password  # 实际应用中应该加密
        }
        
        return APIResponse(
            success=True,
            data={
                "access_token": "dummy_token_" + user_data.username,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": user
            },
            message="注册成功"
        )
    except Exception as e:
        return APIResponse(success=False, message=f"注册失败: {str(e)}")

@app.post("/api/v1/auth/login", response_model=APIResponse)
async def login(login_data: LoginData):
    """用户登录"""
    try:
        user_record = fake_users_db.get(login_data.username)
        
        if not user_record or user_record["password"] != login_data.password:
            return APIResponse(success=False, message="用户名或密码错误")
        
        user = {key: value for key, value in user_record.items() if key != "password"}
        
        return APIResponse(
            success=True,
            data={
                "access_token": "dummy_token_" + login_data.username,
                "token_type": "bearer", 
                "expires_in": 3600,
                "user": user
            },
            message="登录成功"
        )
    except Exception as e:
        return APIResponse(success=False, message=f"登录失败: {str(e)}")

@app.get("/api/v1/auth/me", response_model=APIResponse)
async def get_current_user():
    """获取当前用户信息"""
    # 简化版本，返回默认用户
    user = {
        "id": 1,
        "username": "guest",
        "email": "guest@example.com",
        "full_name": "Guest User",
        "role": "user"
    }
    return APIResponse(success=True, data=user)

@app.post("/api/v1/auth/logout", response_model=APIResponse)
async def logout():
    """用户登出"""
    return APIResponse(success=True, message="登出成功")

# 启动时初始化数据
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("初始化Mock数据...")
    init_mock_data()
    print(f"已创建 {len(fake_experiments_db)} 个Mock实验")

if __name__ == "__main__":
    print("启动Qlib Web Console API服务器...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
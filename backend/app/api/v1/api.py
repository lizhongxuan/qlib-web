from fastapi import APIRouter

from app.api.v1.endpoints import experiments, dashboard, config, backup, templates, websocket, recommendations, factors, workflow, training, deployment
from app.api.v1 import auth, users, team_experiments, shares, comments

api_router = APIRouter()

# 包含各个模块的路由
# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(team_experiments.router, prefix="/teams", tags=["team-experiments"])
api_router.include_router(shares.router, prefix="/shares", tags=["shares"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])

# 业务功能路由  
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"]) 
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(backup.router, prefix="/backup", tags=["backup"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(factors.router, prefix="/factors", tags=["factors"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(deployment.router, prefix="/deployment", tags=["deployment"])
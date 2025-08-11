from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_user_optional, permission_checker
from app.models.experiment import Experiment
from app.models.user import User
from app.schemas.experiment import (
    ExperimentCreate, 
    ExperimentUpdate,
    ExperimentResponse, 
    ExperimentSummary,
    ExperimentLogResponse
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.experiment_service import ExperimentService
from app.utils.experiment_runner import ExperimentRunner

router = APIRouter()

# 初始化服务
experiment_service = ExperimentService()
experiment_runner = ExperimentRunner()


@router.post("", response_model=APIResponse[dict])
async def create_experiment(
    experiment: ExperimentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新实验"""
    try:
        # 生成实验ID
        experiment_id = str(uuid.uuid4())
        
        # 创建实验记录
        db_experiment = Experiment(
            id=experiment_id,
            name=experiment.name,
            description=experiment.description,
            config=experiment.config.dict(),
            tags=experiment.tags,
            status="pending",
            creator_id=current_user.id  # 关联创建者
        )
        
        db.add(db_experiment)
        db.commit()
        db.refresh(db_experiment)
        
        # 在后台运行实验
        background_tasks.add_task(
            run_experiment_task,
            experiment_id,
            experiment.config.dict(),
            db
        )
        
        return APIResponse(
            success=True,
            data={"id": experiment_id},
            message="实验创建成功，正在后台执行"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=APIResponse[PaginatedResponse[ExperimentSummary]])
async def get_experiments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取实验列表"""
    try:
        experiments, total = await experiment_service.get_experiments(
            db=db,
            page=page,
            page_size=page_size,
            status=status,
            search=search,
            user_id=current_user.id if current_user else None  # 根据用户过滤实验
        )
        
        experiment_summaries = [
            ExperimentSummary(**exp.to_summary_dict()) 
            for exp in experiments
        ]
        
        return APIResponse(
            success=True,
            data=PaginatedResponse(
                items=experiment_summaries,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}", response_model=APIResponse[ExperimentResponse])
async def get_experiment(
    experiment_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取实验详情"""
    try:
        experiment = await experiment_service.get_experiment(db, experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        # 检查访问权限
        if current_user and not permission_checker.can_access_experiment(current_user, experiment):
            raise HTTPException(status_code=403, detail="权限不足")
        
        return APIResponse(
            success=True,
            data=ExperimentResponse(**experiment.to_dict())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{experiment_id}", response_model=APIResponse[ExperimentResponse])
async def update_experiment(
    experiment_id: str,
    experiment_update: ExperimentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新实验"""
    try:
        # 先获取实验以检查权限
        experiment = await experiment_service.get_experiment(db, experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        # 检查修改权限
        if not permission_checker.can_modify_experiment(current_user, experiment):
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 执行更新
        updated_experiment = await experiment_service.update_experiment(
            db, experiment_id, experiment_update
        )
        
        return APIResponse(
            success=True,
            data=ExperimentResponse(**updated_experiment.to_dict()),
            message="实验更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{experiment_id}", response_model=APIResponse[dict])
async def delete_experiment(
    experiment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除实验"""
    try:
        # 先获取实验以检查权限
        experiment = await experiment_service.get_experiment(db, experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        # 检查删除权限
        if not permission_checker.can_delete_experiment(current_user, experiment):
            raise HTTPException(status_code=403, detail="权限不足")
        
        success = await experiment_service.delete_experiment(db, experiment_id)
        if not success:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        return APIResponse(
            success=True,
            data={"deleted": True},
            message="实验删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}/performance", response_model=APIResponse[dict])
async def get_experiment_performance(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """获取实验性能数据"""
    try:
        performance_data = await experiment_service.get_performance_data(
            db, experiment_id
        )
        if not performance_data:
            raise HTTPException(status_code=404, detail="实验不存在或尚无性能数据")
        
        return APIResponse(
            success=True,
            data=performance_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}/positions", response_model=APIResponse[dict])
async def get_experiment_positions(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """获取实验持仓数据"""
    try:
        positions_data = await experiment_service.get_positions_data(
            db, experiment_id
        )
        if not positions_data:
            raise HTTPException(status_code=404, detail="实验不存在或尚无持仓数据")
        
        return APIResponse(
            success=True,
            data=positions_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}/logs", response_model=APIResponse[ExperimentLogResponse])
async def get_experiment_logs(
    experiment_id: str,
    lines: int = Query(100, ge=1, le=1000, description="获取日志行数"),
    db: Session = Depends(get_db)
):
    """获取实验执行日志"""
    try:
        logs_data = await experiment_service.get_experiment_logs(
            db, experiment_id, lines
        )
        if not logs_data:
            raise HTTPException(status_code=404, detail="实验不存在或尚无日志数据")
        
        return APIResponse(
            success=True,
            data=logs_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{experiment_id}/cancel", response_model=APIResponse[dict])
async def cancel_experiment(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """取消正在运行的实验"""
    try:
        success = await experiment_service.cancel_experiment(db, experiment_id)
        if not success:
            raise HTTPException(status_code=404, detail="实验不存在或无法取消")
        
        return APIResponse(
            success=True,
            data={"cancelled": True},
            message="实验取消成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 后台任务函数
async def run_experiment_task(
    experiment_id: str, 
    config: dict, 
    db: Session
):
    """在后台运行实验的任务函数"""
    from loguru import logger
    
    try:
        logger.info(f"Starting experiment task: {experiment_id}")
        
        # 更新实验状态为运行中
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if experiment:
            experiment.status = "running"
            experiment.started_at = datetime.utcnow()
            experiment.progress = 0
            db.commit()
        
        # 定义进度回调函数
        async def progress_callback(progress: int, message: str = ""):
            nonlocal experiment
            if experiment:
                experiment.progress = progress
                if message:
                    experiment.error_message = message  # 临时用于存储进度消息
                db.commit()
        
        # 运行回测
        results = await experiment_runner.run_backtest(
            experiment_id, config, progress_callback
        )
        
        # 更新实验结果
        if experiment:
            experiment.status = "completed"
            experiment.completed_at = datetime.utcnow()
            experiment.progress = 100
            experiment.results = results
            experiment.error_message = None
            
            # 提取关键指标
            if "performance" in results:
                perf = results["performance"]
                experiment.total_return = perf.get("total_return")
                experiment.annual_return = perf.get("annual_return")
                experiment.sharpe_ratio = perf.get("sharpe_ratio")
                experiment.max_drawdown = perf.get("max_drawdown")
                experiment.volatility = perf.get("volatility")
            
            db.commit()
            
        logger.success(f"Experiment task completed: {experiment_id}")
        
    except Exception as e:
        logger.error(f"Experiment task failed: {experiment_id} - {e}")
        
        # 更新实验状态为失败
        if experiment:
            experiment.status = "failed"
            experiment.completed_at = datetime.utcnow()
            experiment.error_message = str(e)
            db.commit()
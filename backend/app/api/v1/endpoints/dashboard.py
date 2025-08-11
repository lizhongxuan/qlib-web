from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.experiment import Experiment
from app.schemas.common import APIResponse, DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=APIResponse[DashboardSummary])
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """获取仪表盘统计摘要"""
    try:
        # 查询实验统计数据
        total_experiments = db.query(func.count(Experiment.id)).filter(
            Experiment.is_deleted == False
        ).scalar() or 0
        
        running_experiments = db.query(func.count(Experiment.id)).filter(
            Experiment.status == "running",
            Experiment.is_deleted == False
        ).scalar() or 0
        
        completed_experiments = db.query(func.count(Experiment.id)).filter(
            Experiment.status == "completed",
            Experiment.is_deleted == False
        ).scalar() or 0
        
        failed_experiments = db.query(func.count(Experiment.id)).filter(
            Experiment.status == "failed",
            Experiment.is_deleted == False
        ).scalar() or 0
        
        pending_experiments = db.query(func.count(Experiment.id)).filter(
            Experiment.status == "pending",
            Experiment.is_deleted == False
        ).scalar() or 0
        
        # 获取最近的实验
        recent_experiments = db.query(Experiment).filter(
            Experiment.is_deleted == False
        ).order_by(
            Experiment.created_at.desc()
        ).limit(5).all()
        
        recent_experiments_data = [
            {
                "id": exp.id,
                "name": exp.name,
                "status": exp.status,
                "progress": exp.progress,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "total_return": exp.total_return,
                "sharpe_ratio": exp.sharpe_ratio
            }
            for exp in recent_experiments
        ]
        
        # 系统状态（模拟数据）
        import psutil
        import os
        
        system_status = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "queue_size": running_experiments + pending_experiments  # 简化的队列大小
        }
        
        summary = DashboardSummary(
            total_experiments=total_experiments,
            running_experiments=running_experiments,
            completed_experiments=completed_experiments,
            failed_experiments=failed_experiments,
            pending_experiments=pending_experiments,
            recent_experiments=recent_experiments_data,
            system_status=system_status
        )
        
        return APIResponse(
            success=True,
            data=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=APIResponse[list])
async def get_recent_experiments(db: Session = Depends(get_db)):
    """获取最近的实验列表"""
    try:
        recent_experiments = db.query(Experiment).filter(
            Experiment.is_deleted == False
        ).order_by(
            Experiment.created_at.desc()
        ).limit(10).all()
        
        experiments_data = [exp.to_summary_dict() for exp in recent_experiments]
        
        return APIResponse(
            success=True,
            data=experiments_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=APIResponse[dict])
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取详细统计数据"""
    try:
        # 按状态统计
        status_stats = db.query(
            Experiment.status,
            func.count(Experiment.id).label('count')
        ).filter(
            Experiment.is_deleted == False
        ).group_by(Experiment.status).all()
        
        status_distribution = {stat.status: stat.count for stat in status_stats}
        
        # 按日期统计（最近30天）
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        daily_stats = db.query(
            func.date(Experiment.created_at).label('date'),
            func.count(Experiment.id).label('count')
        ).filter(
            and_(
                Experiment.created_at >= thirty_days_ago,
                Experiment.is_deleted == False
            )
        ).group_by(
            func.date(Experiment.created_at)
        ).order_by(
            func.date(Experiment.created_at)
        ).all()
        
        daily_distribution = [
            {
                "date": stat.date.isoformat() if stat.date else None,
                "count": stat.count
            }
            for stat in daily_stats
        ]
        
        # 成功率统计
        total_completed = status_distribution.get("completed", 0) + status_distribution.get("failed", 0)
        success_rate = (status_distribution.get("completed", 0) / total_completed * 100) if total_completed > 0 else 0
        
        # 平均执行时间
        completed_experiments = db.query(Experiment).filter(
            Experiment.status == "completed",
            Experiment.started_at.isnot(None),
            Experiment.completed_at.isnot(None),
            Experiment.is_deleted == False
        ).all()
        
        if completed_experiments:
            execution_times = [
                (exp.completed_at - exp.started_at).total_seconds()
                for exp in completed_experiments
                if exp.completed_at and exp.started_at
            ]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        else:
            avg_execution_time = 0
        
        stats_data = {
            "status_distribution": status_distribution,
            "daily_distribution": daily_distribution,
            "success_rate": round(success_rate, 2),
            "avg_execution_time_seconds": round(avg_execution_time, 2),
            "total_experiments": sum(status_distribution.values()),
            "active_experiments": status_distribution.get("running", 0) + status_distribution.get("pending", 0)
        }
        
        return APIResponse(
            success=True,
            data=stats_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
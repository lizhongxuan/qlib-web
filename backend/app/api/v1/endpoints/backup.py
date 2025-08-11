from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.backup_service import BackupService
from app.schemas.backup import (
    BackupResponse,
    BackupListResponse,
    BackupCreateRequest,
    BackupRestoreResponse
)

router = APIRouter()
backup_service = BackupService()


@router.post("/full", response_model=BackupResponse)
async def create_full_backup(
    request: BackupCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建完整系统备份"""
    try:
        backup_info = await backup_service.create_full_backup(
            db=db, 
            description=request.description or ""
        )
        return BackupResponse(**backup_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")


@router.post("/experiment/{experiment_id}", response_model=BackupResponse)
async def create_experiment_backup(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """创建单个实验备份"""
    try:
        backup_info = await backup_service.create_experiment_backup(
            db=db, 
            experiment_id=experiment_id
        )
        return BackupResponse(**backup_info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建实验备份失败: {str(e)}")


@router.get("", response_model=BackupListResponse)
async def list_backups():
    """获取备份列表"""
    try:
        backups = await backup_service.list_backups()
        return BackupListResponse(backups=backups, total=len(backups))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


@router.post("/{backup_name}/restore", response_model=BackupRestoreResponse)
async def restore_backup(
    backup_name: str,
    db: Session = Depends(get_db)
):
    """恢复备份"""
    try:
        restore_info = await backup_service.restore_backup(
            backup_name=backup_name,
            db=db
        )
        return BackupRestoreResponse(**restore_info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")


@router.delete("/{backup_name}")
async def delete_backup(backup_name: str):
    """删除备份"""
    try:
        success = await backup_service.delete_backup(backup_name)
        if not success:
            raise HTTPException(status_code=404, detail="备份文件不存在")
        return {"message": "备份删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class BackupCreateRequest(BaseModel):
    """创建备份请求"""
    description: Optional[str] = None


class BackupResponse(BaseModel):
    """备份响应"""
    backup_name: str
    backup_path: str
    backup_size: int
    created_at: str
    description: Optional[str] = None
    experiment_id: Optional[str] = None
    experiment_name: Optional[str] = None


class BackupListItem(BaseModel):
    """备份列表项"""
    backup_name: str
    backup_path: str
    backup_type: str
    file_size: int
    created_at: str
    description: Optional[str] = None
    experiment_id: Optional[str] = None
    experiment_name: Optional[str] = None


class BackupListResponse(BaseModel):
    """备份列表响应"""
    backups: List[BackupListItem]
    total: int


class BackupRestoreResponse(BaseModel):
    """备份恢复响应"""
    experiment_id: Optional[str] = None
    experiment_name: Optional[str] = None
    restored_experiments: Optional[int] = None
    errors: Optional[List[str]] = None
    restored_at: str
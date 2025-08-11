import os
import json
import shutil
import tarfile
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.experiment import Experiment
from app.core.database import get_db


class BackupService:
    """数据备份服务"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_PATH or "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_full_backup(self, db: Session, description: str = "") -> Dict[str, Any]:
        """创建完整备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"full_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 备份数据库数据
            db_backup_path = backup_path / "database"
            await self._backup_database(db, db_backup_path)
            
            # 备份实验结果文件
            files_backup_path = backup_path / "experiment_files"
            await self._backup_experiment_files(db, files_backup_path)
            
            # 创建备份元信息
            metadata = {
                "backup_name": backup_name,
                "backup_type": "full",
                "created_at": timestamp,
                "description": description,
                "database_backup": str(db_backup_path),
                "files_backup": str(files_backup_path),
                "backup_size": self._calculate_directory_size(backup_path)
            }
            
            # 保存元信息
            with open(backup_path / "backup_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 压缩备份
            archive_path = await self._compress_backup(backup_path)
            
            # 清理临时目录
            shutil.rmtree(backup_path)
            
            return {
                "backup_name": backup_name,
                "backup_path": str(archive_path),
                "backup_size": archive_path.stat().st_size,
                "created_at": timestamp,
                "description": description
            }
            
        except FileNotFoundError as e:
            # 清理失败的备份
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise ValueError(f"备份路径不存在: {str(e)}")
        except PermissionError as e:
            # 清理失败的备份
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise PermissionError(f"备份路径权限不足: {str(e)}")
        except OSError as e:
            # 清理失败的备份
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise OSError(f"文件系统操作失败: {str(e)}")
        except Exception as e:
            # 清理失败的备份
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise RuntimeError(f"备份创建失败: {str(e)}")
    
    async def create_experiment_backup(self, db: Session, experiment_id: str) -> Dict[str, Any]:
        """创建单个实验的备份"""
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"实验 {experiment_id} 不存在")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"experiment_{experiment_id[:8]}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 备份实验数据
            experiment_data = {
                "id": experiment.id,
                "name": experiment.name,
                "description": experiment.description,
                "config": experiment.config,
                "results": experiment.results,
                "status": experiment.status,
                "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
                "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None,
                "error_message": experiment.error_message
            }
            
            with open(backup_path / "experiment_data.json", "w", encoding="utf-8") as f:
                json.dump(experiment_data, f, indent=2, ensure_ascii=False)
            
            # 备份实验结果文件
            if experiment.results and experiment.results.get("artifacts_path"):
                artifacts_path = Path(experiment.results["artifacts_path"])
                if artifacts_path.exists():
                    dest_path = backup_path / "artifacts"
                    shutil.copytree(artifacts_path, dest_path)
            
            # 创建备份元信息
            metadata = {
                "backup_name": backup_name,
                "backup_type": "experiment",
                "experiment_id": experiment_id,
                "experiment_name": experiment.name,
                "created_at": timestamp,
                "backup_size": self._calculate_directory_size(backup_path)
            }
            
            with open(backup_path / "backup_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 压缩备份
            archive_path = await self._compress_backup(backup_path)
            
            # 清理临时目录
            shutil.rmtree(backup_path)
            
            return {
                "backup_name": backup_name,
                "backup_path": str(archive_path),
                "backup_size": archive_path.stat().st_size,
                "experiment_id": experiment_id,
                "experiment_name": experiment.name,
                "created_at": timestamp
            }
            
        except Exception as e:
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise Exception(f"实验备份创建失败: {str(e)}")
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            try:
                # 提取备份文件获取元信息
                with tarfile.open(backup_file, "r:gz") as tar:
                    try:
                        metadata_file = tar.extractfile("backup_metadata.json")
                        if metadata_file:
                            metadata = json.loads(metadata_file.read().decode("utf-8"))
                            metadata["backup_path"] = str(backup_file)
                            metadata["file_size"] = backup_file.stat().st_size
                            backups.append(metadata)
                    except:
                        # 如果无法读取元信息，创建基本信息
                        stat = backup_file.stat()
                        backups.append({
                            "backup_name": backup_file.stem.replace(".tar", ""),
                            "backup_path": str(backup_file),
                            "file_size": stat.st_size,
                            "created_at": datetime.fromtimestamp(stat.st_ctime).strftime("%Y%m%d_%H%M%S"),
                            "backup_type": "unknown"
                        })
            except Exception:
                continue
        
        # 按创建时间倒序排列
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups
    
    async def restore_backup(self, backup_name: str, db: Session) -> Dict[str, Any]:
        """恢复备份"""
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        if not backup_file.exists():
            raise ValueError(f"备份文件 {backup_name} 不存在")
        
        restore_dir = self.backup_dir / f"restore_{backup_name}"
        restore_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 解压备份文件
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(restore_dir)
            
            # 读取备份元信息
            metadata_file = restore_dir / "backup_metadata.json"
            if not metadata_file.exists():
                raise ValueError("备份元信息文件不存在")
            
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            if metadata["backup_type"] == "experiment":
                return await self._restore_experiment_backup(restore_dir, db, metadata)
            elif metadata["backup_type"] == "full":
                return await self._restore_full_backup(restore_dir, db, metadata)
            else:
                raise ValueError(f"不支持的备份类型: {metadata['backup_type']}")
                
        except Exception as e:
            raise Exception(f"备份恢复失败: {str(e)}")
        finally:
            # 清理临时目录
            if restore_dir.exists():
                shutil.rmtree(restore_dir)
    
    async def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        if backup_file.exists():
            backup_file.unlink()
            return True
        return False
    
    async def _backup_database(self, db: Session, backup_path: Path):
        """备份数据库数据"""
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 备份实验数据
        experiments = db.query(Experiment).filter(Experiment.is_deleted == False).all()
        experiments_data = []
        
        for exp in experiments:
            exp_data = {
                "id": exp.id,
                "name": exp.name,
                "description": exp.description,
                "config": exp.config,
                "results": exp.results,
                "status": exp.status,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
                "error_message": exp.error_message,
                "is_deleted": exp.is_deleted
            }
            experiments_data.append(exp_data)
        
        with open(backup_path / "experiments.json", "w", encoding="utf-8") as f:
            json.dump(experiments_data, f, indent=2, ensure_ascii=False)
    
    async def _backup_experiment_files(self, db: Session, backup_path: Path):
        """备份实验结果文件"""
        backup_path.mkdir(parents=True, exist_ok=True)
        
        experiments = db.query(Experiment).filter(Experiment.is_deleted == False).all()
        
        for exp in experiments:
            if exp.results and exp.results.get("artifacts_path"):
                artifacts_path = Path(exp.results["artifacts_path"])
                if artifacts_path.exists():
                    dest_path = backup_path / exp.id
                    shutil.copytree(artifacts_path, dest_path)
    
    async def _compress_backup(self, backup_path: Path) -> Path:
        """压缩备份目录"""
        archive_path = backup_path.with_suffix(".tar.gz")
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        return archive_path
    
    async def _restore_experiment_backup(self, restore_dir: Path, db: Session, metadata: Dict) -> Dict[str, Any]:
        """恢复单个实验备份"""
        experiment_file = restore_dir / "experiment_data.json"
        if not experiment_file.exists():
            raise ValueError("实验数据文件不存在")
        
        with open(experiment_file, "r", encoding="utf-8") as f:
            exp_data = json.load(f)
        
        # 检查实验是否已存在
        existing_exp = db.query(Experiment).filter(Experiment.id == exp_data["id"]).first()
        if existing_exp:
            raise ValueError(f"实验 {exp_data['id']} 已存在")
        
        # 创建新实验
        new_experiment = Experiment(
            id=exp_data["id"],
            name=exp_data["name"],
            description=exp_data["description"],
            config=exp_data["config"],
            results=exp_data["results"],
            status=exp_data["status"],
            error_message=exp_data.get("error_message"),
            is_deleted=False
        )
        
        # 设置时间戳
        if exp_data.get("created_at"):
            new_experiment.created_at = datetime.fromisoformat(exp_data["created_at"])
        if exp_data.get("completed_at"):
            new_experiment.completed_at = datetime.fromisoformat(exp_data["completed_at"])
        if exp_data.get("updated_at"):
            new_experiment.updated_at = datetime.fromisoformat(exp_data["updated_at"])
        
        db.add(new_experiment)
        
        # 恢复实验结果文件
        artifacts_dir = restore_dir / "artifacts"
        if artifacts_dir.exists():
            dest_artifacts_path = Path(settings.EXPERIMENTS_PATH) / exp_data["id"]
            if dest_artifacts_path.exists():
                shutil.rmtree(dest_artifacts_path)
            shutil.copytree(artifacts_dir, dest_artifacts_path)
        
        db.commit()
        
        return {
            "experiment_id": exp_data["id"],
            "experiment_name": exp_data["name"],
            "restored_at": datetime.now().isoformat()
        }
    
    async def _restore_full_backup(self, restore_dir: Path, db: Session, metadata: Dict) -> Dict[str, Any]:
        """恢复完整备份"""
        # 这是一个危险操作，需要谨慎处理
        experiments_file = restore_dir / "database" / "experiments.json"
        if not experiments_file.exists():
            raise ValueError("数据库备份文件不存在")
        
        with open(experiments_file, "r", encoding="utf-8") as f:
            experiments_data = json.load(f)
        
        restored_count = 0
        errors = []
        
        for exp_data in experiments_data:
            try:
                # 检查实验是否已存在
                existing_exp = db.query(Experiment).filter(Experiment.id == exp_data["id"]).first()
                if existing_exp:
                    continue  # 跳过已存在的实验
                
                # 创建新实验
                new_experiment = Experiment(
                    id=exp_data["id"],
                    name=exp_data["name"],
                    description=exp_data["description"],
                    config=exp_data["config"],
                    results=exp_data["results"],
                    status=exp_data["status"],
                    error_message=exp_data.get("error_message"),
                    is_deleted=exp_data.get("is_deleted", False)
                )
                
                # 设置时间戳
                if exp_data.get("created_at"):
                    new_experiment.created_at = datetime.fromisoformat(exp_data["created_at"])
                if exp_data.get("completed_at"):
                    new_experiment.completed_at = datetime.fromisoformat(exp_data["completed_at"])
                if exp_data.get("updated_at"):
                    new_experiment.updated_at = datetime.fromisoformat(exp_data["updated_at"])
                
                db.add(new_experiment)
                restored_count += 1
                
            except Exception as e:
                errors.append(f"实验 {exp_data.get('id', 'unknown')}: {str(e)}")
        
        # 恢复实验文件
        files_backup_dir = restore_dir / "experiment_files"
        if files_backup_dir.exists():
            experiments_path = Path(settings.EXPERIMENTS_PATH)
            for exp_dir in files_backup_dir.iterdir():
                if exp_dir.is_dir():
                    dest_path = experiments_path / exp_dir.name
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(exp_dir, dest_path)
        
        db.commit()
        
        return {
            "restored_experiments": restored_count,
            "errors": errors,
            "restored_at": datetime.now().isoformat()
        }
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """计算目录大小"""
        total_size = 0
        for path in directory.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
        return total_size
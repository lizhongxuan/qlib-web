"""
测试业务服务层
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import shutil
from datetime import datetime

from app.services.experiment_service import ExperimentService
from app.services.backup_service import BackupService
from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentUpdate, ExperimentLogResponse


class TestExperimentService:
    """测试实验服务"""
    
    @pytest.fixture
    def experiment_service(self):
        """创建实验服务实例"""
        return ExperimentService()
    
    @pytest.fixture
    def mock_experiment(self):
        """创建模拟实验对象"""
        experiment = Mock(spec=Experiment)
        experiment.id = "test-exp-123"
        experiment.name = "测试实验"
        experiment.status = "completed"
        experiment.results = {
            "performance": {
                "total_return": 0.156,
                "annual_return": 0.078,
                "sharpe_ratio": 1.25
            },
            "positions": [
                {
                    "symbol": "000001.SZ",
                    "date": "2020-01-01",
                    "weight": 0.1,
                    "return": 0.02
                }
            ]
        }
        experiment.created_at = datetime.now()
        experiment.updated_at = datetime.now()
        return experiment
    
    @pytest.mark.asyncio
    async def test_get_experiments(self, experiment_service, db_session):
        """测试获取实验列表"""
        # 模拟数据库查询
        with patch.object(db_session, 'query') as mock_query:
            mock_filter = Mock()
            mock_query.return_value.filter.return_value = mock_filter
            mock_filter.count.return_value = 5
            
            mock_experiments = [Mock(spec=Experiment) for _ in range(3)]
            mock_filter.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_experiments
            
            experiments, total = await experiment_service.get_experiments(
                db=db_session,
                page=1,
                page_size=3,
                status="completed"
            )
            
            assert total == 5
            assert len(experiments) == 3
            # 验证查询条件
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_experiment(self, experiment_service, db_session, mock_experiment):
        """测试获取单个实验"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_experiment
            
            result = await experiment_service.get_experiment(db_session, "test-exp-123")
            
            assert result == mock_experiment
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_experiment_not_found(self, experiment_service, db_session):
        """测试获取不存在的实验"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            result = await experiment_service.get_experiment(db_session, "non-existent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_experiment(self, experiment_service, db_session, mock_experiment):
        """测试更新实验"""
        update_data = ExperimentUpdate(
            name="更新后的实验名称",
            description="更新后的描述"
        )
        
        with patch.object(experiment_service, 'get_experiment') as mock_get:
            mock_get.return_value = mock_experiment
            
            result = await experiment_service.update_experiment(
                db_session, "test-exp-123", update_data
            )
            
            assert result == mock_experiment
            assert mock_experiment.name == "更新后的实验名称"
            db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_experiment(self, experiment_service, db_session, mock_experiment):
        """测试删除实验"""
        with patch.object(experiment_service, 'get_experiment') as mock_get:
            mock_get.return_value = mock_experiment
            
            result = await experiment_service.delete_experiment(db_session, "test-exp-123")
            
            assert result is True
            assert mock_experiment.is_deleted is True
            db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_performance_data(self, experiment_service, db_session, mock_experiment):
        """测试获取性能数据"""
        with patch.object(experiment_service, 'get_experiment') as mock_get:
            mock_get.return_value = mock_experiment
            
            result = await experiment_service.get_performance_data(
                db_session, "test-exp-123"
            )
            
            assert result is not None
            assert "performance_metrics" in result
            assert "performance_curve" in result
            assert "benchmark_comparison" in result
            assert result["experiment_id"] == "test-exp-123"
    
    @pytest.mark.asyncio
    async def test_get_positions_data(self, experiment_service, db_session, mock_experiment):
        """测试获取持仓数据"""
        with patch.object(experiment_service, 'get_experiment') as mock_get:
            mock_get.return_value = mock_experiment
            
            result = await experiment_service.get_positions_data(
                db_session, "test-exp-123"
            )
            
            assert result is not None
            assert "positions" in result
            assert "position_summary" in result
            assert "turnover_analysis" in result
            assert result["experiment_id"] == "test-exp-123"
    
    @pytest.mark.asyncio
    async def test_get_experiment_logs(self, experiment_service, db_session, mock_experiment):
        """测试获取实验日志"""
        mock_experiment.status = "completed"
        
        with patch.object(experiment_service, 'get_experiment') as mock_get:
            mock_get.return_value = mock_experiment
            
            result = await experiment_service.get_experiment_logs(
                db_session, "test-exp-123", lines=50
            )
            
            assert isinstance(result, ExperimentLogResponse)
            assert result.experiment_id == "test-exp-123"
            assert len(result.logs) > 0
            assert len(result.logs) <= 50
    
    def test_calculate_position_summary(self, experiment_service):
        """测试持仓摘要计算"""
        positions = [
            {"symbol": "000001.SZ", "weight": 0.1, "return": 0.02, "date": "2020-01-01"},
            {"symbol": "000001.SZ", "weight": 0.12, "return": 0.03, "date": "2020-01-02"},
            {"symbol": "000002.SZ", "weight": 0.08, "return": -0.01, "date": "2020-01-01"},
        ]
        
        result = experiment_service._calculate_position_summary(positions)
        
        assert result["total_stocks"] == 2
        assert len(result["stock_details"]) == 2
        assert "concentration" in result
        
        # 检查000001.SZ的统计
        stock_001 = next(s for s in result["stock_details"] if s["symbol"] == "000001.SZ")
        assert stock_001["days_held"] == 2
        assert stock_001["total_weight"] == 0.22
        assert stock_001["avg_weight"] == 0.11
    
    def test_calculate_turnover_analysis(self, experiment_service):
        """测试换手率分析计算"""
        positions = [
            {"symbol": "000001.SZ", "weight": 0.1, "date": "2020-01-01"},
            {"symbol": "000002.SZ", "weight": 0.15, "date": "2020-01-01"},
            {"symbol": "000001.SZ", "weight": 0.12, "date": "2020-01-02"},
            {"symbol": "000003.SZ", "weight": 0.13, "date": "2020-01-02"},
        ]
        
        result = experiment_service._calculate_turnover_analysis(positions)
        
        assert "daily_turnovers" in result
        assert "average_turnover" in result
        assert "total_trading_days" in result
        assert len(result["daily_turnovers"]) == 1  # 两天数据，一个换手率


class TestBackupService:
    """测试备份服务"""
    
    @pytest.fixture
    def backup_service(self, temp_dir):
        """创建备份服务实例"""
        with patch('app.services.backup_service.settings') as mock_settings:
            mock_settings.BACKUP_PATH = str(temp_dir)
            mock_settings.EXPERIMENTS_PATH = str(temp_dir / "experiments")
            service = BackupService()
            return service
    
    @pytest.mark.asyncio
    async def test_create_experiment_backup(self, backup_service, db_session, temp_dir):
        """测试创建实验备份"""
        # 创建模拟实验
        mock_experiment = Mock(spec=Experiment)
        mock_experiment.id = "test-exp-123"
        mock_experiment.name = "测试实验"
        mock_experiment.description = "测试描述"
        mock_experiment.config = {"test": "config"}
        mock_experiment.results = {"test": "results"}
        mock_experiment.status = "completed"
        mock_experiment.created_at = datetime.now()
        mock_experiment.completed_at = datetime.now()
        mock_experiment.error_message = None
        
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_experiment
            
            result = await backup_service.create_experiment_backup(
                db_session, "test-exp-123"
            )
            
            assert "backup_name" in result
            assert "backup_path" in result
            assert "backup_size" in result
            assert result["experiment_id"] == "test-exp-123"
            assert result["experiment_name"] == "测试实验"
    
    @pytest.mark.asyncio
    async def test_create_experiment_backup_not_found(self, backup_service, db_session):
        """测试备份不存在的实验"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            with pytest.raises(ValueError, match="实验 .* 不存在"):
                await backup_service.create_experiment_backup(
                    db_session, "non-existent"
                )
    
    @pytest.mark.asyncio
    async def test_list_backups_empty(self, backup_service):
        """测试列出空备份列表"""
        result = await backup_service.list_backups()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_delete_backup_success(self, backup_service, temp_dir):
        """测试删除备份成功"""
        # 创建一个假的备份文件
        backup_file = temp_dir / "test_backup.tar.gz"
        backup_file.touch()
        
        result = await backup_service.delete_backup("test_backup")
        assert result is True
        assert not backup_file.exists()
    
    @pytest.mark.asyncio
    async def test_delete_backup_not_found(self, backup_service):
        """测试删除不存在的备份"""
        result = await backup_service.delete_backup("non-existent")
        assert result is False
    
    def test_calculate_directory_size(self, backup_service, temp_dir):
        """测试目录大小计算"""
        # 创建测试文件
        test_file1 = temp_dir / "file1.txt"
        test_file1.write_text("Hello World")
        
        test_file2 = temp_dir / "subdir" / "file2.txt"
        test_file2.parent.mkdir()
        test_file2.write_text("Test Content")
        
        size = backup_service._calculate_directory_size(temp_dir)
        
        expected_size = len("Hello World") + len("Test Content")
        assert size == expected_size
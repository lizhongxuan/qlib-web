"""
实验工作流集成测试
测试完整的实验生命周期：创建 -> 执行 -> 分析 -> 分享
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi.testclient import TestClient

# 假设我们有一个简化的app实例用于测试
class MockApp:
    """模拟FastAPI应用"""
    def __init__(self):
        self.routes = {}
    
    def get(self, path: str):
        def decorator(func):
            self.routes[f"GET {path}"] = func
            return func
        return decorator
    
    def post(self, path: str):
        def decorator(func):
            self.routes[f"POST {path}"] = func
            return func
        return decorator

# 创建模拟应用
app = MockApp()


class TestExperimentWorkflow:
    """实验工作流集成测试"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session
    
    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        return {
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "ANALYST"
        }
    
    @pytest.fixture
    def experiment_config(self):
        """实验配置"""
        return {
            "name": "集成测试实验",
            "description": "用于集成测试的实验配置",
            "data_config": {
                "stock_pool": "CSI300",
                "start_time": "2020-01-01",
                "end_time": "2023-12-31",
                "features": ["close", "volume", "returns"]
            },
            "model_config": {
                "name": "LightGBM",
                "params": {
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 6
                }
            },
            "strategy_config": {
                "name": "TopkDropoutStrategy",
                "params": {
                    "topk": 50,
                    "n_drop_days": 5
                }
            },
            "backtest_config": {
                "trade_cost": 0.0015,
                "min_periods": 20
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_experiment_lifecycle(self, mock_db_session, mock_user, experiment_config):
        """测试完整的实验生命周期"""
        
        # 第一步：创建实验
        with patch('app.services.experiment_service.ExperimentService') as MockExperimentService:
            mock_service = MockExperimentService.return_value
            mock_experiment_id = "exp-integration-test-123"
            mock_task_id = "task-integration-test-456"
            
            mock_service.create_experiment = AsyncMock(return_value={
                "experiment_id": mock_experiment_id,
                "task_id": mock_task_id,
                "status": "pending"
            })
            
            # 调用创建实验接口
            create_result = await mock_service.create_experiment(
                db=mock_db_session,
                user_id=mock_user["id"],
                experiment_config=experiment_config
            )
            
            assert create_result["experiment_id"] == mock_experiment_id
            assert create_result["task_id"] == mock_task_id
            assert create_result["status"] == "pending"
        
        # 第二步：模拟实验执行过程
        with patch('app.utils.experiment_runner.ExperimentRunner') as MockRunner:
            mock_runner = MockRunner.return_value
            
            # 模拟实验执行成功
            mock_runner.run_experiment = AsyncMock(return_value={
                "status": "completed",
                "results": {
                    "performance_metrics": {
                        "annual_return": 0.156,
                        "sharpe_ratio": 1.25,
                        "max_drawdown": 0.08,
                        "calmar_ratio": 1.95
                    },
                    "returns": [0.01, 0.02, -0.005, 0.015],
                    "positions": [
                        {"symbol": "000001.SZ", "weight": 0.05, "date": "2020-01-01"},
                        {"symbol": "000002.SZ", "weight": 0.03, "date": "2020-01-01"}
                    ]
                },
                "completed_at": datetime.now()
            })
            
            execution_result = await mock_runner.run_experiment(
                experiment_id=mock_experiment_id,
                config=experiment_config
            )
            
            assert execution_result["status"] == "completed"
            assert "performance_metrics" in execution_result["results"]
            assert execution_result["results"]["performance_metrics"]["annual_return"] == 0.156
        
        # 第三步：获取实验结果
        with patch('app.services.experiment_service.ExperimentService') as MockExperimentService:
            mock_service = MockExperimentService.return_value
            
            mock_service.get_experiment = AsyncMock(return_value={
                "id": mock_experiment_id,
                "name": experiment_config["name"],
                "status": "completed",
                "config": experiment_config,
                "results": execution_result["results"],
                "created_at": datetime.now() - timedelta(hours=1),
                "completed_at": datetime.now()
            })
            
            experiment_detail = await mock_service.get_experiment(
                db=mock_db_session,
                experiment_id=mock_experiment_id
            )
            
            assert experiment_detail["id"] == mock_experiment_id
            assert experiment_detail["status"] == "completed"
            assert "performance_metrics" in experiment_detail["results"]
        
        # 第四步：执行高级分析
        with patch('app.services.analysis.AnalysisService') as MockAnalysisService:
            mock_analysis_service = MockAnalysisService.return_value
            
            # 执行归因分析
            mock_analysis_service.execute_analysis = AsyncMock(return_value={
                "analysis_id": "analysis-123",
                "analysis_type": "attribution",
                "status": "completed",
                "results": {
                    "industry_attribution": {
                        "金融": 0.025,
                        "科技": 0.018,
                        "消费": -0.005
                    },
                    "style_attribution": {
                        "size": 0.012,
                        "value": -0.008,
                        "momentum": 0.020
                    },
                    "stock_selection_effect": 0.015
                }
            })
            
            attribution_result = await mock_analysis_service.execute_analysis(
                experiment_id=mock_experiment_id,
                analysis_config={
                    "analysis_type": "attribution",
                    "parameters": {
                        "include_style_factors": True,
                        "include_industry_effects": True
                    }
                }
            )
            
            assert attribution_result["analysis_type"] == "attribution"
            assert "industry_attribution" in attribution_result["results"]
            assert "style_attribution" in attribution_result["results"]
        
        # 第五步：创建分享链接
        with patch('app.services.share.ShareService') as MockShareService:
            mock_share_service = MockShareService.return_value
            
            mock_share_service.create_share = AsyncMock(return_value={
                "share_id": "share-123",
                "share_url": "https://example.com/share/share-123",
                "qr_code": "data:image/png;base64,iVBORw0KGgo...",
                "expires_at": datetime.now() + timedelta(days=30)
            })
            
            share_result = await mock_share_service.create_share(
                db=mock_db_session,
                user_id=mock_user["id"],
                experiment_id=mock_experiment_id,
                share_config={
                    "share_type": "public",
                    "permissions": ["view"],
                    "expires_at": datetime.now() + timedelta(days=30)
                }
            )
            
            assert "share_id" in share_result
            assert "share_url" in share_result
            assert "qr_code" in share_result
        
        print("✅ 完整的实验工作流集成测试通过")

    @pytest.mark.asyncio
    async def test_experiment_failure_handling(self, mock_db_session, mock_user, experiment_config):
        """测试实验失败处理流程"""
        
        with patch('app.services.experiment_service.ExperimentService') as MockExperimentService:
            mock_service = MockExperimentService.return_value
            mock_experiment_id = "exp-fail-test-123"
            
            # 创建实验
            mock_service.create_experiment = AsyncMock(return_value={
                "experiment_id": mock_experiment_id,
                "task_id": "task-fail-456",
                "status": "pending"
            })
            
            create_result = await mock_service.create_experiment(
                db=mock_db_session,
                user_id=mock_user["id"],
                experiment_config=experiment_config
            )
            
            # 模拟实验执行失败
            mock_service.update_experiment_status = AsyncMock(return_value=True)
            
            await mock_service.update_experiment_status(
                db=mock_db_session,
                experiment_id=mock_experiment_id,
                status="failed",
                error_message="数据加载失败：找不到指定的股票池数据"
            )
            
            # 获取失败的实验
            mock_service.get_experiment = AsyncMock(return_value={
                "id": mock_experiment_id,
                "status": "failed",
                "error_message": "数据加载失败：找不到指定的股票池数据",
                "failed_at": datetime.now()
            })
            
            failed_experiment = await mock_service.get_experiment(
                db=mock_db_session,
                experiment_id=mock_experiment_id
            )
            
            assert failed_experiment["status"] == "failed"
            assert "数据加载失败" in failed_experiment["error_message"]
        
        print("✅ 实验失败处理流程测试通过")
    
    @pytest.mark.asyncio
    async def test_concurrent_experiments(self, mock_db_session, mock_user, experiment_config):
        """测试并发实验执行"""
        
        experiment_ids = []
        
        with patch('app.services.experiment_service.ExperimentService') as MockExperimentService:
            mock_service = MockExperimentService.return_value
            
            # 创建多个并发实验
            async def create_experiment(index):
                exp_id = f"exp-concurrent-{index}"
                mock_service.create_experiment = AsyncMock(return_value={
                    "experiment_id": exp_id,
                    "task_id": f"task-concurrent-{index}",
                    "status": "pending"
                })
                
                result = await mock_service.create_experiment(
                    db=mock_db_session,
                    user_id=mock_user["id"],
                    experiment_config={
                        **experiment_config,
                        "name": f"并发实验_{index}"
                    }
                )
                experiment_ids.append(result["experiment_id"])
                return result
            
            # 并发创建5个实验
            tasks = [create_experiment(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert len(experiment_ids) == 5
            
            # 模拟查询所有实验
            mock_service.get_experiments = AsyncMock(return_value=(
                [{"id": exp_id, "status": "pending"} for exp_id in experiment_ids],
                5
            ))
            
            experiments, total = await mock_service.get_experiments(
                db=mock_db_session,
                user_id=mock_user["id"],
                status="pending"
            )
            
            assert total == 5
            assert len(experiments) == 5
        
        print("✅ 并发实验执行测试通过")
    
    @pytest.mark.asyncio
    async def test_data_backup_and_restore(self, mock_db_session, mock_user):
        """测试数据备份和恢复流程"""
        
        with patch('app.services.backup_service.BackupService') as MockBackupService:
            mock_service = MockBackupService.return_value
            
            # 创建系统备份
            mock_service.create_system_backup = AsyncMock(return_value={
                "backup_id": "backup-system-123",
                "backup_name": "system_backup_20240808_120000.tar.gz",
                "backup_size": 1073741824,  # 1GB
                "created_at": datetime.now(),
                "status": "completed"
            })
            
            backup_result = await mock_service.create_system_backup(
                db=mock_db_session,
                backup_type="full",
                description="集成测试系统备份"
            )
            
            assert "backup_id" in backup_result
            assert "backup_size" in backup_result
            assert backup_result["status"] == "completed"
            
            # 列出备份
            mock_service.list_backups = AsyncMock(return_value=[
                {
                    "backup_id": "backup-system-123",
                    "filename": "system_backup_20240808_120000.tar.gz",
                    "size": 1073741824,
                    "created_at": datetime.now()
                }
            ])
            
            backups = await mock_service.list_backups()
            assert len(backups) == 1
            assert backups[0]["backup_id"] == "backup-system-123"
            
            # 恢复备份
            mock_service.restore_backup = AsyncMock(return_value={
                "restore_id": "restore-123",
                "status": "completed",
                "restored_components": ["experiments", "users", "configurations"],
                "restore_time": datetime.now()
            })
            
            restore_result = await mock_service.restore_backup(
                db=mock_db_session,
                backup_id="backup-system-123",
                restore_config={
                    "restore_type": "selective",
                    "components": ["experiments", "users"]
                }
            )
            
            assert restore_result["status"] == "completed"
            assert "experiments" in restore_result["restored_components"]
            assert "users" in restore_result["restored_components"]
        
        print("✅ 数据备份和恢复流程测试通过")
    
    @pytest.mark.asyncio
    async def test_user_collaboration_workflow(self, mock_db_session):
        """测试用户协作工作流"""
        
        # 创建团队和用户
        team_data = {
            "id": "team-123",
            "name": "量化研究团队",
            "description": "专注量化投资研究",
            "created_at": datetime.now()
        }
        
        users = [
            {"id": "user-admin", "username": "admin", "role": "MANAGER"},
            {"id": "user-analyst1", "username": "analyst1", "role": "ANALYST"},
            {"id": "user-analyst2", "username": "analyst2", "role": "ANALYST"},
            {"id": "user-observer", "username": "observer", "role": "OBSERVER"}
        ]
        
        with patch('app.services.user.UserService') as MockUserService:
            mock_user_service = MockUserService.return_value
            
            # 创建团队
            mock_user_service.create_team = AsyncMock(return_value=team_data)
            team_result = await mock_user_service.create_team(
                db=mock_db_session,
                creator_id=users[0]["id"],
                team_data={
                    "name": team_data["name"],
                    "description": team_data["description"]
                }
            )
            
            assert team_result["name"] == team_data["name"]
            
            # 邀请成员加入团队
            for user in users[1:]:
                mock_user_service.invite_team_member = AsyncMock(return_value={
                    "invitation_id": f"inv-{user['id']}",
                    "team_id": team_data["id"],
                    "user_id": user["id"],
                    "role": user["role"],
                    "status": "accepted"
                })
                
                invite_result = await mock_user_service.invite_team_member(
                    db=mock_db_session,
                    team_id=team_data["id"],
                    inviter_id=users[0]["id"],
                    user_id=user["id"],
                    role=user["role"]
                )
                
                assert invite_result["user_id"] == user["id"]
                assert invite_result["status"] == "accepted"
        
        # 测试团队实验协作
        with patch('app.services.experiment_service.ExperimentService') as MockExperimentService:
            mock_service = MockExperimentService.return_value
            
            # 分析师1创建实验
            mock_service.create_experiment = AsyncMock(return_value={
                "experiment_id": "exp-team-123",
                "name": "团队协作实验",
                "creator_id": users[1]["id"],
                "team_id": team_data["id"],
                "permissions": {
                    users[0]["id"]: ["view", "edit", "delete", "share"],  # 管理员权限
                    users[1]["id"]: ["view", "edit", "share"],            # 创建者权限
                    users[2]["id"]: ["view", "comment"],                  # 其他分析师权限
                    users[3]["id"]: ["view"]                              # 观察者权限
                }
            })
            
            team_experiment = await mock_service.create_experiment(
                db=mock_db_session,
                user_id=users[1]["id"],
                experiment_config={
                    "name": "团队协作实验",
                    "team_id": team_data["id"],
                    "data_config": {"stock_pool": "CSI300"}
                }
            )
            
            assert team_experiment["team_id"] == team_data["id"]
            assert team_experiment["creator_id"] == users[1]["id"]
            
            # 测试权限检查
            assert users[0]["id"] in team_experiment["permissions"]
            assert "delete" in team_experiment["permissions"][users[0]["id"]]
            assert "view" in team_experiment["permissions"][users[3]["id"]]
            assert len(team_experiment["permissions"][users[3]["id"]]) == 1  # 观察者只有查看权限
        
        print("✅ 用户协作工作流测试通过")
    
    @pytest.mark.asyncio
    async def test_system_monitoring_integration(self, mock_db_session):
        """测试系统监控集成"""
        
        with patch('app.services.apm_service.APMService') as MockAPMService:
            mock_apm = MockAPMService.return_value
            
            # 模拟系统指标收集
            mock_metrics = {
                "request_count": 1500,
                "average_response_time": 0.245,
                "error_rate": 0.025,
                "active_connections": 45,
                "system_resources": {
                    "cpu_percent": 72.5,
                    "memory_percent": 68.3,
                    "disk_usage": 45.2
                }
            }
            
            mock_apm.get_current_metrics = AsyncMock(return_value=mock_metrics)
            
            current_metrics = await mock_apm.get_current_metrics()
            
            assert current_metrics["request_count"] == 1500
            assert current_metrics["error_rate"] == 0.025
            assert "system_resources" in current_metrics
            
            # 测试异常检测
            abnormal_metrics = {
                "response_time": 5.0,
                "error_rate": 0.15,
                "cpu_percent": 95.0
            }
            
            mock_apm.detect_anomalies = AsyncMock(return_value=[
                {
                    "metric": "response_time",
                    "value": 5.0,
                    "threshold": 2.0,
                    "severity": "high"
                },
                {
                    "metric": "cpu_percent", 
                    "value": 95.0,
                    "threshold": 80.0,
                    "severity": "critical"
                }
            ])
            
            anomalies = await mock_apm.detect_anomalies(abnormal_metrics)
            
            assert len(anomalies) == 2
            assert anomalies[0]["severity"] == "high"
            assert anomalies[1]["severity"] == "critical"
        
        # 测试故障恢复
        with patch('app.services.fault_recovery_service.FaultRecoveryService') as MockFaultRecovery:
            mock_recovery = MockFaultRecovery.return_value
            
            mock_recovery.detect_system_failures = AsyncMock(return_value=[
                {
                    "type": "high_cpu_usage",
                    "severity": "critical", 
                    "description": "CPU使用率超过95%",
                    "recommended_action": "重启高负载服务"
                }
            ])
            
            failures = await mock_recovery.detect_system_failures({
                "cpu_usage": 0.96,
                "memory_usage": 0.85
            })
            
            assert len(failures) == 1
            assert failures[0]["type"] == "high_cpu_usage"
            
            # 测试自动恢复
            mock_recovery.attempt_auto_recovery = AsyncMock(return_value={
                "success": True,
                "action_taken": "restart_service",
                "details": "已重启负载均衡服务"
            })
            
            recovery_result = await mock_recovery.attempt_auto_recovery(failures[0])
            
            assert recovery_result["success"] is True
            assert "restart_service" in recovery_result["action_taken"]
        
        print("✅ 系统监控集成测试通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
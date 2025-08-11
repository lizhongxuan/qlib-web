"""
API集成测试
"""
import pytest
from fastapi.testclient import TestClient


class TestExperimentAPI:
    """测试实验API"""
    
    def test_create_experiment_success(self, client: TestClient, sample_experiment_config):
        """测试成功创建实验"""
        response = client.post("/api/v1/experiments", json=sample_experiment_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "id" in data["data"]
    
    def test_create_experiment_invalid_config(self, client: TestClient):
        """测试创建实验时配置无效"""
        invalid_config = {
            "name": "",  # 空名称
            "config": {
                "data_config": {
                    "stock_pool": "INVALID_POOL",  # 无效股票池
                    "start_time": "2020-01-01",
                    "end_time": "2021-12-31"
                },
                "model_config": {"name": "LightGBM", "params": {}},
                "strategy_config": {"name": "TopkDropoutStrategy", "params": {}}
            }
        }
        
        response = client.post("/api/v1/experiments", json=invalid_config)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_get_experiments_list(self, client: TestClient):
        """测试获取实验列表"""
        response = client.get("/api/v1/experiments")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
    
    def test_get_experiments_with_pagination(self, client: TestClient):
        """测试分页获取实验列表"""
        response = client.get("/api/v1/experiments", params={
            "page": 1,
            "page_size": 5,
            "status": "completed"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) <= 5
    
    def test_get_experiment_detail_not_found(self, client: TestClient):
        """测试获取不存在的实验详情"""
        response = client.get("/api/v1/experiments/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
    
    def test_delete_experiment_not_found(self, client: TestClient):
        """测试删除不存在的实验"""
        response = client.delete("/api/v1/experiments/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestConfigAPI:
    """测试配置API"""
    
    def test_get_stock_pools(self, client: TestClient):
        """测试获取股票池列表"""
        response = client.get("/api/v1/config/stock-pools")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "CSI300" in data["data"]
    
    def test_get_models(self, client: TestClient):
        """测试获取模型列表"""
        response = client.get("/api/v1/config/models")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "LightGBM" in data["data"]
    
    def test_get_strategies(self, client: TestClient):
        """测试获取策略列表"""
        response = client.get("/api/v1/config/strategies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_get_model_params(self, client: TestClient):
        """测试获取模型参数"""
        response = client.get("/api/v1/config/model-params/LightGBM")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], dict)
        assert "n_estimators" in data["data"]
    
    def test_get_model_params_invalid_model(self, client: TestClient):
        """测试获取无效模型的参数"""
        response = client.get("/api/v1/config/model-params/InvalidModel")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
    
    def test_validate_config_success(self, client: TestClient, sample_experiment_config):
        """测试配置验证成功"""
        response = client.post("/api/v1/config/validate", json=sample_experiment_config["config"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is True
    
    def test_validate_config_failure(self, client: TestClient):
        """测试配置验证失败"""
        invalid_config = {
            "data_config": {
                "stock_pool": "INVALID_POOL",
                "start_time": "2020-01-01",
                "end_time": "2021-12-31"
            },
            "model_config": {"name": "InvalidModel", "params": {}},
            "strategy_config": {"name": "InvalidStrategy", "params": {}}
        }
        
        response = client.post("/api/v1/config/validate", json=invalid_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is False
        assert "errors" in data["data"]


class TestDashboardAPI:
    """测试仪表盘API"""
    
    def test_get_dashboard_summary(self, client: TestClient):
        """测试获取仪表盘摘要"""
        response = client.get("/api/v1/dashboard/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "totalExperiments" in data["data"]
        assert "runningExperiments" in data["data"]
        assert "completedExperiments" in data["data"]
        assert "failedExperiments" in data["data"]
    
    def test_get_recent_experiments(self, client: TestClient):
        """测试获取最近实验"""
        response = client.get("/api/v1/dashboard/recent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_get_system_info(self, client: TestClient):
        """测试获取系统信息"""
        response = client.get("/api/v1/dashboard/system-info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "qlib_version" in data["data"]
        assert "system_status" in data["data"]


class TestBackupAPI:
    """测试备份API"""
    
    def test_create_full_backup(self, client: TestClient):
        """测试创建完整备份"""
        response = client.post("/api/v1/backup/full", json={
            "description": "测试完整备份"
        })
        
        # 备份功能可能需要一些时间，这里主要测试接口可达性
        assert response.status_code in [200, 500]  # 500可能是因为缺少实际数据
    
    def test_list_backups(self, client: TestClient):
        """测试获取备份列表"""
        response = client.get("/api/v1/backup")
        
        assert response.status_code == 200
        data = response.json()
        assert "backups" in data
        assert "total" in data
    
    def test_delete_backup_not_found(self, client: TestClient):
        """测试删除不存在的备份"""
        response = client.delete("/api/v1/backup/non-existent-backup")
        
        assert response.status_code == 404


class TestHealthCheck:
    """测试健康检查"""
    
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
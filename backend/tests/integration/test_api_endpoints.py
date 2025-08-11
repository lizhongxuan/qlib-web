"""
API端点集成测试
测试主要API接口的完整请求-响应流程
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import status


class MockFastAPIApp:
    """模拟FastAPI应用，用于测试"""
    
    def __init__(self):
        self.middleware = []
        self.routes = {}
        self.dependencies = {}
    
    def add_middleware(self, middleware_class, **options):
        self.middleware.append((middleware_class, options))
    
    def include_router(self, router, **options):
        pass  # 简化实现


# 创建模拟应用实例
app = MockFastAPIApp()


class TestExperimentAPIEndpoints:
    """实验相关API端点测试"""
    
    @pytest.fixture
    def mock_auth_header(self):
        """模拟认证头"""
        return {"Authorization": "Bearer test-jwt-token"}
    
    @pytest.fixture
    def experiment_payload(self):
        """实验创建请求载荷"""
        return {
            "name": "API测试实验",
            "description": "用于API集成测试",
            "data_config": {
                "stock_pool": "CSI300",
                "start_time": "2020-01-01",
                "end_time": "2023-12-31"
            },
            "model_config": {
                "name": "LightGBM",
                "params": {"n_estimators": 100}
            },
            "strategy_config": {
                "name": "TopkDropoutStrategy",
                "params": {"topk": 50}
            },
            "backtest_config": {
                "trade_cost": 0.0015
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_experiment_endpoint(self, mock_auth_header, experiment_payload):
        """测试创建实验API端点"""
        
        # 模拟HTTP客户端
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            # 模拟成功响应
            mock_response = MockHTTPResponse(201, {
                "success": True,
                "data": {
                    "experiment_id": "exp-api-test-123",
                    "task_id": "task-api-test-456",
                    "status": "pending",
                    "message": "实验已创建并加入执行队列"
                }
            })
            
            mock_client.post = AsyncMock(return_value=mock_response)
            
            # 发送创建实验请求
            response = await mock_client.post(
                "/api/v1/experiments",
                headers=mock_auth_header,
                json=experiment_payload
            )
            
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["success"] is True
            assert "experiment_id" in response_data["data"]
            assert "task_id" in response_data["data"]
            
            # 验证请求参数
            mock_client.post.assert_called_once_with(
                "/api/v1/experiments",
                headers=mock_auth_header,
                json=experiment_payload
            )
    
    @pytest.mark.asyncio
    async def test_get_experiments_list_endpoint(self, mock_auth_header):
        """测试获取实验列表API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_experiments = [
                {
                    "id": "exp-1",
                    "name": "实验1",
                    "status": "completed",
                    "created_at": "2024-08-08T10:00:00Z",
                    "performance_summary": {
                        "annual_return": 0.15,
                        "sharpe_ratio": 1.2
                    }
                },
                {
                    "id": "exp-2", 
                    "name": "实验2",
                    "status": "running",
                    "created_at": "2024-08-08T11:00:00Z"
                }
            ]
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "experiments": mock_experiments,
                    "total": 2,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 1
                }
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # 发送获取实验列表请求
            response = await mock_client.get(
                "/api/v1/experiments?page=1&page_size=20&status=all",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert len(response_data["data"]["experiments"]) == 2
            assert response_data["data"]["total"] == 2
    
    @pytest.mark.asyncio
    async def test_get_experiment_detail_endpoint(self, mock_auth_header):
        """测试获取实验详情API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        experiment_id = "exp-detail-test-123"
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "id": experiment_id,
                    "name": "详情测试实验",
                    "status": "completed",
                    "config": {
                        "data_config": {"stock_pool": "CSI300"},
                        "model_config": {"name": "LightGBM"}
                    },
                    "results": {
                        "performance_metrics": {
                            "annual_return": 0.18,
                            "sharpe_ratio": 1.35,
                            "max_drawdown": 0.06
                        }
                    },
                    "created_at": "2024-08-08T09:00:00Z",
                    "completed_at": "2024-08-08T09:45:00Z"
                }
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = await mock_client.get(
                f"/api/v1/experiments/{experiment_id}",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["data"]["id"] == experiment_id
            assert response_data["data"]["status"] == "completed"
            assert "performance_metrics" in response_data["data"]["results"]
    
    @pytest.mark.asyncio
    async def test_delete_experiment_endpoint(self, mock_auth_header):
        """测试删除实验API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        experiment_id = "exp-delete-test-123"
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "message": f"实验 {experiment_id} 已删除"
            })
            
            mock_client.delete = AsyncMock(return_value=mock_response)
            
            response = await mock_client.delete(
                f"/api/v1/experiments/{experiment_id}",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert "已删除" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_experiment_performance_endpoint(self, mock_auth_header):
        """测试获取实验性能数据API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        experiment_id = "exp-perf-test-123"
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "experiment_id": experiment_id,
                    "performance_metrics": {
                        "annual_return": 0.165,
                        "sharpe_ratio": 1.28,
                        "max_drawdown": 0.075,
                        "calmar_ratio": 2.2,
                        "information_ratio": 0.85
                    },
                    "performance_curve": [
                        {"date": "2020-01-01", "portfolio_return": 0.002, "benchmark_return": 0.001},
                        {"date": "2020-01-02", "portfolio_return": 0.015, "benchmark_return": 0.008},
                    ],
                    "benchmark_comparison": {
                        "excess_return": 0.045,
                        "tracking_error": 0.12,
                        "win_rate": 0.68
                    }
                }
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = await mock_client.get(
                f"/api/v1/experiments/{experiment_id}/performance",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["data"]["experiment_id"] == experiment_id
            assert "performance_metrics" in response_data["data"]
            assert "performance_curve" in response_data["data"]
            assert len(response_data["data"]["performance_curve"]) == 2


class TestAnalysisAPIEndpoints:
    """分析相关API端点测试"""
    
    @pytest.fixture 
    def mock_auth_header(self):
        return {"Authorization": "Bearer test-jwt-token"}
    
    @pytest.mark.asyncio
    async def test_execute_attribution_analysis_endpoint(self, mock_auth_header):
        """测试执行归因分析API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        experiment_id = "exp-attribution-test-123"
        analysis_config = {
            "analysis_type": "enhanced_attribution",
            "parameters": {
                "include_style_factors": True,
                "include_industry_effects": True,
                "include_interaction_effects": True
            }
        }
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(201, {
                "success": True,
                "data": {
                    "analysis_id": "analysis-attribution-456",
                    "analysis_type": "enhanced_attribution",
                    "status": "completed",
                    "results": {
                        "industry_attribution": {
                            "金融": 0.025,
                            "科技": 0.018,
                            "消费": -0.005,
                            "医药": 0.012
                        },
                        "style_attribution": {
                            "size": 0.008,
                            "value": -0.003,
                            "momentum": 0.015,
                            "quality": 0.007
                        },
                        "stock_selection_effect": 0.018,
                        "timing_effect": -0.002,
                        "interaction_effects": {
                            "size_value": -0.001,
                            "momentum_quality": 0.003
                        }
                    }
                }
            })
            
            mock_client.post = AsyncMock(return_value=mock_response)
            
            response = await mock_client.post(
                f"/api/v1/analysis/{experiment_id}/execute",
                headers=mock_auth_header,
                json=analysis_config
            )
            
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["analysis_type"] == "enhanced_attribution"
            assert "industry_attribution" in response_data["data"]["results"]
            assert "style_attribution" in response_data["data"]["results"]
    
    @pytest.mark.asyncio
    async def test_risk_analysis_endpoint(self, mock_auth_header):
        """测试风险分析API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        experiment_id = "exp-risk-test-123"
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "analysis_id": "analysis-risk-456",
                    "analysis_type": "advanced_risk_analysis",
                    "results": {
                        "var_metrics": {
                            "var_95": -0.032,
                            "var_99": -0.058,
                            "cvar_95": -0.045,
                            "cvar_99": -0.072
                        },
                        "drawdown_analysis": {
                            "max_drawdown": -0.085,
                            "max_drawdown_duration": 42,
                            "current_drawdown": -0.015,
                            "recovery_time": 12
                        },
                        "correlation_analysis": {
                            "market_correlation": 0.78,
                            "sector_correlations": {
                                "金融": 0.65,
                                "科技": 0.72,
                                "消费": 0.58
                            }
                        },
                        "tail_risk_metrics": {
                            "skewness": -0.23,
                            "kurtosis": 3.45,
                            "tail_ratio": 1.15
                        }
                    }
                }
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = await mock_client.get(
                f"/api/v1/analysis/{experiment_id}/risk",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert "var_metrics" in response_data["data"]["results"]
            assert "drawdown_analysis" in response_data["data"]["results"]
            assert response_data["data"]["results"]["var_metrics"]["var_95"] < 0


class TestUserAPIEndpoints:
    """用户相关API端点测试"""
    
    @pytest.mark.asyncio
    async def test_user_registration_endpoint(self):
        """测试用户注册API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        registration_data = {
            "username": "newuser",
            "email": "newuser@example.com", 
            "password": "secure_password123",
            "full_name": "新用户"
        }
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(201, {
                "success": True,
                "data": {
                    "user_id": "user-new-123",
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "verification_sent": True
                },
                "message": "用户注册成功，请检查邮箱验证"
            })
            
            mock_client.post = AsyncMock(return_value=mock_response)
            
            response = await mock_client.post(
                "/api/v1/auth/register",
                json=registration_data
            )
            
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["data"]["username"] == "newuser"
            assert response_data["data"]["verification_sent"] is True
    
    @pytest.mark.asyncio
    async def test_user_login_endpoint(self):
        """测试用户登录API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        login_data = {
            "username": "testuser",
            "password": "test_password"
        }
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 7200,
                    "user": {
                        "id": "user-test-123",
                        "username": "testuser",
                        "email": "test@example.com",
                        "role": "ANALYST"
                    }
                }
            })
            
            mock_client.post = AsyncMock(return_value=mock_response)
            
            response = await mock_client.post(
                "/api/v1/auth/login",
                json=login_data
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert "access_token" in response_data["data"]
            assert "refresh_token" in response_data["data"]
            assert response_data["data"]["user"]["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_current_user_endpoint(self):
        """测试获取当前用户信息API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        auth_header = {"Authorization": "Bearer valid-jwt-token"}
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "id": "user-current-123",
                    "username": "current_user",
                    "email": "current@example.com",
                    "full_name": "当前用户",
                    "role": "ANALYST",
                    "status": "ACTIVE",
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_login": "2024-08-08T12:00:00Z",
                    "experiment_count": 25,
                    "team_count": 2
                }
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = await mock_client.get(
                "/api/v1/users/me",
                headers=auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["data"]["username"] == "current_user"
            assert response_data["data"]["role"] == "ANALYST"
            assert response_data["data"]["experiment_count"] == 25


class TestSystemAPIEndpoints:
    """系统相关API端点测试"""
    
    @pytest.fixture
    def mock_auth_header(self):
        return {"Authorization": "Bearer admin-jwt-token"}
    
    @pytest.mark.asyncio
    async def test_system_health_endpoint(self, mock_auth_header):
        """测试系统健康检查API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "status": "healthy",
                    "version": "2.0.0",
                    "uptime": 86400,
                    "components": {
                        "database": {
                            "status": "healthy",
                            "response_time": 0.05
                        },
                        "redis": {
                            "status": "healthy",
                            "response_time": 0.02
                        },
                        "celery": {
                            "status": "healthy",
                            "active_workers": 3,
                            "queue_length": 5
                        },
                        "file_system": {
                            "status": "healthy",
                            "disk_usage": 0.45
                        }
                    },
                    "metrics": {
                        "active_experiments": 12,
                        "total_users": 156,
                        "cpu_usage": 68.5,
                        "memory_usage": 72.3
                    }
                }
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = await mock_client.get(
                "/api/v1/system/health",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["data"]["status"] == "healthy"
            assert "database" in response_data["data"]["components"]
            assert response_data["data"]["components"]["database"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_system_metrics_endpoint(self, mock_auth_header):
        """测试系统指标API端点"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(200, {
                "success": True,
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "system_resources": {
                        "cpu": {
                            "usage_percent": 65.8,
                            "load_average": [1.2, 1.5, 1.8]
                        },
                        "memory": {
                            "total": 16000000000,
                            "used": 11520000000,
                            "percent": 72.0
                        },
                        "disk": {
                            "total": 500000000000,
                            "used": 225000000000,
                            "percent": 45.0
                        }
                    },
                    "application_metrics": {
                        "request_rate": 150.5,
                        "error_rate": 0.025,
                        "average_response_time": 0.245
                    },
                    "business_metrics": {
                        "active_experiments": 18,
                        "completed_today": 7,
                        "active_users": 45
                    }
                }
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = await mock_client.get(
                "/api/v1/monitoring/metrics",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert "system_resources" in response_data["data"]
            assert "application_metrics" in response_data["data"]
            assert response_data["data"]["system_resources"]["cpu"]["usage_percent"] == 65.8


class TestErrorHandling:
    """API错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """测试认证错误处理"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(401, {
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_ERROR",
                    "message": "无效的认证令牌",
                    "details": {
                        "reason": "token_expired"
                    }
                },
                "request_id": "req-auth-error-123"
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # 使用无效token请求
            response = await mock_client.get(
                "/api/v1/experiments",
                headers={"Authorization": "Bearer invalid-token"}
            )
            
            assert response.status_code == 401
            response_data = response.json()
            assert response_data["success"] is False
            assert response_data["error"]["code"] == "AUTHENTICATION_ERROR"
            assert "request_id" in response_data
    
    @pytest.mark.asyncio
    async def test_validation_error(self):
        """测试参数验证错误处理"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        invalid_payload = {
            "name": "",  # 空名称
            "data_config": {
                "start_time": "2023-01-01",
                "end_time": "2022-01-01"  # 结束时间早于开始时间
            }
        }
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(422, {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR", 
                    "message": "请求参数验证失败",
                    "details": [
                        {
                            "field": "name",
                            "message": "实验名称不能为空"
                        },
                        {
                            "field": "data_config.end_time",
                            "message": "结束时间必须晚于开始时间"
                        }
                    ]
                },
                "request_id": "req-validation-error-123"
            })
            
            mock_client.post = AsyncMock(return_value=mock_response)
            
            response = await mock_client.post(
                "/api/v1/experiments",
                headers={"Authorization": "Bearer valid-token"},
                json=invalid_payload
            )
            
            assert response.status_code == 422
            response_data = response.json()
            assert response_data["error"]["code"] == "VALIDATION_ERROR"
            assert len(response_data["error"]["details"]) == 2
    
    @pytest.mark.asyncio
    async def test_resource_not_found_error(self):
        """测试资源未找到错误处理"""
        
        class MockHTTPResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        non_existent_id = "exp-not-exist-123"
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MockHTTPResponse(404, {
                "success": False,
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": f"实验 {non_existent_id} 不存在",
                    "details": {
                        "resource_type": "experiment",
                        "resource_id": non_existent_id
                    }
                },
                "request_id": "req-not-found-123"
            })
            
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = await mock_client.get(
                f"/api/v1/experiments/{non_existent_id}",
                headers={"Authorization": "Bearer valid-token"}
            )
            
            assert response.status_code == 404
            response_data = response.json()
            assert response_data["error"]["code"] == "RESOURCE_NOT_FOUND"
            assert non_existent_id in response_data["error"]["message"]


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short"])
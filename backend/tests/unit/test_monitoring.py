"""
测试系统监控功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import psutil
from datetime import datetime, timedelta

from app.services.apm_service import APMService
from app.services.error_logging_service import ErrorLoggingService
from app.services.user_analytics_service import UserAnalyticsService
from app.services.fault_recovery_service import FaultRecoveryService
from app.services.graceful_degradation_service import GracefulDegradationService


class TestAPMService:
    """测试APM性能监控服务"""
    
    @pytest.fixture
    def apm_service(self):
        """创建APM服务实例"""
        return APMService()
    
    @pytest.fixture
    def mock_request(self):
        """创建模拟HTTP请求"""
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/v1/experiments"
        request.headers = {"user-agent": "test-client/1.0"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request
    
    def test_record_request_metrics(self, apm_service, mock_request):
        """测试记录请求指标"""
        response_time = 0.150  # 150ms
        status_code = 200
        
        apm_service.record_request_metrics(
            request=mock_request,
            response_time=response_time,
            status_code=status_code,
            response_size=1024
        )
        
        # 验证指标已记录（通过内部状态或mock验证）
        metrics = apm_service.get_current_metrics()
        assert metrics is not None
        assert 'request_count' in metrics
        assert 'average_response_time' in metrics
        assert metrics['request_count'] >= 1
    
    def test_get_current_metrics(self, apm_service):
        """测试获取当前指标"""
        metrics = apm_service.get_current_metrics()
        
        # 验证指标结构
        expected_keys = [
            'request_count',
            'average_response_time',
            'error_rate',
            'active_connections',
            'system_resources'
        ]
        
        for key in expected_keys:
            assert key in metrics
        
        # 验证系统资源指标
        system_resources = metrics['system_resources']
        assert 'cpu_percent' in system_resources
        assert 'memory_percent' in system_resources
        assert 'disk_usage' in system_resources
    
    def test_get_performance_history(self, apm_service):
        """测试获取性能历史"""
        # 模拟历史数据
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        history = apm_service.get_performance_history(
            start_time=start_time,
            end_time=end_time,
            interval='5m'
        )
        
        assert isinstance(history, list)
        
        if history:  # 如果有历史数据
            record = history[0]
            assert 'timestamp' in record
            assert 'metrics' in record
            assert 'response_time' in record['metrics']
            assert 'request_count' in record['metrics']
    
    def test_detect_anomalies(self, apm_service):
        """测试异常检测"""
        # 模拟异常指标
        abnormal_metrics = {
            'response_time': 5.0,  # 5秒响应时间
            'error_rate': 0.25,    # 25%错误率
            'cpu_percent': 95.0,   # 95% CPU使用率
            'memory_percent': 98.0  # 98%内存使用率
        }
        
        anomalies = apm_service.detect_anomalies(abnormal_metrics)
        
        assert isinstance(anomalies, list)
        assert len(anomalies) > 0
        
        # 验证异常记录结构
        anomaly = anomalies[0]
        assert 'metric' in anomaly
        assert 'value' in anomaly
        assert 'threshold' in anomaly
        assert 'severity' in anomaly
        assert anomaly['severity'] in ['low', 'medium', 'high', 'critical']
    
    def test_generate_health_report(self, apm_service):
        """测试生成健康报告"""
        report = apm_service.generate_health_report()
        
        assert 'overall_health' in report
        assert 'component_health' in report
        assert 'recommendations' in report
        assert 'timestamp' in report
        
        # 验证整体健康状态
        overall_health = report['overall_health']
        assert 'status' in overall_health
        assert 'score' in overall_health
        assert overall_health['status'] in ['healthy', 'warning', 'critical']
        assert 0 <= overall_health['score'] <= 100
        
        # 验证组件健康状态
        component_health = report['component_health']
        expected_components = ['database', 'redis', 'file_system', 'external_apis']
        for component in expected_components:
            if component in component_health:
                assert 'status' in component_health[component]
                assert 'details' in component_health[component]


class TestErrorLoggingService:
    """测试错误日志服务"""
    
    @pytest.fixture
    def error_service(self):
        """创建错误日志服务实例"""
        return ErrorLoggingService()
    
    @pytest.fixture
    def mock_error(self):
        """创建模拟错误"""
        try:
            raise ValueError("测试错误消息")
        except Exception as e:
            return e
    
    def test_log_error(self, error_service, mock_error):
        """测试记录错误"""
        context = {
            'user_id': 'user-123',
            'request_id': 'req-456',
            'experiment_id': 'exp-789'
        }
        
        error_id = error_service.log_error(
            error=mock_error,
            context=context,
            severity='high'
        )
        
        assert error_id is not None
        assert isinstance(error_id, str)
        
        # 验证错误已保存
        saved_error = error_service.get_error(error_id)
        assert saved_error is not None
        assert saved_error['error_type'] == 'ValueError'
        assert saved_error['message'] == '测试错误消息'
        assert saved_error['severity'] == 'high'
    
    def test_get_error_statistics(self, error_service):
        """测试获取错误统计"""
        # 先记录一些测试错误
        for i in range(5):
            try:
                raise RuntimeError(f"测试错误 {i}")
            except Exception as e:
                error_service.log_error(e, severity='medium')
        
        stats = error_service.get_error_statistics(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )
        
        assert 'total_errors' in stats
        assert 'error_by_type' in stats
        assert 'error_by_severity' in stats
        assert 'error_trend' in stats
        
        assert stats['total_errors'] >= 5
        assert 'RuntimeError' in stats['error_by_type']
        assert 'medium' in stats['error_by_severity']
    
    def test_get_frequent_errors(self, error_service):
        """测试获取频繁错误"""
        frequent_errors = error_service.get_frequent_errors(limit=10)
        
        assert isinstance(frequent_errors, list)
        
        if frequent_errors:
            error = frequent_errors[0]
            assert 'error_pattern' in error
            assert 'count' in error
            assert 'latest_occurrence' in error
            assert 'suggested_fix' in error
    
    def test_create_error_alert(self, error_service, mock_error):
        """测试创建错误告警"""
        context = {
            'user_id': 'user-123',
            'critical_operation': True
        }
        
        alert = error_service.create_error_alert(
            error=mock_error,
            context=context,
            severity='critical'
        )
        
        assert alert is not None
        assert 'alert_id' in alert
        assert 'notification_sent' in alert
        assert 'escalation_level' in alert
        assert alert['severity'] == 'critical'


class TestUserAnalyticsService:
    """测试用户行为分析服务"""
    
    @pytest.fixture
    def analytics_service(self):
        """创建用户分析服务实例"""
        return UserAnalyticsService()
    
    def test_track_user_action(self, analytics_service):
        """测试跟踪用户行为"""
        user_id = 'user-123'
        action = 'create_experiment'
        properties = {
            'experiment_name': '测试实验',
            'model_type': 'LightGBM',
            'data_range': '2020-2023'
        }
        
        event_id = analytics_service.track_user_action(
            user_id=user_id,
            action=action,
            properties=properties
        )
        
        assert event_id is not None
        assert isinstance(event_id, str)
    
    def test_get_user_activity_summary(self, analytics_service):
        """测试获取用户活动摘要"""
        user_id = 'user-123'
        
        # 先记录一些活动
        actions = [
            ('login', {}),
            ('create_experiment', {'model_type': 'LightGBM'}),
            ('view_experiment', {'experiment_id': 'exp-123'}),
            ('share_experiment', {'share_type': 'public'})
        ]
        
        for action, properties in actions:
            analytics_service.track_user_action(user_id, action, properties)
        
        summary = analytics_service.get_user_activity_summary(
            user_id=user_id,
            days=30
        )
        
        assert 'total_actions' in summary
        assert 'action_breakdown' in summary
        assert 'daily_activity' in summary
        assert 'most_active_day' in summary
        
        assert summary['total_actions'] >= len(actions)
    
    def test_get_popular_features(self, analytics_service):
        """测试获取热门功能"""
        popular_features = analytics_service.get_popular_features(days=30)
        
        assert isinstance(popular_features, list)
        
        if popular_features:
            feature = popular_features[0]
            assert 'feature_name' in feature
            assert 'usage_count' in feature
            assert 'unique_users' in feature
            assert 'trend' in feature
    
    def test_generate_usage_report(self, analytics_service):
        """测试生成使用报告"""
        report = analytics_service.generate_usage_report(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        assert 'summary' in report
        assert 'user_metrics' in report
        assert 'feature_metrics' in report
        assert 'trends' in report
        
        # 验证摘要信息
        summary = report['summary']
        assert 'total_users' in summary
        assert 'active_users' in summary
        assert 'total_actions' in summary
        assert 'avg_session_duration' in summary


class TestFaultRecoveryService:
    """测试故障恢复服务"""
    
    @pytest.fixture
    def recovery_service(self):
        """创建故障恢复服务实例"""
        return FaultRecoveryService()
    
    def test_detect_system_failure(self, recovery_service):
        """测试系统故障检测"""
        # 模拟系统指标
        system_metrics = {
            'database_connection': False,
            'redis_connection': True,
            'disk_space_free': 0.02,  # 只有2%空间
            'memory_usage': 0.98,     # 98%内存使用
            'response_time': 10.0,    # 10秒响应时间
            'error_rate': 0.50        # 50%错误率
        }
        
        failures = recovery_service.detect_system_failures(system_metrics)
        
        assert isinstance(failures, list)
        assert len(failures) > 0
        
        # 应该检测到多个故障
        failure_types = [f['type'] for f in failures]
        assert 'database_connection' in failure_types
        assert 'low_disk_space' in failure_types
        assert 'high_memory_usage' in failure_types
        
        # 验证故障记录结构
        failure = failures[0]
        assert 'type' in failure
        assert 'severity' in failure
        assert 'description' in failure
        assert 'recommended_action' in failure
    
    def test_attempt_auto_recovery(self, recovery_service):
        """测试自动恢复"""
        failure = {
            'type': 'database_connection',
            'severity': 'high',
            'description': '数据库连接失败',
            'context': {'connection_pool': 'exhausted'}
        }
        
        with patch.object(recovery_service, '_reconnect_database') as mock_reconnect:
            mock_reconnect.return_value = True
            
            recovery_result = recovery_service.attempt_auto_recovery(failure)
            
            assert recovery_result is not None
            assert 'success' in recovery_result
            assert 'action_taken' in recovery_result
            assert 'details' in recovery_result
            
            mock_reconnect.assert_called_once()
    
    def test_execute_recovery_plan(self, recovery_service):
        """测试执行恢复计划"""
        recovery_plan = {
            'plan_id': 'plan-123',
            'steps': [
                {
                    'step': 'restart_service',
                    'service': 'redis',
                    'timeout': 30
                },
                {
                    'step': 'clear_cache',
                    'cache_type': 'application',
                    'timeout': 10
                }
            ]
        }
        
        with patch.object(recovery_service, '_execute_recovery_step') as mock_execute:
            mock_execute.return_value = {'success': True, 'message': 'Step completed'}
            
            result = recovery_service.execute_recovery_plan(recovery_plan)
            
            assert result is not None
            assert 'plan_id' in result
            assert 'success' in result
            assert 'step_results' in result
            
            # 应该执行所有步骤
            assert len(result['step_results']) == len(recovery_plan['steps'])
            assert mock_execute.call_count == len(recovery_plan['steps'])
    
    def test_get_recovery_history(self, recovery_service):
        """测试获取恢复历史"""
        history = recovery_service.get_recovery_history(limit=10)
        
        assert isinstance(history, list)
        
        if history:
            record = history[0]
            assert 'timestamp' in record
            assert 'failure_type' in record
            assert 'recovery_action' in record
            assert 'success' in record
            assert 'duration' in record


class TestGracefulDegradationService:
    """测试优雅降级服务"""
    
    @pytest.fixture
    def degradation_service(self):
        """创建优雅降级服务实例"""
        return GracefulDegradationService()
    
    def test_should_activate_degradation(self, degradation_service):
        """测试是否应该激活降级"""
        # 正常情况
        normal_metrics = {
            'error_rate': 0.01,
            'response_time': 0.200,
            'cpu_usage': 0.60,
            'memory_usage': 0.70
        }
        
        should_degrade = degradation_service.should_activate_degradation(normal_metrics)
        assert should_degrade is False
        
        # 异常情况
        abnormal_metrics = {
            'error_rate': 0.15,      # 15%错误率
            'response_time': 3.0,    # 3秒响应时间
            'cpu_usage': 0.95,       # 95% CPU
            'memory_usage': 0.90     # 90%内存
        }
        
        should_degrade = degradation_service.should_activate_degradation(abnormal_metrics)
        assert should_degrade is True
    
    def test_activate_degradation_mode(self, degradation_service):
        """测试激活降级模式"""
        trigger_reason = "high_error_rate"
        severity_level = "medium"
        
        result = degradation_service.activate_degradation_mode(
            trigger_reason=trigger_reason,
            severity_level=severity_level
        )
        
        assert result is not None
        assert 'activation_id' in result
        assert 'activated_features' in result
        assert 'disabled_features' in result
        assert result['severity_level'] == severity_level
        
        # 验证降级状态已激活
        assert degradation_service.is_degradation_active() is True
        
        # 验证降级配置已应用
        config = degradation_service.get_current_degradation_config()
        assert config is not None
        assert 'level' in config
        assert 'active_features' in config
    
    def test_get_degraded_response(self, degradation_service):
        """测试获取降级响应"""
        # 先激活降级模式
        degradation_service.activate_degradation_mode("high_load", "medium")
        
        # 测试不同功能的降级响应
        test_cases = [
            {
                'feature': 'experiment_list',
                'request_data': {'page': 1, 'page_size': 20}
            },
            {
                'feature': 'performance_analysis', 
                'request_data': {'experiment_id': 'exp-123'}
            },
            {
                'feature': 'real_time_updates',
                'request_data': {'user_id': 'user-123'}
            }
        ]
        
        for test_case in test_cases:
            response = degradation_service.get_degraded_response(
                feature=test_case['feature'],
                request_data=test_case['request_data']
            )
            
            assert response is not None
            assert 'status' in response
            assert 'message' in response
            assert 'degradation_active' in response
            assert response['degradation_active'] is True
    
    def test_deactivate_degradation_mode(self, degradation_service):
        """测试停用降级模式"""
        # 先激活降级模式
        degradation_service.activate_degradation_mode("test", "low")
        assert degradation_service.is_degradation_active() is True
        
        # 停用降级模式
        result = degradation_service.deactivate_degradation_mode(
            reason="system_recovered"
        )
        
        assert result is not None
        assert 'deactivation_id' in result
        assert 'duration' in result
        assert 'restored_features' in result
        
        # 验证降级状态已停用
        assert degradation_service.is_degradation_active() is False
    
    def test_get_degradation_history(self, degradation_service):
        """测试获取降级历史"""
        # 激活并停用几次降级
        for i in range(3):
            degradation_service.activate_degradation_mode(f"test_{i}", "low")
            degradation_service.deactivate_degradation_mode("test_complete")
        
        history = degradation_service.get_degradation_history(limit=10)
        
        assert isinstance(history, list)
        assert len(history) >= 3
        
        # 验证历史记录结构
        record = history[0]
        assert 'activation_time' in record
        assert 'deactivation_time' in record
        assert 'trigger_reason' in record
        assert 'severity_level' in record
        assert 'duration' in record
        assert 'affected_features' in record
    
    def test_circuit_breaker_pattern(self, degradation_service):
        """测试熔断器模式"""
        service_name = "external_api"
        
        # 初始状态应该是关闭的
        state = degradation_service.get_circuit_breaker_state(service_name)
        assert state == "closed"
        
        # 模拟连续失败
        for _ in range(5):
            degradation_service.record_service_failure(service_name)
        
        # 应该转为打开状态
        state = degradation_service.get_circuit_breaker_state(service_name)
        assert state == "open"
        
        # 在打开状态下调用应该直接失败
        result = degradation_service.call_with_circuit_breaker(
            service_name, lambda: "success"
        )
        assert result is None or 'circuit_breaker_open' in str(result)
    
    def test_adaptive_timeout(self, degradation_service):
        """测试自适应超时"""
        service_name = "slow_service"
        
        # 记录一些响应时间
        response_times = [0.1, 0.2, 0.5, 1.0, 2.0]
        for rt in response_times:
            degradation_service.record_response_time(service_name, rt)
        
        # 获取自适应超时
        timeout = degradation_service.get_adaptive_timeout(service_name)
        
        assert timeout > 0
        assert timeout > max(response_times)  # 应该大于最大响应时间
        
        # 在高负载情况下，超时应该增加
        degradation_service.activate_degradation_mode("high_load", "high")
        degraded_timeout = degradation_service.get_adaptive_timeout(service_name)
        
        assert degraded_timeout >= timeout  # 降级时超时应该不减少
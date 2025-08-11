"""
参数推荐服务单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from datetime import datetime, timedelta

from app.services.parameter_recommendation import ParameterRecommendationService
from app.models.experiment import Experiment


class TestParameterRecommendationService:
    """参数推荐服务测试"""

    def setup_method(self):
        """设置测试方法"""
        with patch('app.services.parameter_recommendation.QLIB_CONFIG', {
            'model_params': {
                'LightGBM': {
                    'n_estimators': {
                        'type': 'int',
                        'min': 50,
                        'max': 300,
                        'default': 100,
                        'display_name': 'Number of Estimators'
                    },
                    'learning_rate': {
                        'type': 'float',
                        'min': 0.01,
                        'max': 0.3,
                        'default': 0.1,
                        'display_name': 'Learning Rate'
                    },
                    'use_gpu': {
                        'type': 'bool',
                        'default': False,
                        'display_name': 'Use GPU'
                    }
                }
            },
            'strategy_params': {
                'TopkDropoutStrategy': {
                    'topk': {
                        'type': 'int',
                        'min': 10,
                        'max': 100,
                        'default': 50,
                        'display_name': 'Top K'
                    },
                    'dropout': {
                        'type': 'float',
                        'min': 0.0,
                        'max': 0.5,
                        'default': 0.1,
                        'display_name': 'Dropout Rate'
                    }
                }
            }
        }):
            self.service = ParameterRecommendationService()

    def create_mock_experiment(self, exp_id: str, config: dict, results: dict = None):
        """创建模拟实验对象"""
        experiment = Mock(spec=Experiment)
        experiment.id = exp_id
        experiment.config = config
        experiment.results = results or {
            'performance': {
                'total_return': 0.15,
                'sharpe_ratio': 1.2,
                'max_drawdown': -0.1
            }
        }
        experiment.created_at = datetime.now()
        experiment.status = 'completed'
        return experiment

    @pytest.mark.asyncio
    async def test_recommend_model_params_with_historical_data(self):
        """测试基于历史数据的模型参数推荐"""
        # 创建模拟的历史实验
        experiments = [
            self.create_mock_experiment(
                '1',
                {
                    'model_config': {
                        'name': 'LightGBM',
                        'params': {'n_estimators': 120, 'learning_rate': 0.08}
                    }
                },
                {
                    'performance': {
                        'total_return': 0.18,
                        'sharpe_ratio': 1.5,
                        'max_drawdown': -0.08
                    }
                }
            ),
            self.create_mock_experiment(
                '2',
                {
                    'model_config': {
                        'name': 'LightGBM',
                        'params': {'n_estimators': 100, 'learning_rate': 0.1}
                    }
                },
                {
                    'performance': {
                        'total_return': 0.12,
                        'sharpe_ratio': 1.0,
                        'max_drawdown': -0.12
                    }
                }
            )
        ]
        
        # 模拟数据库查询
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = experiments
        
        # 执行推荐
        result = await self.service.recommend_model_params(
            db=mock_db,
            model_name='LightGBM'
        )
        
        # 验证结果
        assert result['model_name'] == 'LightGBM'
        assert 'recommended_params' in result
        assert 'confidence' in result
        assert 'explanation' in result
        assert result['historical_data']['experiments_analyzed'] == 2
        
        # 验证推荐参数在合理范围内
        params = result['recommended_params']
        assert 50 <= params.get('n_estimators', 0) <= 300
        assert 0.01 <= params.get('learning_rate', 0) <= 0.3

    @pytest.mark.asyncio
    async def test_recommend_model_params_no_historical_data(self):
        """测试无历史数据时的默认参数推荐"""
        # 模拟空查询结果
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = await self.service.recommend_model_params(
            db=mock_db,
            model_name='LightGBM'
        )
        
        # 验证返回默认参数
        assert result['model_name'] == 'LightGBM'
        assert result['confidence'] == 0.5
        assert result['explanation'] == '使用默认参数，无足够历史数据进行推荐'
        assert result['recommended_params']['n_estimators'] == 100
        assert result['recommended_params']['learning_rate'] == 0.1

    @pytest.mark.asyncio
    async def test_recommend_strategy_params(self):
        """测试策略参数推荐"""
        experiments = [
            self.create_mock_experiment(
                '1',
                {
                    'strategy_config': {
                        'name': 'TopkDropoutStrategy',
                        'params': {'topk': 40, 'dropout': 0.05}
                    }
                }
            )
        ]
        
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = experiments
        
        result = await self.service.recommend_strategy_params(
            db=mock_db,
            strategy_name='TopkDropoutStrategy'
        )
        
        assert result['strategy_name'] == 'TopkDropoutStrategy'
        assert 'recommended_params' in result
        assert result['historical_data']['experiments_analyzed'] == 1

    @pytest.mark.asyncio
    async def test_validate_parameters_success(self):
        """测试参数验证成功"""
        result = await self.service.validate_parameters(
            model_name='LightGBM',
            model_params={'n_estimators': 100, 'learning_rate': 0.1},
            strategy_name='TopkDropoutStrategy',
            strategy_params={'topk': 50, 'dropout': 0.1}
        )
        
        assert result['valid'] is True
        assert len(result['errors']) == 0

    @pytest.mark.asyncio
    async def test_validate_parameters_invalid_model(self):
        """测试无效模型参数验证"""
        result = await self.service.validate_parameters(
            model_name='UnknownModel',
            model_params={},
            strategy_name='TopkDropoutStrategy',
            strategy_params={}
        )
        
        assert result['valid'] is False
        assert any('未知模型' in error for error in result['errors'])

    @pytest.mark.asyncio
    async def test_validate_parameters_out_of_range(self):
        """测试参数超出范围验证"""
        result = await self.service.validate_parameters(
            model_name='LightGBM',
            model_params={'n_estimators': 500, 'learning_rate': 0.5},  # 超出范围
            strategy_name='TopkDropoutStrategy',
            strategy_params={}
        )
        
        assert result['valid'] is False
        errors = result['errors']
        assert any('大于最大值' in error for error in errors)

    @pytest.mark.asyncio
    async def test_analyze_parameter_sensitivity(self):
        """测试参数敏感性分析"""
        experiments = [
            self.create_mock_experiment(
                f'{i}',
                {
                    'model_config': {
                        'name': 'LightGBM',
                        'params': {'learning_rate': 0.01 + i * 0.02}
                    }
                },
                {
                    'performance': {
                        'total_return': 0.1 + i * 0.02,
                        'sharpe_ratio': 1.0 + i * 0.1,
                        'max_drawdown': -0.1 - i * 0.01
                    }
                }
            )
            for i in range(10)
        ]
        
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = experiments
        
        result = await self.service.analyze_parameter_sensitivity(
            db=mock_db,
            model_name='LightGBM',
            param_name='learning_rate'
        )
        
        assert result['parameter'] == 'learning_rate'
        assert result['model'] == 'LightGBM'
        assert result['sensitivity'] in ['low', 'medium', 'high']
        assert isinstance(result['correlation'], float)
        assert len(result['optimal_range']) == 2

    @pytest.mark.asyncio
    async def test_analyze_parameter_sensitivity_insufficient_data(self):
        """测试数据不足时的敏感性分析"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []  # 无数据
        
        result = await self.service.analyze_parameter_sensitivity(
            db=mock_db,
            model_name='LightGBM',
            param_name='learning_rate'
        )
        
        assert result['sensitivity'] == 'unknown'
        assert '历史数据不足' in result['message']

    def test_calculate_performance_score_valid_data(self):
        """测试性能评分计算（有效数据）"""
        performance = {
            'total_return': 0.15,
            'sharpe_ratio': 1.2,
            'max_drawdown': -0.1
        }
        
        score = self.service._calculate_performance_score(performance)
        
        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_calculate_performance_score_empty_data(self):
        """测试性能评分计算（空数据）"""
        score = self.service._calculate_performance_score({})
        assert score == 0.0

    def test_calculate_performance_score_invalid_data(self):
        """测试性能评分计算（无效数据）"""
        performance = {
            'total_return': 'invalid',
            'sharpe_ratio': float('inf'),
            'max_drawdown': float('nan')
        }
        
        score = self.service._calculate_performance_score(performance)
        assert score == 0.0

    def test_calculate_performance_score_missing_fields(self):
        """测试性能评分计算（缺少字段）"""
        performance = {
            'total_return': 0.15
            # 缺少 sharpe_ratio 和 max_drawdown
        }
        
        score = self.service._calculate_performance_score(performance)
        assert score > 0  # 应该有部分得分

    def test_get_default_params_valid_model(self):
        """测试获取默认参数（有效模型）"""
        result = self.service._get_default_params('LightGBM')
        
        assert result['model_name'] == 'LightGBM'
        assert result['recommended_params']['n_estimators'] == 100
        assert result['recommended_params']['learning_rate'] == 0.1
        assert result['confidence'] == 0.5

    def test_get_default_params_unknown_model(self):
        """测试获取默认参数（未知模型）"""
        result = self.service._get_default_params('UnknownModel')
        
        assert result['model_name'] == 'UnknownModel'
        assert result['recommended_params'] == {}
        assert result['confidence'] == 0.5

    def test_analyze_parameter_recommendations(self):
        """测试参数推荐分析"""
        param_data = [
            {
                'params': {'n_estimators': 120, 'learning_rate': 0.08, 'use_gpu': True},
                'score': 85.0,
                'experiment_id': '1'
            },
            {
                'params': {'n_estimators': 100, 'learning_rate': 0.1, 'use_gpu': False},
                'score': 75.0,
                'experiment_id': '2'
            },
            {
                'params': {'n_estimators': 150, 'learning_rate': 0.05, 'use_gpu': True},
                'score': 90.0,
                'experiment_id': '3'
            }
        ]
        
        result = self.service._analyze_parameter_recommendations(param_data, 'LightGBM')
        
        assert 'params' in result
        assert 'confidence' in result
        assert 'explanation' in result
        assert 'analysis' in result
        
        # 验证推荐参数基于高分实验
        params = result['params']
        assert isinstance(params['n_estimators'], int)
        assert isinstance(params['learning_rate'], float)
        assert isinstance(params['use_gpu'], bool)
        
        # 验证分析结果
        analysis = result['analysis']
        for param_name in ['n_estimators', 'learning_rate', 'use_gpu']:
            assert param_name in analysis
            assert 'recommended_value' in analysis[param_name]
            assert 'confidence' in analysis[param_name]

    def test_validate_model_params(self):
        """测试模型参数验证"""
        params = {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'unknown_param': 'value'
        }
        
        result = self.service._validate_model_params('LightGBM', params)
        
        assert len(result['errors']) == 0
        assert 'unknown_param' in ' '.join(result['warnings'])

    def test_validate_model_params_type_errors(self):
        """测试模型参数类型错误"""
        params = {
            'n_estimators': 'not_int',
            'learning_rate': 'not_float',
            'use_gpu': 'not_bool'
        }
        
        result = self.service._validate_model_params('LightGBM', params)
        
        errors = result['errors']
        assert len(errors) == 3
        assert any('整数类型' in error for error in errors)
        assert any('数值类型' in error for error in errors)
        assert any('布尔类型' in error for error in errors)

    def test_validate_model_params_range_errors(self):
        """测试模型参数范围错误"""
        params = {
            'n_estimators': 500,  # 超过最大值300
            'learning_rate': 0.5   # 超过最大值0.3
        }
        
        result = self.service._validate_model_params('LightGBM', params)
        
        errors = result['errors']
        assert any('大于最大值' in error for error in errors)

    def test_validate_parameter_combination(self):
        """测试参数组合验证"""
        model_params = {'n_estimators': 500}
        strategy_params = {'topk': 150}
        
        result = self.service._validate_parameter_combination(
            'LightGBM', model_params, 'TopkDropoutStrategy', strategy_params
        )
        
        # 应该有关于复杂度的警告
        warnings = result['warnings']
        assert len(warnings) > 0
        assert any('复杂度' in warning for warning in warnings)

    def test_calculate_parameter_sensitivity(self):
        """测试参数敏感性计算"""
        # 创建具有相关性的数据
        param_values = [0.01 + i * 0.02 for i in range(10)]
        performance_scores = [50 + i * 5 for i in range(10)]
        param_performance_pairs = list(zip(param_values, performance_scores))
        
        result = self.service._calculate_parameter_sensitivity(
            param_performance_pairs, 'learning_rate'
        )
        
        assert result['level'] in ['low', 'medium', 'high']
        assert isinstance(result['correlation'], float)
        assert len(result['optimal_range']) == 2
        assert result['optimal_range'][0] <= result['optimal_range'][1]

    def test_calculate_parameter_sensitivity_insufficient_data(self):
        """测试数据不足的敏感性计算"""
        param_performance_pairs = [(0.1, 50.0)]  # 只有一个数据点
        
        result = self.service._calculate_parameter_sensitivity(
            param_performance_pairs, 'learning_rate'
        )
        
        assert result['level'] == 'unknown'
        assert result['correlation'] == 0
        assert result['optimal_range'] is None
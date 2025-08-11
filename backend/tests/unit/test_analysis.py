"""
测试高级分析功能
"""
import pytest
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.services.analysis import AnalysisService
from app.utils.analysis_calculator import (
    AttributionCalculator,
    RiskAnalysisCalculator,
    ScenarioAnalysisCalculator,
    ModelDiagnosticCalculator
)


class TestAttributionCalculator:
    """测试归因分析计算器"""
    
    @pytest.fixture
    def attribution_calculator(self):
        """创建归因分析计算器实例"""
        return AttributionCalculator()
    
    @pytest.fixture
    def mock_returns_data(self):
        """创建模拟收益数据"""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        returns = pd.DataFrame({
            'date': dates,
            'portfolio_return': np.random.normal(0.001, 0.02, len(dates)),
            'benchmark_return': np.random.normal(0.0005, 0.015, len(dates))
        })
        return returns
    
    @pytest.fixture
    def mock_holdings_data(self):
        """创建模拟持仓数据"""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        holdings = []
        for date in dates[::5]:  # 每5天一个持仓记录
            holdings.append({
                'date': date,
                'holdings': {
                    '000001.SZ': np.random.uniform(0.02, 0.08),
                    '000002.SZ': np.random.uniform(0.02, 0.08),
                    '600000.SH': np.random.uniform(0.02, 0.08),
                }
            })
        return holdings
    
    def test_calculate_enhanced_attribution(self, attribution_calculator, mock_returns_data, mock_holdings_data):
        """测试增强归因分析"""
        result = attribution_calculator.calculate_enhanced_attribution(
            returns_data=mock_returns_data,
            holdings_data=mock_holdings_data
        )
        
        # 验证返回结构
        assert 'industry_attribution' in result
        assert 'style_attribution' in result  
        assert 'stock_selection_effect' in result
        assert 'timing_effect' in result
        assert 'interaction_effects' in result
        
        # 验证行业归因
        industry_attr = result['industry_attribution']
        assert isinstance(industry_attr, dict)
        assert len(industry_attr) > 0
        
        # 验证风格归因
        style_attr = result['style_attribution']
        assert 'size' in style_attr
        assert 'value' in style_attr
        assert 'momentum' in style_attr
        
        # 验证数值类型
        assert isinstance(result['stock_selection_effect'], (int, float))
        assert isinstance(result['timing_effect'], (int, float))
    
    def test_industry_contribution(self, attribution_calculator):
        """测试行业贡献分析"""
        mock_holdings = [
            {
                'date': '2020-01-01',
                'holdings': {
                    '000001.SZ': 0.05,  # 银行
                    '000858.SZ': 0.03,  # 科技
                    '000002.SZ': 0.04   # 房地产
                }
            }
        ]
        
        result = attribution_calculator._calculate_industry_contribution(mock_holdings)
        
        assert isinstance(result, dict)
        # 应该包含主要行业
        assert any('金融' in industry or '银行' in industry for industry in result.keys())
        
        # 所有贡献值应该是数字
        for contribution in result.values():
            assert isinstance(contribution, (int, float))
    
    def test_style_factor_analysis(self, attribution_calculator, mock_returns_data):
        """测试风格因子分析"""
        result = attribution_calculator._calculate_style_factor_analysis(mock_returns_data)
        
        expected_factors = ['size', 'value', 'momentum', 'quality', 'growth']
        
        assert isinstance(result, dict)
        
        for factor in expected_factors:
            assert factor in result
            assert isinstance(result[factor], (int, float))
            # 风格因子贡献应该在合理范围内
            assert -0.1 <= result[factor] <= 0.1
    
    def test_stock_selection_effect(self, attribution_calculator, mock_holdings_data, mock_returns_data):
        """测试个股选择效应"""
        result = attribution_calculator._calculate_stock_selection_effect(
            mock_holdings_data, mock_returns_data
        )
        
        assert isinstance(result, (int, float))
        # 选择效应应该在合理范围内
        assert -0.2 <= result <= 0.2


class TestRiskAnalysisCalculator:
    """测试风险分析计算器"""
    
    @pytest.fixture
    def risk_calculator(self):
        """创建风险分析计算器实例"""
        return RiskAnalysisCalculator()
    
    @pytest.fixture
    def mock_portfolio_returns(self):
        """创建模拟组合收益数据"""
        np.random.seed(42)  # 固定随机种子以获得可重现的结果
        returns = np.random.normal(0.001, 0.02, 252)  # 一年的日收益
        return pd.Series(returns, index=pd.date_range('2020-01-01', periods=252))
    
    def test_calculate_advanced_risk_analysis(self, risk_calculator, mock_portfolio_returns):
        """测试高级风险分析"""
        result = risk_calculator.calculate_advanced_risk_analysis(
            returns_data=mock_portfolio_returns
        )
        
        # 验证返回结构
        assert 'var_metrics' in result
        assert 'drawdown_analysis' in result
        assert 'correlation_analysis' in result
        assert 'tail_risk_metrics' in result
        assert 'liquidity_risk' in result
        
        # 验证VaR指标
        var_metrics = result['var_metrics']
        assert 'var_95' in var_metrics
        assert 'var_99' in var_metrics
        assert 'cvar_95' in var_metrics
        assert 'cvar_99' in var_metrics
        
        # VaR应该是负值（损失）
        assert var_metrics['var_95'] < 0
        assert var_metrics['var_99'] < var_metrics['var_95']  # 99% VaR应该更极端
        
        # 验证回撤分析
        drawdown = result['drawdown_analysis']
        assert 'max_drawdown' in drawdown
        assert 'max_drawdown_duration' in drawdown
        assert 'current_drawdown' in drawdown
        assert 'recovery_time' in drawdown
        
    def test_calculate_var(self, risk_calculator, mock_portfolio_returns):
        """测试VaR计算"""
        # 历史方法
        var_95_hist = risk_calculator._calculate_var_historical(mock_portfolio_returns, 0.95)
        var_99_hist = risk_calculator._calculate_var_historical(mock_portfolio_returns, 0.99)
        
        assert var_95_hist < 0  # 损失为负值
        assert var_99_hist < var_95_hist  # 99% VaR更极端
        
        # 蒙特卡洛方法
        var_95_mc = risk_calculator._calculate_var_monte_carlo(mock_portfolio_returns, 0.95)
        var_99_mc = risk_calculator._calculate_var_monte_carlo(mock_portfolio_returns, 0.99)
        
        assert var_95_mc < 0
        assert var_99_mc < var_95_mc
        
        # 两种方法的结果应该相对接近
        assert abs(var_95_hist - var_95_mc) < 0.01
    
    def test_calculate_drawdown(self, risk_calculator, mock_portfolio_returns):
        """测试回撤计算"""
        drawdown_series = risk_calculator._calculate_drawdown_series(mock_portfolio_returns)
        
        assert len(drawdown_series) == len(mock_portfolio_returns)
        assert all(drawdown_series <= 0)  # 回撤应该都是非正值
        
        max_dd = risk_calculator._calculate_max_drawdown(mock_portfolio_returns)
        assert max_dd <= 0  # 最大回撤应该是负值
        assert max_dd == drawdown_series.min()  # 应该等于回撤序列的最小值
    
    def test_correlation_analysis(self, risk_calculator, mock_portfolio_returns):
        """测试相关性分析"""
        # 创建基准收益
        benchmark_returns = np.random.normal(0.0005, 0.015, len(mock_portfolio_returns))
        benchmark_series = pd.Series(benchmark_returns, index=mock_portfolio_returns.index)
        
        corr_analysis = risk_calculator._calculate_correlation_analysis(
            mock_portfolio_returns, benchmark_series
        )
        
        assert 'market_correlation' in corr_analysis
        assert 'rolling_correlation' in corr_analysis
        assert 'upside_correlation' in corr_analysis
        assert 'downside_correlation' in corr_analysis
        
        # 相关系数应该在[-1, 1]范围内
        market_corr = corr_analysis['market_correlation']
        assert -1 <= market_corr <= 1
        
        # 滚动相关系数应该是时间序列
        rolling_corr = corr_analysis['rolling_correlation']
        assert isinstance(rolling_corr, (list, pd.Series))


class TestScenarioAnalysisCalculator:
    """测试情景分析计算器"""
    
    @pytest.fixture
    def scenario_calculator(self):
        """创建情景分析计算器实例"""
        return ScenarioAnalysisCalculator()
    
    @pytest.fixture
    def mock_scenario_config(self):
        """创建模拟情景配置"""
        return {
            'scenarios': [
                {
                    'name': '市场下跌',
                    'market_shock': -0.20,
                    'duration': 30,
                    'sector_shocks': {
                        '金融': -0.25,
                        '科技': -0.15,
                        '消费': -0.18
                    }
                },
                {
                    'name': '利率上升',
                    'interest_rate_shock': 0.02,
                    'duration': 90,
                    'sector_shocks': {
                        '金融': 0.10,
                        '地产': -0.30,
                        '公用事业': -0.15
                    }
                }
            ]
        }
    
    @pytest.fixture
    def mock_portfolio_data(self):
        """创建模拟组合数据"""
        return {
            'positions': {
                '000001.SZ': 0.05,  # 银行
                '000858.SZ': 0.03,  # 科技
                '000002.SZ': 0.04,  # 地产
                '600036.SH': 0.06,  # 银行
                '300059.SZ': 0.02   # 科技
            },
            'total_value': 1000000,
            'cash': 0.80  # 80%现金
        }
    
    def test_calculate_enhanced_scenario_analysis(self, scenario_calculator, mock_scenario_config, mock_portfolio_data):
        """测试增强情景分析"""
        result = scenario_calculator.calculate_enhanced_scenario_analysis(
            portfolio_data=mock_portfolio_data,
            scenario_config=mock_scenario_config
        )
        
        # 验证返回结构
        assert 'scenario_results' in result
        assert 'risk_metrics' in result
        assert 'sensitivity_analysis' in result
        
        # 验证情景结果
        scenario_results = result['scenario_results']
        assert len(scenario_results) == 2  # 两个情景
        
        for scenario in scenario_results:
            assert 'scenario_name' in scenario
            assert 'portfolio_impact' in scenario
            assert 'sector_impacts' in scenario
            assert 'expected_loss' in scenario
            assert 'confidence_interval' in scenario
    
    def test_simulate_market_scenario(self, scenario_calculator, mock_portfolio_data):
        """测试市场情景模拟"""
        scenario = {
            'name': '市场崩盘',
            'market_shock': -0.30,
            'duration': 20,
            'sector_shocks': {
                '金融': -0.35,
                '科技': -0.40
            }
        }
        
        result = scenario_calculator._simulate_market_scenario(
            mock_portfolio_data, scenario
        )
        
        assert 'scenario_name' in result
        assert 'portfolio_impact' in result
        assert 'sector_impacts' in result
        
        # 在负向冲击下，组合影响应该是负的
        assert result['portfolio_impact'] < 0
        
        # 验证行业影响
        sector_impacts = result['sector_impacts']
        assert '金融' in sector_impacts
        assert '科技' in sector_impacts
    
    def test_monte_carlo_simulation(self, scenario_calculator, mock_portfolio_data):
        """测试蒙特卡洛模拟"""
        simulation_config = {
            'simulation_count': 100,
            'time_horizon': 252,
            'confidence_levels': [0.05, 0.95]
        }
        
        result = scenario_calculator.calculate_monte_carlo_simulation(
            portfolio_data=mock_portfolio_data,
            simulation_config=simulation_config
        )
        
        assert 'simulation_results' in result
        assert 'confidence_intervals' in result
        assert 'risk_metrics' in result
        
        # 验证模拟结果
        sim_results = result['simulation_results']
        assert len(sim_results) == simulation_config['simulation_count']
        
        # 验证置信区间
        confidence_intervals = result['confidence_intervals']
        assert 0.05 in confidence_intervals
        assert 0.95 in confidence_intervals
    
    def test_sensitivity_analysis(self, scenario_calculator, mock_portfolio_data):
        """测试敏感性分析"""
        parameters = {
            'market_volatility': [0.15, 0.20, 0.25, 0.30],
            'interest_rate': [0.02, 0.03, 0.04, 0.05],
            'sector_correlation': [0.3, 0.5, 0.7, 0.9]
        }
        
        result = scenario_calculator.calculate_sensitivity_analysis(
            portfolio_data=mock_portfolio_data,
            parameters=parameters
        )
        
        assert 'parameter_sensitivity' in result
        assert 'tornado_chart_data' in result
        assert 'elasticity_measures' in result
        
        # 验证参数敏感性
        param_sensitivity = result['parameter_sensitivity']
        for param_name in parameters.keys():
            assert param_name in param_sensitivity
            sensitivity_data = param_sensitivity[param_name]
            assert len(sensitivity_data) == len(parameters[param_name])


class TestModelDiagnosticCalculator:
    """测试模型诊断计算器"""
    
    @pytest.fixture
    def diagnostic_calculator(self):
        """创建模型诊断计算器实例"""
        return ModelDiagnosticCalculator()
    
    @pytest.fixture
    def mock_model_predictions(self):
        """创建模拟模型预测数据"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=252)
        
        # 模拟预测和实际收益
        predictions = np.random.normal(0.02, 0.05, (252, 10))  # 10只股票，252个交易日
        actual_returns = predictions + np.random.normal(0, 0.03, (252, 10))  # 加入噪声
        
        return {
            'predictions': pd.DataFrame(predictions, index=dates),
            'actual_returns': pd.DataFrame(actual_returns, index=dates),
            'features': pd.DataFrame(np.random.randn(252, 20), index=dates)  # 20个特征
        }
    
    def test_calculate_enhanced_feature_importance(self, diagnostic_calculator, mock_model_predictions):
        """测试增强特征重要性分析"""
        result = diagnostic_calculator.calculate_enhanced_feature_importance(
            predictions_data=mock_model_predictions['predictions'],
            features_data=mock_model_predictions['features'],
            actual_returns=mock_model_predictions['actual_returns']
        )
        
        # 验证返回结构
        assert 'shap_values' in result
        assert 'feature_importance_ranking' in result
        assert 'interaction_matrix' in result
        assert 'stability_analysis' in result
        
        # 验证SHAP值
        shap_values = result['shap_values']
        assert 'global_importance' in shap_values
        assert 'waterfall_data' in shap_values
        
        # 验证特征排序
        feature_ranking = result['feature_importance_ranking']
        assert isinstance(feature_ranking, list)
        assert len(feature_ranking) > 0
        
        # 验证交互矩阵
        interaction_matrix = result['interaction_matrix']
        assert isinstance(interaction_matrix, (dict, list))
    
    def test_calculate_model_performance_monitoring(self, diagnostic_calculator, mock_model_predictions):
        """测试模型性能监控"""
        result = diagnostic_calculator.calculate_model_performance_monitoring(
            predictions_data=mock_model_predictions['predictions'],
            actual_returns=mock_model_predictions['actual_returns']
        )
        
        # 验证返回结构
        assert 'ic_analysis' in result
        assert 'stability_metrics' in result
        assert 'prediction_error_analysis' in result
        assert 'model_health_score' in result
        assert 'alert_flags' in result
        
        # 验证IC分析
        ic_analysis = result['ic_analysis']
        assert 'rolling_ic' in ic_analysis
        assert 'ic_decay' in ic_analysis
        assert 'ic_statistics' in ic_analysis
        
        # 验证模型健康评分
        health_score = result['model_health_score']
        assert isinstance(health_score, (int, float))
        assert 0 <= health_score <= 1
        
        # 验证预警标志
        alert_flags = result['alert_flags']
        assert isinstance(alert_flags, list)
    
    def test_calculate_backtest_quality_check(self, diagnostic_calculator, mock_model_predictions):
        """测试回测质量检验"""
        # 创建模拟回测结果
        backtest_data = {
            'returns': mock_model_predictions['actual_returns'].mean(axis=1),
            'positions': mock_model_predictions['predictions'].apply(lambda x: x > x.median(), axis=1),
            'turnover': pd.Series(np.random.uniform(0.1, 0.3, 252), 
                                index=mock_model_predictions['predictions'].index)
        }
        
        result = diagnostic_calculator.calculate_backtest_quality_check(
            backtest_data=backtest_data,
            market_data=mock_model_predictions['actual_returns']
        )
        
        # 验证返回结构
        assert 'lookahead_bias_check' in result
        assert 'data_quality_check' in result
        assert 'statistical_significance' in result
        assert 'robustness_tests' in result
        assert 'quality_score' in result
        
        # 验证前瞻偏差检测
        lookahead_check = result['lookahead_bias_check']
        assert 'suspicious_correlations' in lookahead_check
        assert 'timing_analysis' in lookahead_check
        
        # 验证数据质量检查
        data_quality = result['data_quality_check']
        assert 'missing_values_ratio' in data_quality
        assert 'outlier_detection' in data_quality
        assert 'distribution_analysis' in data_quality
        
        # 验证质量评分
        quality_score = result['quality_score']
        assert isinstance(quality_score, (int, float))
        assert 0 <= quality_score <= 1
    
    def test_calculate_ic_metrics(self, diagnostic_calculator, mock_model_predictions):
        """测试IC指标计算"""
        predictions = mock_model_predictions['predictions'].iloc[:, 0]  # 取第一只股票
        actual_returns = mock_model_predictions['actual_returns'].iloc[:, 0]
        
        ic_metrics = diagnostic_calculator._calculate_ic_metrics(predictions, actual_returns)
        
        assert 'ic' in ic_metrics
        assert 'rank_ic' in ic_metrics
        assert 'ic_mean' in ic_metrics
        assert 'ic_std' in ic_metrics
        assert 'ic_ir' in ic_metrics  # IC信息比率
        assert 'hit_rate' in ic_metrics
        
        # IC值应该在[-1, 1]范围内
        assert -1 <= ic_metrics['ic'] <= 1
        assert -1 <= ic_metrics['rank_ic'] <= 1
        
        # 命中率应该在[0, 1]范围内
        assert 0 <= ic_metrics['hit_rate'] <= 1
    
    def test_detect_model_degradation(self, diagnostic_calculator, mock_model_predictions):
        """测试模型退化检测"""
        predictions = mock_model_predictions['predictions']
        actual_returns = mock_model_predictions['actual_returns']
        
        # 模拟模型性能随时间退化
        degraded_predictions = predictions.copy()
        degraded_predictions.iloc[150:] *= 0.5  # 后期性能降低
        
        degradation_result = diagnostic_calculator._detect_model_degradation(
            degraded_predictions, actual_returns
        )
        
        assert 'performance_trend' in degradation_result
        assert 'degradation_detected' in degradation_result
        assert 'degradation_start_date' in degradation_result
        assert 'severity' in degradation_result
        
        # 应该检测到性能退化
        assert degradation_result['degradation_detected'] is True


class TestAnalysisService:
    """测试分析服务"""
    
    @pytest.fixture
    def analysis_service(self):
        """创建分析服务实例"""
        return AnalysisService()
    
    @pytest.fixture
    def mock_experiment_data(self):
        """创建模拟实验数据"""
        return {
            'experiment_id': 'test-exp-123',
            'results': {
                'returns': [0.01, 0.02, -0.005, 0.015, -0.01],
                'positions': [
                    {'symbol': '000001.SZ', 'weight': 0.1, 'date': '2020-01-01'},
                    {'symbol': '000002.SZ', 'weight': 0.08, 'date': '2020-01-01'},
                ],
                'benchmark_returns': [0.005, 0.01, -0.002, 0.008, -0.005]
            }
        }
    
    @pytest.mark.asyncio
    async def test_execute_analysis(self, analysis_service, mock_experiment_data):
        """测试执行分析"""
        analysis_config = {
            'analysis_type': 'attribution',
            'parameters': {
                'include_style_factors': True,
                'include_industry_effects': True
            }
        }
        
        with patch.object(analysis_service, '_load_experiment_data') as mock_load:
            mock_load.return_value = mock_experiment_data
            
            result = await analysis_service.execute_analysis(
                experiment_id='test-exp-123',
                analysis_config=analysis_config
            )
            
            assert result is not None
            assert 'analysis_id' in result
            assert 'analysis_type' in result
            assert 'results' in result
            assert result['analysis_type'] == 'attribution'
    
    @pytest.mark.asyncio
    async def test_get_analysis_results(self, analysis_service):
        """测试获取分析结果"""
        analysis_id = 'test-analysis-123'
        
        with patch.object(analysis_service, '_load_analysis_from_storage') as mock_load:
            mock_result = {
                'analysis_id': analysis_id,
                'status': 'completed',
                'results': {'test': 'data'},
                'created_at': datetime.now(),
                'completed_at': datetime.now()
            }
            mock_load.return_value = mock_result
            
            result = await analysis_service.get_analysis_results(analysis_id)
            
            assert result['analysis_id'] == analysis_id
            assert result['status'] == 'completed'
            assert 'results' in result
    
    @pytest.mark.asyncio
    async def test_list_available_analyses(self, analysis_service):
        """测试列出可用分析类型"""
        result = await analysis_service.list_available_analyses()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 验证分析类型结构
        analysis_type = result[0]
        assert 'name' in analysis_type
        assert 'display_name' in analysis_type
        assert 'description' in analysis_type
        assert 'parameters' in analysis_type
        
        # 应该包含主要的分析类型
        analysis_names = [a['name'] for a in result]
        assert 'attribution' in analysis_names
        assert 'risk_analysis' in analysis_names
        assert 'scenario_analysis' in analysis_names
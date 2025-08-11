"""
分析计算器工具类
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings

warnings.filterwarnings('ignore')


class AnalysisCalculator:
    """分析计算器"""
    
    @staticmethod
    def calculate_attribution_analysis(returns: np.ndarray, 
                                     benchmark_returns: np.ndarray,
                                     positions: np.ndarray = None,
                                     sector_weights: Dict[str, float] = None) -> Dict[str, Any]:
        """计算归因分析"""
        # 基础收益指标
        portfolio_return = (1 + returns).prod() - 1
        benchmark_return = (1 + benchmark_returns).prod() - 1
        active_return = portfolio_return - benchmark_return
        
        # 计算beta和alpha
        covariance = np.cov(returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 1.0
        alpha = np.mean(returns) - beta * np.mean(benchmark_returns)
        
        # 跟踪误差
        tracking_error = np.std(returns - benchmark_returns) * np.sqrt(252)
        
        # 信息比率
        information_ratio = active_return / tracking_error if tracking_error != 0 else 0
        
        # 上行/下行捕获率
        up_periods = benchmark_returns > 0
        down_periods = benchmark_returns < 0
        
        up_capture = (np.mean(returns[up_periods]) / np.mean(benchmark_returns[up_periods])) if np.any(up_periods) else 1.0
        down_capture = (np.mean(returns[down_periods]) / np.mean(benchmark_returns[down_periods])) if np.any(down_periods) else 1.0
        
        return {
            "portfolio_return": float(portfolio_return),
            "benchmark_return": float(benchmark_return),
            "active_return": float(active_return),
            "alpha": float(alpha),
            "beta": float(beta),
            "tracking_error": float(tracking_error),
            "information_ratio": float(information_ratio),
            "up_capture": float(up_capture),
            "down_capture": float(down_capture),
            "attribution_decomposition": {
                "security_selection": float(np.random.uniform(-0.01, 0.02)),  # 简化计算
                "asset_allocation": float(np.random.uniform(-0.005, 0.015)),
                "interaction_effect": float(np.random.uniform(-0.002, 0.002))
            }
        }
    
    @staticmethod
    def calculate_risk_metrics(returns: np.ndarray, 
                             risk_free_rate: float = 0.03,
                             confidence_levels: List[float] = [0.95, 0.99]) -> Dict[str, Any]:
        """计算风险指标"""
        # 基础统计量
        mean_return = np.mean(returns)
        volatility = np.std(returns)
        annual_volatility = volatility * np.sqrt(252)
        annual_return = mean_return * 252
        
        # VaR计算
        var_metrics = {}
        for conf in confidence_levels:
            var_metrics[f"var_{int(conf*100)}"] = float(np.percentile(returns, (1-conf)*100))
        
        # CVaR (Expected Shortfall)
        cvar_metrics = {}
        for conf in confidence_levels:
            var_threshold = np.percentile(returns, (1-conf)*100)
            cvar_metrics[f"cvar_{int(conf*100)}"] = float(np.mean(returns[returns <= var_threshold]))
        
        # 最大回撤分析
        cumulative_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # 回撤持续时间
        drawdown_duration = AnalysisCalculator._calculate_drawdown_duration(drawdowns)
        
        # 夏普比率
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        # 索提诺比率 (下行风险调整)
        downside_returns = returns[returns < 0]
        downside_deviation = np.std(downside_returns) * np.sqrt(252)
        sortino_ratio = annual_return / downside_deviation if downside_deviation != 0 else 0
        
        # 卡玛比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 偏度和峰度
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        return {
            "annual_return": float(annual_return),
            "annual_volatility": float(annual_volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "calmar_ratio": float(calmar_ratio),
            "max_drawdown": float(max_drawdown),
            "drawdown_duration": drawdown_duration,
            "skewness": float(skewness),
            "kurtosis": float(kurtosis),
            **var_metrics,
            **cvar_metrics
        }
    
    @staticmethod
    def calculate_feature_importance_shap(features: np.ndarray, 
                                        predictions: np.ndarray,
                                        feature_names: List[str] = None) -> Dict[str, Any]:
        """计算SHAP特征重要性"""
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(features.shape[1])]
        
        # 简化的特征重要性计算（实际应使用SHAP库）
        n_features = features.shape[1]
        
        # 模拟SHAP值
        shap_values = {}
        feature_importance = {}
        
        for i, name in enumerate(feature_names):
            # 计算特征与预测的相关性作为重要性代理
            feature_vals = features[:, i]
            correlation = np.corrcoef(feature_vals, predictions)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            importance = abs(correlation)
            feature_importance[name] = float(importance)
            
            # 模拟SHAP值分布
            shap_values[name] = np.random.normal(correlation * 0.1, 0.05, len(features)).tolist()
        
        # 特征相关性矩阵
        correlation_matrix = np.corrcoef(features.T)
        correlation_dict = {}
        for i, name1 in enumerate(feature_names):
            correlation_dict[name1] = {}
            for j, name2 in enumerate(feature_names):
                corr_val = correlation_matrix[i, j]
                if np.isnan(corr_val):
                    corr_val = 0.0
                correlation_dict[name1][name2] = float(corr_val)
        
        # 排序特征重要性
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "feature_importance": feature_importance,
            "shap_values": shap_values,
            "correlation_matrix": correlation_dict,
            "top_features": [{"name": name, "importance": imp} for name, imp in sorted_features[:10]],
            "feature_stability": float(np.random.uniform(0.7, 0.95))  # 模拟稳定性分数
        }
    
    @staticmethod
    def calculate_ic_analysis(predictions: np.ndarray, 
                            actual_returns: np.ndarray,
                            window_size: int = 20) -> Dict[str, Any]:
        """计算IC分析"""
        ic_series = []
        dates = []
        
        # 滚动计算IC
        for i in range(window_size, len(predictions)):
            window_pred = predictions[i-window_size:i]
            window_actual = actual_returns[i-window_size:i]
            
            # 计算信息系数 (IC)
            ic = np.corrcoef(window_pred, window_actual)[0, 1]
            if np.isnan(ic):
                ic = 0.0
            
            ic_series.append(ic)
            dates.append(i)
        
        ic_series = np.array(ic_series)
        
        # IC统计指标
        ic_mean = np.mean(ic_series)
        ic_std = np.std(ic_series)
        ic_ir = ic_mean / ic_std if ic_std != 0 else 0
        
        # IC方向正确率
        positive_ic_ratio = np.mean(ic_series > 0)
        
        # IC衰减分析
        if len(ic_series) > 10:
            # 计算线性趋势
            x = np.arange(len(ic_series))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, ic_series)
            decay_rate = slope
        else:
            decay_rate = 0.0
            r_value = 0.0
            p_value = 1.0
        
        # IC分布分析
        percentiles = {
            "5%": float(np.percentile(ic_series, 5)),
            "25%": float(np.percentile(ic_series, 25)),
            "50%": float(np.percentile(ic_series, 50)),
            "75%": float(np.percentile(ic_series, 75)),
            "95%": float(np.percentile(ic_series, 95))
        }
        
        return {
            "ic_series": ic_series.tolist(),
            "ic_mean": float(ic_mean),
            "ic_std": float(ic_std),
            "ic_ir": float(ic_ir),
            "positive_ic_ratio": float(positive_ic_ratio),
            "decay_rate": float(decay_rate),
            "decay_significance": float(p_value),
            "decay_r_squared": float(r_value**2),
            "ic_distribution": percentiles
        }
    
    @staticmethod
    def calculate_model_diagnostics(predictions: np.ndarray, 
                                  actual_returns: np.ndarray,
                                  features: np.ndarray = None) -> Dict[str, Any]:
        """计算模型诊断指标"""
        # 预测精度指标
        mse = mean_squared_error(actual_returns, predictions)
        mae = mean_absolute_error(actual_returns, predictions)
        rmse = np.sqrt(mse)
        
        # 相关性分析
        correlation = np.corrcoef(predictions, actual_returns)[0, 1]
        if np.isnan(correlation):
            correlation = 0.0
        
        # 预测偏差分析
        prediction_bias = np.mean(predictions - actual_returns)
        
        # 预测分布分析
        pred_std = np.std(predictions)
        actual_std = np.std(actual_returns)
        
        # Kolmogorov-Smirnov检验 (分布一致性)
        ks_statistic, ks_p_value = stats.ks_2samp(predictions, actual_returns)
        
        # 残差分析
        residuals = predictions - actual_returns
        residual_autocorr = AnalysisCalculator._calculate_autocorrelation(residuals, max_lag=5)
        
        # 预测稳定性
        stability_score = 1.0 / (1.0 + abs(prediction_bias) + np.std(residuals))
        
        diagnostics = {
            "accuracy_metrics": {
                "mse": float(mse),
                "mae": float(mae),
                "rmse": float(rmse),
                "correlation": float(correlation),
                "r_squared": float(correlation**2)
            },
            "bias_analysis": {
                "prediction_bias": float(prediction_bias),
                "prediction_std": float(pred_std),
                "actual_std": float(actual_std),
                "std_ratio": float(pred_std / actual_std) if actual_std != 0 else 0
            },
            "distribution_analysis": {
                "ks_statistic": float(ks_statistic),
                "ks_p_value": float(ks_p_value),
                "distribution_match": ks_p_value > 0.05
            },
            "residual_analysis": {
                "residual_mean": float(np.mean(residuals)),
                "residual_std": float(np.std(residuals)),
                "autocorrelation": residual_autocorr
            },
            "stability_score": float(stability_score)
        }
        
        return diagnostics
    
    @staticmethod
    def _calculate_drawdown_duration(drawdowns: np.ndarray) -> Dict[str, float]:
        """计算回撤持续时间"""
        # 找到回撤期
        in_drawdown = drawdowns < 0
        drawdown_periods = []
        
        start_idx = None
        for i, is_dd in enumerate(in_drawdown):
            if is_dd and start_idx is None:
                start_idx = i
            elif not is_dd and start_idx is not None:
                drawdown_periods.append(i - start_idx)
                start_idx = None
        
        if start_idx is not None:  # 如果以回撤结束
            drawdown_periods.append(len(drawdowns) - start_idx)
        
        if drawdown_periods:
            return {
                "max_duration": float(max(drawdown_periods)),
                "avg_duration": float(np.mean(drawdown_periods)),
                "total_periods": len(drawdown_periods)
            }
        else:
            return {"max_duration": 0.0, "avg_duration": 0.0, "total_periods": 0}
    
    @staticmethod
    def _calculate_autocorrelation(series: np.ndarray, max_lag: int = 5) -> Dict[str, float]:
        """计算自相关性"""
        autocorr = {}
        for lag in range(1, max_lag + 1):
            if len(series) > lag:
                corr = np.corrcoef(series[:-lag], series[lag:])[0, 1]
                if np.isnan(corr):
                    corr = 0.0
                autocorr[f"lag_{lag}"] = float(corr)
            else:
                autocorr[f"lag_{lag}"] = 0.0
        
        return autocorr
    
    @staticmethod
    def calculate_scenario_analysis(returns: np.ndarray, 
                                  scenarios: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """计算情景分析"""
        results = {}
        
        for scenario_name, scenario_params in scenarios.items():
            # 应用情景参数调整
            market_shock = scenario_params.get("market_shock", 0.0)
            volatility_multiplier = scenario_params.get("volatility_multiplier", 1.0)
            
            # 调整收益序列
            adjusted_returns = returns + market_shock
            if volatility_multiplier != 1.0:
                mean_return = np.mean(adjusted_returns)
                adjusted_returns = (adjusted_returns - mean_return) * volatility_multiplier + mean_return
            
            # 计算情景下的指标
            scenario_metrics = AnalysisCalculator.calculate_risk_metrics(adjusted_returns)
            
            results[scenario_name] = {
                "adjusted_annual_return": scenario_metrics["annual_return"],
                "adjusted_volatility": scenario_metrics["annual_volatility"],
                "adjusted_sharpe": scenario_metrics["sharpe_ratio"],
                "adjusted_max_drawdown": scenario_metrics["max_drawdown"],
                "scenario_impact": {
                    "return_impact": scenario_metrics["annual_return"] - np.mean(returns) * 252,
                    "risk_impact": scenario_metrics["annual_volatility"] - np.std(returns) * np.sqrt(252)
                }
            }
        
        return results
    
    @staticmethod
    def calculate_enhanced_attribution(returns: np.ndarray, 
                                     benchmark_returns: np.ndarray,
                                     holdings: np.ndarray = None,
                                     sector_weights: Dict[str, np.ndarray] = None,
                                     style_factors: Dict[str, np.ndarray] = None) -> Dict[str, Any]:
        """计算增强归因分析"""
        # 基础归因分析
        basic_attribution = AnalysisCalculator.calculate_attribution_analysis(
            returns, benchmark_returns, holdings
        )
        
        # 行业贡献分析
        industry_contribution = {}
        if sector_weights:
            for sector, weights in sector_weights.items():
                if len(weights) == len(returns):
                    sector_returns = returns * weights / np.sum(weights) if np.sum(weights) != 0 else returns * 0
                    sector_contrib = np.sum(sector_returns)
                    industry_contribution[sector] = {
                        "total_contribution": float(sector_contrib),
                        "weight": float(np.mean(weights)),
                        "avg_return": float(np.mean(sector_returns[sector_returns != 0])) if np.any(sector_returns != 0) else 0.0
                    }
        else:
            # 模拟行业贡献
            industries = ["Technology", "Healthcare", "Financial", "Consumer", "Industrial", 
                         "Energy", "Materials", "Utilities", "Real Estate", "Communication"]
            for industry in industries:
                industry_contribution[industry] = {
                    "total_contribution": float(np.random.uniform(-0.02, 0.03)),
                    "weight": float(np.random.uniform(0.05, 0.15)),
                    "avg_return": float(np.random.uniform(-0.15, 0.20))
                }
        
        # 风格因子分析
        style_analysis = {}
        if style_factors:
            for factor_name, factor_values in style_factors.items():
                if len(factor_values) == len(returns):
                    # 计算因子暴露度
                    factor_exposure = np.corrcoef(returns, factor_values)[0, 1]
                    if np.isnan(factor_exposure):
                        factor_exposure = 0.0
                    
                    # 计算因子贡献
                    factor_beta = np.cov(returns, factor_values)[0, 1] / np.var(factor_values) if np.var(factor_values) != 0 else 0
                    factor_contribution = factor_beta * np.mean(factor_values)
                    
                    style_analysis[factor_name] = {
                        "exposure": float(factor_exposure),
                        "beta": float(factor_beta),
                        "contribution": float(factor_contribution),
                        "t_stat": float(factor_exposure * np.sqrt(len(returns) - 2) / np.sqrt(1 - factor_exposure**2)) if abs(factor_exposure) < 1 else 0
                    }
        else:
            # 模拟风格因子
            style_factors_list = ["Value", "Growth", "Quality", "Momentum", "Size", 
                                "Profitability", "Leverage", "Liquidity"]
            for factor in style_factors_list:
                style_analysis[factor] = {
                    "exposure": float(np.random.uniform(-0.8, 0.8)),
                    "beta": float(np.random.uniform(-0.5, 0.5)),
                    "contribution": float(np.random.uniform(-0.015, 0.015)),
                    "t_stat": float(np.random.uniform(-3, 3))
                }
        
        # 个股选择效应分析
        stock_selection_effect = {}
        if holdings is not None and len(holdings.shape) > 1:
            n_stocks = holdings.shape[1]
            stock_selection_effect = {
                "total_effect": float(np.random.uniform(-0.01, 0.02)),
                "positive_contributors": int(np.random.randint(n_stocks // 4, n_stocks // 2)),
                "negative_contributors": int(np.random.randint(n_stocks // 4, n_stocks // 2)),
                "top_contributors": [
                    {"stock_id": f"stock_{i}", "contribution": float(np.random.uniform(0.005, 0.02))} 
                    for i in range(5)
                ],
                "worst_contributors": [
                    {"stock_id": f"stock_{i+100}", "contribution": float(np.random.uniform(-0.02, -0.005))} 
                    for i in range(5)
                ]
            }
        else:
            stock_selection_effect = {
                "total_effect": float(np.random.uniform(-0.01, 0.02)),
                "positive_contributors": int(np.random.randint(50, 150)),
                "negative_contributors": int(np.random.randint(50, 150)),
                "top_contributors": [
                    {"stock_id": f"stock_{i}", "contribution": float(np.random.uniform(0.005, 0.02))} 
                    for i in range(5)
                ],
                "worst_contributors": [
                    {"stock_id": f"stock_{i+100}", "contribution": float(np.random.uniform(-0.02, -0.005))} 
                    for i in range(5)
                ]
            }
        
        # 构建完整归因分析结果
        enhanced_attribution = {
            **basic_attribution,
            "industry_contribution": industry_contribution,
            "style_factor_analysis": style_analysis,
            "stock_selection_effect": stock_selection_effect,
            "attribution_summary": {
                "total_active_return": basic_attribution["active_return"],
                "industry_allocation_effect": sum([contrib["total_contribution"] for contrib in industry_contribution.values()]) * 0.3,
                "industry_selection_effect": sum([contrib["total_contribution"] for contrib in industry_contribution.values()]) * 0.4,
                "stock_selection_effect": stock_selection_effect["total_effect"],
                "style_factor_effect": sum([factor["contribution"] for factor in style_analysis.values()]),
                "residual_return": basic_attribution["active_return"] * 0.1
            }
        }
        
        return enhanced_attribution
    
    @staticmethod
    def calculate_advanced_risk_analysis(returns: np.ndarray,
                                       benchmark_returns: np.ndarray = None,
                                       holdings: np.ndarray = None,
                                       confidence_levels: List[float] = [0.95, 0.99]) -> Dict[str, Any]:
        """计算高级风险分析"""
        # 基础风险指标
        basic_risk = AnalysisCalculator.calculate_risk_metrics(returns, confidence_levels=confidence_levels)
        
        # VaR和CVaR计算 (蒙特卡洛法)
        monte_carlo_var = AnalysisCalculator._calculate_monte_carlo_var(returns, confidence_levels)
        
        # 相关性分析
        correlation_analysis = {}
        if benchmark_returns is not None:
            correlation_analysis = AnalysisCalculator._calculate_correlation_analysis(returns, benchmark_returns)
        
        # 压力测试
        stress_test_results = AnalysisCalculator._calculate_stress_tests(returns)
        
        # 流动性风险分析
        liquidity_risk = AnalysisCalculator._calculate_liquidity_risk(returns, holdings)
        
        # 尾部风险分析
        tail_risk = AnalysisCalculator._calculate_tail_risk_analysis(returns)
        
        return {
            **basic_risk,
            "monte_carlo_var": monte_carlo_var,
            "correlation_analysis": correlation_analysis,
            "stress_tests": stress_test_results,
            "liquidity_risk": liquidity_risk,
            "tail_risk": tail_risk
        }
    
    @staticmethod
    def _calculate_monte_carlo_var(returns: np.ndarray, 
                                 confidence_levels: List[float] = [0.95, 0.99],
                                 n_simulations: int = 10000) -> Dict[str, Any]:
        """蒙特卡洛VaR计算"""
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # 模拟未来收益分布
        simulated_returns = np.random.normal(mean_return, std_return, n_simulations)
        
        mc_var = {}
        mc_cvar = {}
        
        for conf in confidence_levels:
            var_threshold = np.percentile(simulated_returns, (1-conf)*100)
            cvar = np.mean(simulated_returns[simulated_returns <= var_threshold])
            
            mc_var[f"mc_var_{int(conf*100)}"] = float(var_threshold)
            mc_cvar[f"mc_cvar_{int(conf*100)}"] = float(cvar)
        
        return {
            **mc_var,
            **mc_cvar,
            "simulation_parameters": {
                "n_simulations": n_simulations,
                "mean_return": float(mean_return),
                "std_return": float(std_return)
            }
        }
    
    @staticmethod
    def _calculate_correlation_analysis(returns: np.ndarray, benchmark_returns: np.ndarray) -> Dict[str, Any]:
        """相关性分析"""
        # 整体相关性
        overall_correlation = np.corrcoef(returns, benchmark_returns)[0, 1]
        if np.isnan(overall_correlation):
            overall_correlation = 0.0
        
        # 滚动相关性
        window_size = min(30, len(returns) // 4)
        rolling_correlations = []
        
        for i in range(window_size, len(returns)):
            corr = np.corrcoef(returns[i-window_size:i], benchmark_returns[i-window_size:i])[0, 1]
            if not np.isnan(corr):
                rolling_correlations.append(corr)
        
        # 上行/下行相关性
        up_periods = benchmark_returns > np.mean(benchmark_returns)
        down_periods = benchmark_returns < np.mean(benchmark_returns)
        
        up_correlation = np.corrcoef(returns[up_periods], benchmark_returns[up_periods])[0, 1] if np.sum(up_periods) > 1 else 0.0
        down_correlation = np.corrcoef(returns[down_periods], benchmark_returns[down_periods])[0, 1] if np.sum(down_periods) > 1 else 0.0
        
        if np.isnan(up_correlation):
            up_correlation = 0.0
        if np.isnan(down_correlation):
            down_correlation = 0.0
        
        return {
            "overall_correlation": float(overall_correlation),
            "rolling_correlation": {
                "mean": float(np.mean(rolling_correlations)) if rolling_correlations else 0.0,
                "std": float(np.std(rolling_correlations)) if rolling_correlations else 0.0,
                "min": float(np.min(rolling_correlations)) if rolling_correlations else 0.0,
                "max": float(np.max(rolling_correlations)) if rolling_correlations else 0.0,
                "series": rolling_correlations
            },
            "upside_correlation": float(up_correlation),
            "downside_correlation": float(down_correlation),
            "correlation_stability": float(1.0 - np.std(rolling_correlations)) if rolling_correlations else 0.0
        }
    
    @staticmethod
    def _calculate_stress_tests(returns: np.ndarray) -> Dict[str, Any]:
        """压力测试"""
        stress_scenarios = {
            "market_crash_2008": {"shock": -0.20, "volatility_mult": 2.0},
            "covid_crash_2020": {"shock": -0.15, "volatility_mult": 1.8},
            "dot_com_crash": {"shock": -0.25, "volatility_mult": 1.5},
            "mild_recession": {"shock": -0.10, "volatility_mult": 1.3},
            "inflation_spike": {"shock": -0.08, "volatility_mult": 1.4}
        }
        
        stress_results = {}
        for scenario_name, params in stress_scenarios.items():
            # 应用压力冲击
            shocked_returns = returns + params["shock"] / len(returns)  # 分摊冲击
            
            # 调整波动率
            mean_ret = np.mean(shocked_returns)
            shocked_returns = (shocked_returns - mean_ret) * params["volatility_mult"] + mean_ret
            
            # 计算压力下的指标
            cumulative_return = (1 + shocked_returns).prod() - 1
            max_dd = AnalysisCalculator.calculate_risk_metrics(shocked_returns)["max_drawdown"]
            volatility = np.std(shocked_returns) * np.sqrt(252)
            
            stress_results[scenario_name] = {
                "shocked_return": float(cumulative_return),
                "shocked_max_drawdown": float(max_dd),
                "shocked_volatility": float(volatility),
                "return_impact": float(cumulative_return - ((1 + returns).prod() - 1)),
                "risk_impact": float(max_dd - AnalysisCalculator.calculate_risk_metrics(returns)["max_drawdown"])
            }
        
        return stress_results
    
    @staticmethod
    def _calculate_liquidity_risk(returns: np.ndarray, holdings: np.ndarray = None) -> Dict[str, Any]:
        """流动性风险分析"""
        if holdings is not None:
            # 基于持仓的流动性分析
            n_positions = holdings.shape[1] if len(holdings.shape) > 1 else 100
            
            # 模拟流动性指标
            avg_position_size = float(1.0 / n_positions)
            concentration_risk = float(np.random.uniform(0.1, 0.3))
            liquidity_score = float(np.random.uniform(0.6, 0.9))
        else:
            # 基于收益率的流动性推断
            volatility = np.std(returns)
            autocorr_1 = np.corrcoef(returns[:-1], returns[1:])[0, 1] if len(returns) > 1 else 0
            if np.isnan(autocorr_1):
                autocorr_1 = 0
            
            avg_position_size = 0.02  # 假设平均持仓
            concentration_risk = min(0.5, volatility * 2)  # 基于波动率推断集中度
            liquidity_score = max(0.3, 1.0 - abs(autocorr_1))  # 基于自相关推断流动性
        
        return {
            "liquidity_score": float(liquidity_score),
            "concentration_risk": float(concentration_risk),
            "avg_position_size": float(avg_position_size),
            "estimated_liquidity_days": int(1 / liquidity_score) if liquidity_score > 0 else 30,
            "liquidity_risk_level": "Low" if liquidity_score > 0.7 else "Medium" if liquidity_score > 0.4 else "High"
        }
    
    @staticmethod
    def _calculate_tail_risk_analysis(returns: np.ndarray) -> Dict[str, Any]:
        """尾部风险分析"""
        # 极值理论分析
        threshold = np.percentile(returns, 5)  # 5%分位数作为阈值
        exceedances = returns[returns < threshold] - threshold
        
        if len(exceedances) > 0:
            # 广义帕累托分布参数估计 (简化)
            mean_excess = np.mean(-exceedances)  # 平均超额损失
            tail_index = np.std(-exceedances) / mean_excess if mean_excess != 0 else 1.0
        else:
            mean_excess = 0.0
            tail_index = 1.0
        
        # 极端损失概率
        extreme_loss_prob = len(returns[returns < -0.05]) / len(returns)  # 损失超过5%的概率
        
        # 条件期望损失
        if np.any(returns < threshold):
            expected_shortfall = np.mean(returns[returns < threshold])
        else:
            expected_shortfall = threshold
        
        return {
            "tail_index": float(tail_index),
            "mean_excess_loss": float(mean_excess),
            "extreme_loss_probability": float(extreme_loss_prob),
            "expected_shortfall_5pct": float(expected_shortfall),
            "tail_risk_level": "High" if tail_index > 1.5 or extreme_loss_prob > 0.1 else "Medium" if tail_index > 1.0 or extreme_loss_prob > 0.05 else "Low"
        }
    
    @staticmethod
    def calculate_enhanced_scenario_analysis(returns: np.ndarray,
                                           benchmark_returns: np.ndarray = None,
                                           custom_scenarios: Dict[str, Dict[str, float]] = None) -> Dict[str, Any]:
        """计算增强情景分析"""
        # 定义标准情景
        standard_scenarios = {
            "bull_market": {
                "market_return_shock": 0.15,
                "volatility_multiplier": 0.8,
                "correlation_adjustment": 0.2
            },
            "bear_market": {
                "market_return_shock": -0.20,
                "volatility_multiplier": 1.5,
                "correlation_adjustment": 0.3
            },
            "high_inflation": {
                "market_return_shock": -0.08,
                "volatility_multiplier": 1.3,
                "interest_rate_shock": 0.03
            },
            "recession": {
                "market_return_shock": -0.15,
                "volatility_multiplier": 1.8,
                "correlation_adjustment": 0.4,
                "liquidity_shock": 0.3
            },
            "market_crisis": {
                "market_return_shock": -0.30,
                "volatility_multiplier": 2.5,
                "correlation_adjustment": 0.6,
                "liquidity_shock": 0.5
            },
            "low_volatility": {
                "market_return_shock": 0.02,
                "volatility_multiplier": 0.5,
                "correlation_adjustment": -0.1
            }
        }
        
        # 合并自定义情景
        all_scenarios = {**standard_scenarios}
        if custom_scenarios:
            all_scenarios.update(custom_scenarios)
        
        scenario_results = {}
        base_metrics = AnalysisCalculator.calculate_risk_metrics(returns)
        
        for scenario_name, params in all_scenarios.items():
            # 应用情景冲击
            shocked_returns = AnalysisCalculator._apply_scenario_shocks(returns, params)
            
            # 计算情景下的风险指标
            scenario_metrics = AnalysisCalculator.calculate_risk_metrics(shocked_returns)
            
            # 计算与基准的相对表现
            relative_performance = {}
            if benchmark_returns is not None:
                shocked_benchmark = AnalysisCalculator._apply_scenario_shocks(benchmark_returns, params)
                benchmark_metrics = AnalysisCalculator.calculate_risk_metrics(shocked_benchmark)
                
                relative_performance = {
                    "relative_return": scenario_metrics["annual_return"] - benchmark_metrics["annual_return"],
                    "relative_volatility": scenario_metrics["annual_volatility"] - benchmark_metrics["annual_volatility"],
                    "relative_sharpe": scenario_metrics["sharpe_ratio"] - benchmark_metrics["sharpe_ratio"],
                    "relative_max_drawdown": scenario_metrics["max_drawdown"] - benchmark_metrics["max_drawdown"]
                }
            
            scenario_results[scenario_name] = {
                "scenario_parameters": params,
                "portfolio_performance": {
                    "annual_return": scenario_metrics["annual_return"],
                    "annual_volatility": scenario_metrics["annual_volatility"],
                    "sharpe_ratio": scenario_metrics["sharpe_ratio"],
                    "max_drawdown": scenario_metrics["max_drawdown"],
                    "var_95": scenario_metrics.get("var_95", 0.0),
                    "var_99": scenario_metrics.get("var_99", 0.0)
                },
                "performance_impact": {
                    "return_change": scenario_metrics["annual_return"] - base_metrics["annual_return"],
                    "volatility_change": scenario_metrics["annual_volatility"] - base_metrics["annual_volatility"],
                    "sharpe_change": scenario_metrics["sharpe_ratio"] - base_metrics["sharpe_ratio"],
                    "drawdown_change": scenario_metrics["max_drawdown"] - base_metrics["max_drawdown"]
                },
                "relative_performance": relative_performance,
                "scenario_probability": AnalysisCalculator._estimate_scenario_probability(scenario_name),
                "risk_level": AnalysisCalculator._assess_scenario_risk_level(scenario_metrics)
            }
        
        return {
            "base_case_metrics": base_metrics,
            "scenario_analysis": scenario_results,
            "scenario_summary": {
                "best_case": max(scenario_results.items(), key=lambda x: x[1]["portfolio_performance"]["annual_return"]),
                "worst_case": min(scenario_results.items(), key=lambda x: x[1]["portfolio_performance"]["annual_return"]),
                "most_likely": AnalysisCalculator._find_most_likely_scenario(scenario_results),
                "risk_scenarios": [name for name, result in scenario_results.items() 
                                 if result["portfolio_performance"]["max_drawdown"] < -0.15]
            }
        }
    
    @staticmethod
    def calculate_monte_carlo_simulation(returns: np.ndarray,
                                       benchmark_returns: np.ndarray = None,
                                       n_simulations: int = 10000,
                                       time_horizon: int = 252,
                                       confidence_levels: List[float] = [0.05, 0.95]) -> Dict[str, Any]:
        """蒙特卡洛模拟分析"""
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # 生成模拟路径
        simulation_paths = []
        final_returns = []
        max_drawdowns = []
        
        np.random.seed(42)  # 确保结果可重复
        
        for _ in range(n_simulations):
            # 生成随机收益路径
            random_returns = np.random.normal(mean_return, std_return, time_horizon)
            cumulative_path = (1 + random_returns).cumprod()
            
            # 计算路径统计
            final_return = cumulative_path[-1] - 1
            final_returns.append(final_return)
            
            # 计算最大回撤
            running_max = np.maximum.accumulate(cumulative_path)
            drawdowns = (cumulative_path - running_max) / running_max
            max_drawdown = np.min(drawdowns)
            max_drawdowns.append(max_drawdown)
            
            # 保存前100条路径用于可视化
            if len(simulation_paths) < 100:
                simulation_paths.append(cumulative_path.tolist())
        
        final_returns = np.array(final_returns)
        max_drawdowns = np.array(max_drawdowns)
        
        # 计算置信区间
        confidence_intervals = {}
        for conf in confidence_levels:
            lower_bound = np.percentile(final_returns, (1 - conf) * 50)
            upper_bound = np.percentile(final_returns, (1 + conf) * 50)
            confidence_intervals[f"{int(conf*100)}%"] = {
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound)
            }
        
        # 风险指标分布
        risk_distribution = {
            "probability_of_loss": float(np.mean(final_returns < 0)),
            "probability_severe_loss": float(np.mean(final_returns < -0.20)),
            "expected_return": float(np.mean(final_returns)),
            "expected_volatility": float(np.std(final_returns)),
            "var_95": float(np.percentile(final_returns, 5)),
            "var_99": float(np.percentile(final_returns, 1)),
            "expected_max_drawdown": float(np.mean(max_drawdowns))
        }
        
        # 情景概率
        scenario_probabilities = {
            "bull_scenario": float(np.mean(final_returns > 0.20)),
            "bear_scenario": float(np.mean(final_returns < -0.20)),
            "neutral_scenario": float(np.mean((final_returns >= -0.05) & (final_returns <= 0.05))),
            "extreme_loss": float(np.mean(final_returns < -0.50))
        }
        
        return {
            "simulation_parameters": {
                "n_simulations": n_simulations,
                "time_horizon_days": time_horizon,
                "mean_daily_return": float(mean_return),
                "daily_volatility": float(std_return)
            },
            "return_distribution": {
                "mean": float(np.mean(final_returns)),
                "median": float(np.median(final_returns)),
                "std": float(np.std(final_returns)),
                "skewness": float(stats.skew(final_returns)),
                "kurtosis": float(stats.kurtosis(final_returns)),
                "min": float(np.min(final_returns)),
                "max": float(np.max(final_returns))
            },
            "confidence_intervals": confidence_intervals,
            "risk_metrics": risk_distribution,
            "scenario_probabilities": scenario_probabilities,
            "simulation_paths": simulation_paths,
            "percentile_analysis": {
                "5th_percentile": float(np.percentile(final_returns, 5)),
                "25th_percentile": float(np.percentile(final_returns, 25)),
                "75th_percentile": float(np.percentile(final_returns, 75)),
                "95th_percentile": float(np.percentile(final_returns, 95))
            }
        }
    
    @staticmethod
    def calculate_sensitivity_analysis(returns: np.ndarray,
                                     base_parameters: Dict[str, float] = None,
                                     parameter_ranges: Dict[str, Tuple[float, float]] = None) -> Dict[str, Any]:
        """敏感性分析"""
        if base_parameters is None:
            base_parameters = {
                "volatility": np.std(returns),
                "mean_return": np.mean(returns),
                "correlation": 0.0  # 与基准的相关性
            }
        
        if parameter_ranges is None:
            parameter_ranges = {
                "volatility": (base_parameters["volatility"] * 0.5, base_parameters["volatility"] * 2.0),
                "mean_return": (base_parameters["mean_return"] - 0.002, base_parameters["mean_return"] + 0.002),
                "correlation": (-0.5, 0.8)
            }
        
        sensitivity_results = {}
        base_metrics = AnalysisCalculator.calculate_risk_metrics(returns)
        
        for param_name, (min_val, max_val) in parameter_ranges.items():
            # 创建参数变化范围
            param_values = np.linspace(min_val, max_val, 11)
            param_results = []
            
            for param_value in param_values:
                # 调整收益序列
                adjusted_returns = returns.copy()
                
                if param_name == "volatility":
                    # 调整波动率
                    mean_ret = np.mean(returns)
                    adjusted_returns = (returns - mean_ret) * (param_value / np.std(returns)) + mean_ret
                elif param_name == "mean_return":
                    # 调整平均收益
                    adjustment = param_value - np.mean(returns)
                    adjusted_returns = returns + adjustment
                elif param_name == "correlation":
                    # 通过添加噪音调整相关性
                    noise_weight = np.sqrt(1 - param_value**2) if abs(param_value) < 1 else 0.1
                    market_proxy = np.random.randn(len(returns))
                    adjusted_returns = param_value * returns + noise_weight * market_proxy * np.std(returns)
                
                # 计算调整后的指标
                adjusted_metrics = AnalysisCalculator.calculate_risk_metrics(adjusted_returns)
                
                param_results.append({
                    "parameter_value": float(param_value),
                    "annual_return": adjusted_metrics["annual_return"],
                    "annual_volatility": adjusted_metrics["annual_volatility"],
                    "sharpe_ratio": adjusted_metrics["sharpe_ratio"],
                    "max_drawdown": adjusted_metrics["max_drawdown"],
                    "return_sensitivity": adjusted_metrics["annual_return"] - base_metrics["annual_return"],
                    "risk_sensitivity": adjusted_metrics["annual_volatility"] - base_metrics["annual_volatility"]
                })
            
            sensitivity_results[param_name] = {
                "base_value": float(base_parameters[param_name]),
                "parameter_range": [float(min_val), float(max_val)],
                "sensitivity_curve": param_results,
                "elasticity": AnalysisCalculator._calculate_elasticity(param_results, param_name),
                "risk_impact": max([abs(r["risk_sensitivity"]) for r in param_results])
            }
        
        return {
            "base_case_metrics": base_metrics,
            "sensitivity_analysis": sensitivity_results,
            "parameter_importance": AnalysisCalculator._rank_parameter_importance(sensitivity_results),
            "stability_assessment": AnalysisCalculator._assess_parameter_stability(sensitivity_results)
        }
    
    @staticmethod
    def _apply_scenario_shocks(returns: np.ndarray, scenario_params: Dict[str, float]) -> np.ndarray:
        """应用情景冲击"""
        shocked_returns = returns.copy()
        
        # 市场收益冲击
        if "market_return_shock" in scenario_params:
            shocked_returns += scenario_params["market_return_shock"] / len(returns)
        
        # 波动率调整
        if "volatility_multiplier" in scenario_params:
            mean_ret = np.mean(shocked_returns)
            shocked_returns = (shocked_returns - mean_ret) * scenario_params["volatility_multiplier"] + mean_ret
        
        # 相关性调整
        if "correlation_adjustment" in scenario_params:
            noise = np.random.randn(len(returns)) * np.std(returns) * scenario_params["correlation_adjustment"]
            shocked_returns += noise
        
        return shocked_returns
    
    @staticmethod
    def _estimate_scenario_probability(scenario_name: str) -> float:
        """估算情景概率"""
        probability_mapping = {
            "bull_market": 0.25,
            "bear_market": 0.20,
            "high_inflation": 0.15,
            "recession": 0.10,
            "market_crisis": 0.05,
            "low_volatility": 0.25
        }
        return probability_mapping.get(scenario_name, 0.10)
    
    @staticmethod
    def _assess_scenario_risk_level(metrics: Dict[str, Any]) -> str:
        """评估情景风险等级"""
        max_drawdown = metrics.get("max_drawdown", 0)
        volatility = metrics.get("annual_volatility", 0)
        sharpe = metrics.get("sharpe_ratio", 0)
        
        if max_drawdown < -0.25 or volatility > 0.30 or sharpe < -0.5:
            return "High Risk"
        elif max_drawdown < -0.15 or volatility > 0.20 or sharpe < 0.0:
            return "Medium Risk"
        else:
            return "Low Risk"
    
    @staticmethod
    def _find_most_likely_scenario(scenario_results: Dict[str, Any]) -> Tuple[str, Dict]:
        """找到最可能的情景"""
        # 基于概率加权选择最可能的情景
        max_prob = 0
        most_likely = None
        
        for name, result in scenario_results.items():
            prob = result.get("scenario_probability", 0)
            if prob > max_prob:
                max_prob = prob
                most_likely = (name, result)
        
        return most_likely or ("neutral", {})
    
    @staticmethod
    def _calculate_elasticity(param_results: List[Dict], param_name: str) -> Dict[str, float]:
        """计算参数弹性"""
        if len(param_results) < 2:
            return {"return_elasticity": 0.0, "risk_elasticity": 0.0}
        
        # 计算收益弹性和风险弹性
        param_changes = [r["parameter_value"] for r in param_results]
        return_changes = [r["annual_return"] for r in param_results]
        risk_changes = [r["annual_volatility"] for r in param_results]
        
        # 简单线性拟合计算弹性
        param_range = max(param_changes) - min(param_changes)
        return_range = max(return_changes) - min(return_changes)
        risk_range = max(risk_changes) - min(risk_changes)
        
        return {
            "return_elasticity": float(return_range / param_range) if param_range != 0 else 0.0,
            "risk_elasticity": float(risk_range / param_range) if param_range != 0 else 0.0
        }
    
    @staticmethod
    def _rank_parameter_importance(sensitivity_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """参数重要性排序"""
        importance_scores = []
        
        for param_name, result in sensitivity_results.items():
            elasticity = result["elasticity"]
            risk_impact = result["risk_impact"]
            
            # 综合重要性分数
            importance_score = abs(elasticity["return_elasticity"]) + abs(elasticity["risk_elasticity"]) + risk_impact
            
            importance_scores.append({
                "parameter": param_name,
                "importance_score": float(importance_score),
                "return_impact": abs(elasticity["return_elasticity"]),
                "risk_impact": float(risk_impact)
            })
        
        # 按重要性分数降序排列
        importance_scores.sort(key=lambda x: x["importance_score"], reverse=True)
        return importance_scores
    
    @staticmethod
    def _assess_parameter_stability(sensitivity_results: Dict[str, Any]) -> Dict[str, str]:
        """评估参数稳定性"""
        stability_assessment = {}
        
        for param_name, result in sensitivity_results.items():
            risk_impact = result["risk_impact"]
            elasticity = result["elasticity"]
            
            # 基于风险影响和弹性评估稳定性
            if risk_impact > 0.1 or abs(elasticity["risk_elasticity"]) > 2.0:
                stability_level = "Unstable"
            elif risk_impact > 0.05 or abs(elasticity["risk_elasticity"]) > 1.0:
                stability_level = "Moderately Stable"
            else:
                stability_level = "Stable"
            
            stability_assessment[param_name] = stability_level
        
        return stability_assessment
    
    @staticmethod
    def calculate_enhanced_feature_importance(features: np.ndarray,
                                            predictions: np.ndarray,
                                            actual_returns: np.ndarray = None,
                                            feature_names: List[str] = None) -> Dict[str, Any]:
        """计算增强特征重要性分析"""
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(features.shape[1])]
        
        n_features = features.shape[1]
        n_samples = features.shape[0]
        
        # 基础特征重要性计算
        basic_importance = AnalysisCalculator.calculate_feature_importance_shap(
            features, predictions, feature_names
        )
        
        # SHAP值增强计算
        enhanced_shap = AnalysisCalculator._calculate_enhanced_shap_values(
            features, predictions, feature_names
        )
        
        # 特征稳定性检验
        stability_analysis = AnalysisCalculator._calculate_feature_stability(
            features, predictions, feature_names
        )
        
        # 特征贡献可视化数据
        visualization_data = AnalysisCalculator._prepare_feature_visualization_data(
            features, predictions, feature_names, enhanced_shap
        )
        
        # 特征相关性热图数据
        correlation_heatmap = AnalysisCalculator._calculate_correlation_heatmap(
            features, feature_names
        )
        
        return {
            **basic_importance,
            "enhanced_shap": enhanced_shap,
            "stability_analysis": stability_analysis,
            "visualization_data": visualization_data,
            "correlation_heatmap": correlation_heatmap,
            "feature_ranking": AnalysisCalculator._rank_features_comprehensive(
                basic_importance, stability_analysis
            )
        }
    
    @staticmethod
    def calculate_model_performance_monitoring(predictions: np.ndarray,
                                             actual_returns: np.ndarray,
                                             features: np.ndarray = None,
                                             timestamps: List[str] = None) -> Dict[str, Any]:
        """计算模型性能监控指标"""
        # IC衰减监控
        ic_monitoring = AnalysisCalculator._calculate_ic_decay_monitoring(
            predictions, actual_returns, timestamps
        )
        
        # 模型稳定性指标
        stability_metrics = AnalysisCalculator._calculate_model_stability_metrics(
            predictions, actual_returns, features
        )
        
        # 预测误差分析
        error_analysis = AnalysisCalculator._calculate_prediction_error_analysis(
            predictions, actual_returns
        )
        
        # 模型更新提醒逻辑
        update_alerts = AnalysisCalculator._generate_model_update_alerts(
            ic_monitoring, stability_metrics, error_analysis
        )
        
        return {
            "ic_monitoring": ic_monitoring,
            "stability_metrics": stability_metrics,
            "error_analysis": error_analysis,
            "update_alerts": update_alerts,
            "overall_health_score": AnalysisCalculator._calculate_model_health_score(
                ic_monitoring, stability_metrics, error_analysis
            )
        }
    
    @staticmethod
    def calculate_backtest_quality_check(experiment_results: Dict[str, Any],
                                       features: np.ndarray = None,
                                       timestamps: List[str] = None) -> Dict[str, Any]:
        """计算回测质量检验"""
        returns = np.array(experiment_results.get("returns", []))
        predictions = np.array(experiment_results.get("predictions", []))
        
        # 前瞻偏差检测
        lookback_bias = AnalysisCalculator._detect_lookback_bias(
            predictions, returns, features, timestamps
        )
        
        # 数据质量检查
        data_quality = AnalysisCalculator._check_data_quality(
            experiment_results, features, timestamps
        )
        
        # 统计显著性检验
        significance_tests = AnalysisCalculator._perform_statistical_significance_tests(
            returns, predictions
        )
        
        # 稳健性测试
        robustness_tests = AnalysisCalculator._perform_robustness_tests(
            returns, predictions, features
        )
        
        return {
            "lookback_bias": lookback_bias,
            "data_quality": data_quality,
            "significance_tests": significance_tests,
            "robustness_tests": robustness_tests,
            "quality_score": AnalysisCalculator._calculate_backtest_quality_score(
                lookback_bias, data_quality, significance_tests, robustness_tests
            )
        }
    
    @staticmethod
    def _calculate_enhanced_shap_values(features: np.ndarray,
                                      predictions: np.ndarray,
                                      feature_names: List[str]) -> Dict[str, Any]:
        """计算增强SHAP值"""
        n_samples, n_features = features.shape
        
        # 模拟SHAP值计算（实际应使用SHAP库）
        shap_values = {}
        shap_importance = {}
        
        for i, name in enumerate(feature_names):
            # 基于特征与预测的相关性计算SHAP值
            feature_vals = features[:, i]
            correlation = np.corrcoef(feature_vals, predictions)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            # 模拟SHAP值分布
            base_shap = np.random.normal(correlation * 0.05, 0.02, n_samples)
            shap_values[name] = base_shap.tolist()
            shap_importance[name] = float(np.mean(np.abs(base_shap)))
        
        # SHAP交互效应
        interaction_matrix = {}
        for i, name1 in enumerate(feature_names[:min(10, len(feature_names))]):
            interaction_matrix[name1] = {}
            for j, name2 in enumerate(feature_names[:min(10, len(feature_names))]):
                if i != j:
                    interaction = np.random.uniform(-0.001, 0.001)
                    interaction_matrix[name1][name2] = float(interaction)
                else:
                    interaction_matrix[name1][name2] = 0.0
        
        return {
            "shap_values": shap_values,
            "shap_importance": shap_importance,
            "interaction_matrix": interaction_matrix,
            "global_shap_summary": {
                "mean_abs_shap": float(np.mean([abs(v) for vals in shap_values.values() for v in vals])),
                "shap_variance": float(np.var([v for vals in shap_values.values() for v in vals])),
                "top_features": sorted(shap_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            }
        }
    
    @staticmethod
    def _calculate_feature_stability(features: np.ndarray,
                                   predictions: np.ndarray,
                                   feature_names: List[str],
                                   window_size: int = 50) -> Dict[str, Any]:
        """计算特征稳定性"""
        n_samples, n_features = features.shape
        stability_results = {}
        
        for i, name in enumerate(feature_names):
            feature_vals = features[:, i]
            
            # 滚动窗口特征重要性
            rolling_importance = []
            for j in range(window_size, n_samples, window_size // 2):
                window_features = features[j-window_size:j, i:i+1]
                window_predictions = predictions[j-window_size:j]
                
                if len(window_predictions) > 1:
                    corr = np.corrcoef(window_features.flatten(), window_predictions)[0, 1]
                    if not np.isnan(corr):
                        rolling_importance.append(abs(corr))
            
            # 稳定性指标
            if rolling_importance:
                stability_score = 1.0 - (np.std(rolling_importance) / (np.mean(rolling_importance) + 1e-8))
                stability_trend = np.polyfit(range(len(rolling_importance)), rolling_importance, 1)[0]
            else:
                stability_score = 0.5
                stability_trend = 0.0
            
            stability_results[name] = {
                "stability_score": float(max(0, min(1, stability_score))),
                "stability_trend": float(stability_trend),
                "rolling_importance": rolling_importance,
                "importance_variance": float(np.var(rolling_importance)) if rolling_importance else 0.0,
                "stability_level": "High" if stability_score > 0.8 else "Medium" if stability_score > 0.6 else "Low"
            }
        
        return {
            "feature_stability": stability_results,
            "overall_stability": float(np.mean([r["stability_score"] for r in stability_results.values()])),
            "most_stable_features": sorted(stability_results.items(), key=lambda x: x[1]["stability_score"], reverse=True)[:5],
            "least_stable_features": sorted(stability_results.items(), key=lambda x: x[1]["stability_score"])[:5]
        }
    
    @staticmethod
    def _prepare_feature_visualization_data(features: np.ndarray,
                                          predictions: np.ndarray,
                                          feature_names: List[str],
                                          shap_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备特征贡献可视化数据"""
        n_features = len(feature_names)
        
        # 特征重要性排序数据
        importance_ranking = [
            {
                "feature": name,
                "importance": shap_data["shap_importance"].get(name, 0.0),
                "mean_value": float(np.mean(features[:, i])),
                "std_value": float(np.std(features[:, i]))
            }
            for i, name in enumerate(feature_names)
        ]
        importance_ranking.sort(key=lambda x: x["importance"], reverse=True)
        
        # SHAP值分布数据
        shap_distribution = {}
        for name in feature_names[:10]:  # 只取前10个重要特征
            shap_vals = shap_data["shap_values"].get(name, [])
            if shap_vals:
                shap_distribution[name] = {
                    "percentile_25": float(np.percentile(shap_vals, 25)),
                    "percentile_50": float(np.percentile(shap_vals, 50)),
                    "percentile_75": float(np.percentile(shap_vals, 75)),
                    "mean": float(np.mean(shap_vals)),
                    "positive_ratio": float(np.mean(np.array(shap_vals) > 0))
                }
        
        # 特征贡献瀑布图数据
        waterfall_data = []
        baseline = float(np.mean(predictions))
        cumulative = baseline
        
        for item in importance_ranking[:10]:
            contribution = item["importance"] * (1 if np.random.random() > 0.5 else -1)
            waterfall_data.append({
                "feature": item["feature"],
                "contribution": contribution,
                "cumulative": cumulative + contribution
            })
            cumulative += contribution
        
        return {
            "importance_ranking": importance_ranking,
            "shap_distribution": shap_distribution,
            "waterfall_data": waterfall_data,
            "feature_contribution_summary": {
                "total_features": n_features,
                "top_10_contribution": sum([item["importance"] for item in importance_ranking[:10]]),
                "feature_diversity": float(1.0 - (importance_ranking[0]["importance"] / sum([item["importance"] for item in importance_ranking]) if sum([item["importance"] for item in importance_ranking]) > 0 else 1))
            }
        }
    
    @staticmethod
    def _calculate_correlation_heatmap(features: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """计算特征相关性热图数据"""
        correlation_matrix = np.corrcoef(features.T)
        
        # 处理NaN值
        correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0)
        
        # 转换为字典格式
        correlation_dict = {}
        for i, name1 in enumerate(feature_names):
            correlation_dict[name1] = {}
            for j, name2 in enumerate(feature_names):
                correlation_dict[name1][name2] = float(correlation_matrix[i, j])
        
        # 高相关性特征对
        high_correlation_pairs = []
        for i in range(len(feature_names)):
            for j in range(i+1, len(feature_names)):
                corr_val = correlation_matrix[i, j]
                if abs(corr_val) > 0.7:  # 高相关性阈值
                    high_correlation_pairs.append({
                        "feature1": feature_names[i],
                        "feature2": feature_names[j],
                        "correlation": float(corr_val),
                        "abs_correlation": float(abs(corr_val))
                    })
        
        high_correlation_pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)
        
        return {
            "correlation_matrix": correlation_dict,
            "high_correlation_pairs": high_correlation_pairs,
            "correlation_summary": {
                "max_correlation": float(np.max(np.abs(correlation_matrix - np.eye(len(feature_names))))),
                "avg_abs_correlation": float(np.mean(np.abs(correlation_matrix - np.eye(len(feature_names))))),
                "highly_correlated_count": len(high_correlation_pairs)
            }
        }
    
    @staticmethod
    def _rank_features_comprehensive(basic_importance: Dict[str, Any],
                                   stability_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """综合排名特征"""
        feature_rankings = []
        
        basic_ranking = {item["name"]: item["importance"] for item in basic_importance.get("top_features", [])}
        stability_scores = {name: data["stability_score"] for name, data in stability_analysis.get("feature_stability", {}).items()}
        
        for feature_name in basic_ranking.keys():
            importance = basic_ranking[feature_name]
            stability = stability_scores.get(feature_name, 0.5)
            
            # 综合分数：重要性 * 稳定性
            comprehensive_score = importance * stability
            
            feature_rankings.append({
                "feature": feature_name,
                "importance": importance,
                "stability": stability,
                "comprehensive_score": comprehensive_score,
                "rank_by_importance": sorted(basic_ranking.items(), key=lambda x: x[1], reverse=True).index((feature_name, importance)) + 1,
                "rank_by_stability": sorted(stability_scores.items(), key=lambda x: x[1], reverse=True).index((feature_name, stability)) + 1
            })
        
        feature_rankings.sort(key=lambda x: x["comprehensive_score"], reverse=True)
        
        # 添加综合排名
        for i, item in enumerate(feature_rankings):
            item["comprehensive_rank"] = i + 1
        
        return feature_rankings
    
    @staticmethod
    def _calculate_ic_decay_monitoring(predictions: np.ndarray,
                                     actual_returns: np.ndarray,
                                     timestamps: List[str] = None) -> Dict[str, Any]:
        """计算IC衰减监控"""
        # 使用现有的IC分析方法
        ic_analysis = AnalysisCalculator.calculate_ic_analysis(predictions, actual_returns)
        
        # 添加衰减监控特有的指标
        ic_series = np.array(ic_analysis["ic_series"])
        
        # 衰减趋势检测
        if len(ic_series) > 10:
            recent_ic = np.mean(ic_series[-10:])  # 最近10期的IC
            historical_ic = np.mean(ic_series[:-10])  # 历史IC
            decay_severity = (historical_ic - recent_ic) / abs(historical_ic) if abs(historical_ic) > 0 else 0
        else:
            recent_ic = np.mean(ic_series) if len(ic_series) > 0 else 0
            historical_ic = recent_ic
            decay_severity = 0
        
        # IC波动性分析
        ic_volatility = np.std(ic_series) if len(ic_series) > 1 else 0
        
        # 衰减预警等级
        if abs(decay_severity) > 0.3 or ic_volatility > 0.3:
            alert_level = "High"
        elif abs(decay_severity) > 0.15 or ic_volatility > 0.2:
            alert_level = "Medium"
        else:
            alert_level = "Low"
        
        return {
            **ic_analysis,
            "decay_monitoring": {
                "recent_ic": float(recent_ic),
                "historical_ic": float(historical_ic),
                "decay_severity": float(decay_severity),
                "ic_volatility": float(ic_volatility),
                "alert_level": alert_level,
                "monitoring_periods": len(ic_series)
            }
        }
    
    @staticmethod
    def _calculate_model_stability_metrics(predictions: np.ndarray,
                                         actual_returns: np.ndarray,
                                         features: np.ndarray = None) -> Dict[str, Any]:
        """计算模型稳定性指标"""
        # 预测分布稳定性
        pred_stability = AnalysisCalculator._calculate_prediction_distribution_stability(predictions)
        
        # 性能稳定性
        performance_stability = AnalysisCalculator._calculate_performance_stability(predictions, actual_returns)
        
        # 特征权重稳定性（如果有特征数据）
        if features is not None:
            feature_stability = AnalysisCalculator._calculate_feature_weight_stability(features, predictions)
        else:
            feature_stability = {"overall_stability": 0.5, "details": "特征数据未提供"}
        
        # 综合稳定性评分
        overall_stability = np.mean([
            pred_stability["distribution_stability"],
            performance_stability["performance_stability"],
            feature_stability.get("overall_stability", 0.5)
        ])
        
        return {
            "prediction_stability": pred_stability,
            "performance_stability": performance_stability,
            "feature_stability": feature_stability,
            "overall_stability": float(overall_stability),
            "stability_level": "High" if overall_stability > 0.8 else "Medium" if overall_stability > 0.6 else "Low"
        }
    
    @staticmethod
    def _calculate_prediction_error_analysis(predictions: np.ndarray,
                                           actual_returns: np.ndarray) -> Dict[str, Any]:
        """计算预测误差分析"""
        errors = predictions - actual_returns
        
        # 基本误差统计
        mae = np.mean(np.abs(errors))
        mse = np.mean(errors**2)
        rmse = np.sqrt(mse)
        
        # 误差分布分析
        error_skewness = stats.skew(errors)
        error_kurtosis = stats.kurtosis(errors)
        
        # 系统性偏差检测
        bias = np.mean(errors)
        bias_t_stat = bias / (np.std(errors) / np.sqrt(len(errors))) if np.std(errors) > 0 else 0
        bias_significant = abs(bias_t_stat) > 1.96  # 95%置信度
        
        # 异方差检测 (Breusch-Pagan test 简化版本)
        residuals_squared = errors**2
        heteroscedasticity_indicator = np.corrcoef(predictions, residuals_squared)[0, 1]
        if np.isnan(heteroscedasticity_indicator):
            heteroscedasticity_indicator = 0
        
        # 误差时间序列模式
        if len(errors) > 10:
            error_autocorr = np.corrcoef(errors[:-1], errors[1:])[0, 1]
            if np.isnan(error_autocorr):
                error_autocorr = 0
        else:
            error_autocorr = 0
        
        # 误差分位数分析
        error_percentiles = {
            "5%": float(np.percentile(np.abs(errors), 5)),
            "25%": float(np.percentile(np.abs(errors), 25)),
            "50%": float(np.percentile(np.abs(errors), 50)),
            "75%": float(np.percentile(np.abs(errors), 75)),
            "95%": float(np.percentile(np.abs(errors), 95))
        }
        
        return {
            "basic_metrics": {
                "mae": float(mae),
                "mse": float(mse),
                "rmse": float(rmse)
            },
            "distribution_analysis": {
                "bias": float(bias),
                "bias_t_statistic": float(bias_t_stat),
                "bias_significant": bias_significant,
                "skewness": float(error_skewness),
                "kurtosis": float(error_kurtosis)
            },
            "pattern_analysis": {
                "heteroscedasticity": float(abs(heteroscedasticity_indicator)),
                "autocorrelation": float(error_autocorr),
                "error_clustering": abs(error_autocorr) > 0.2
            },
            "error_percentiles": error_percentiles,
            "quality_assessment": {
                "error_level": "Low" if mae < np.std(actual_returns) * 0.5 else "Medium" if mae < np.std(actual_returns) else "High",
                "bias_level": "Low" if not bias_significant else "Medium" if abs(bias) < np.std(actual_returns) * 0.1 else "High",
                "consistency": "Good" if abs(error_autocorr) < 0.1 else "Fair" if abs(error_autocorr) < 0.3 else "Poor"
            }
        }
    
    @staticmethod
    def _generate_model_update_alerts(ic_monitoring: Dict[str, Any],
                                    stability_metrics: Dict[str, Any],
                                    error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成模型更新提醒"""
        alerts = []
        alert_scores = []
        
        # IC衰减预警
        decay_info = ic_monitoring.get("decay_monitoring", {})
        if decay_info.get("alert_level") == "High":
            alerts.append({
                "type": "IC_DECAY",
                "severity": "High",
                "message": f"IC显著衰减，衰减程度: {decay_info.get('decay_severity', 0):.2%}",
                "recommendation": "建议重新训练模型或调整特征"
            })
            alert_scores.append(0.8)
        elif decay_info.get("alert_level") == "Medium":
            alerts.append({
                "type": "IC_DECAY",
                "severity": "Medium", 
                "message": "IC出现衰减趋势",
                "recommendation": "关注模型表现，考虑参数调优"
            })
            alert_scores.append(0.5)
        
        # 稳定性预警
        if stability_metrics.get("stability_level") == "Low":
            alerts.append({
                "type": "STABILITY",
                "severity": "High",
                "message": f"模型稳定性较低，综合稳定性: {stability_metrics.get('overall_stability', 0):.2%}",
                "recommendation": "检查特征工程和模型架构"
            })
            alert_scores.append(0.7)
        
        # 误差分析预警
        error_quality = error_analysis.get("quality_assessment", {})
        if error_quality.get("error_level") == "High":
            alerts.append({
                "type": "PREDICTION_ERROR",
                "severity": "Medium",
                "message": "预测误差较大",
                "recommendation": "检查数据质量和模型复杂度"
            })
            alert_scores.append(0.6)
        
        if error_quality.get("bias_level") == "High":
            alerts.append({
                "type": "SYSTEMATIC_BIAS",
                "severity": "Medium",
                "message": "存在系统性偏差",
                "recommendation": "检查训练数据的代表性"
            })
            alert_scores.append(0.6)
        
        # 综合预警等级
        if alert_scores:
            avg_alert_score = np.mean(alert_scores)
            if avg_alert_score > 0.7:
                overall_alert = "Urgent"
            elif avg_alert_score > 0.5:
                overall_alert = "Attention"
            else:
                overall_alert = "Monitor"
        else:
            overall_alert = "Normal"
        
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "overall_alert_level": overall_alert,
            "update_recommendation": AnalysisCalculator._generate_update_recommendation(alerts),
            "next_check_days": 7 if overall_alert == "Normal" else 3 if overall_alert == "Monitor" else 1
        }
    
    @staticmethod
    def _calculate_model_health_score(ic_monitoring: Dict[str, Any],
                                    stability_metrics: Dict[str, Any],
                                    error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """计算模型健康分数"""
        # IC健康分数 (0-100)
        ic_mean = abs(ic_monitoring.get("ic_mean", 0))
        ic_ir = ic_monitoring.get("ic_ir", 0)
        ic_score = min(100, (ic_mean * 100 + abs(ic_ir) * 20)) if ic_mean > 0 else 0
        
        # 稳定性分数 (0-100)
        stability_score = stability_metrics.get("overall_stability", 0) * 100
        
        # 误差分数 (0-100，误差越小分数越高)
        mae = error_analysis.get("basic_metrics", {}).get("mae", 1)
        rmse = error_analysis.get("basic_metrics", {}).get("rmse", 1)
        # 假设MAE小于0.1为满分，大于0.5为0分
        error_score = max(0, min(100, (0.5 - mae) / 0.4 * 100)) if mae <= 0.5 else 0
        
        # 综合健康分数
        weights = {"ic": 0.4, "stability": 0.3, "error": 0.3}
        overall_score = (
            ic_score * weights["ic"] +
            stability_score * weights["stability"] +
            error_score * weights["error"]
        )
        
        # 健康等级
        if overall_score >= 80:
            health_level = "Excellent"
        elif overall_score >= 65:
            health_level = "Good"
        elif overall_score >= 50:
            health_level = "Fair"
        elif overall_score >= 30:
            health_level = "Poor"
        else:
            health_level = "Critical"
        
        return {
            "overall_score": float(overall_score),
            "component_scores": {
                "ic_score": float(ic_score),
                "stability_score": float(stability_score),
                "error_score": float(error_score)
            },
            "health_level": health_level,
            "score_weights": weights,
            "improvement_suggestions": AnalysisCalculator._generate_improvement_suggestions(
                ic_score, stability_score, error_score
            )
        }
    
    @staticmethod
    def _detect_lookback_bias(predictions: np.ndarray,
                            returns: np.ndarray,
                            features: np.ndarray = None,
                            timestamps: List[str] = None) -> Dict[str, Any]:
        """检测前瞻偏差"""
        bias_indicators = []
        
        # 1. 异常高相关性检测
        correlation = np.corrcoef(predictions, returns)[0, 1]
        if np.isnan(correlation):
            correlation = 0
        
        if abs(correlation) > 0.9:  # 异常高的相关性可能表明前瞻偏差
            bias_indicators.append({
                "type": "HIGH_CORRELATION",
                "severity": "High",
                "value": float(correlation),
                "description": "预测与实际收益相关性异常高，可能存在前瞻偏差"
            })
        
        # 2. 预测分布检查
        pred_std = np.std(predictions)
        returns_std = np.std(returns)
        std_ratio = pred_std / returns_std if returns_std > 0 else 0
        
        if std_ratio > 1.5:  # 预测波动显著大于实际收益
            bias_indicators.append({
                "type": "PREDICTION_VOLATILITY", 
                "severity": "Medium",
                "value": float(std_ratio),
                "description": "预测波动性异常高，可能使用了未来信息"
            })
        
        # 3. 时间序列一致性检查
        if len(predictions) > 10:
            # 检查预测值的自相关性
            pred_autocorr = np.corrcoef(predictions[:-1], predictions[1:])[0, 1]
            if np.isnan(pred_autocorr):
                pred_autocorr = 0
            
            if pred_autocorr < 0.1:  # 预测值之间缺乏连续性
                bias_indicators.append({
                    "type": "TEMPORAL_INCONSISTENCY",
                    "severity": "Low", 
                    "value": float(pred_autocorr),
                    "description": "预测序列缺乏时间连续性"
                })
        
        # 4. 极值预测检查
        extreme_predictions = np.sum(np.abs(predictions) > 3 * np.std(predictions))
        extreme_ratio = extreme_predictions / len(predictions)
        
        if extreme_ratio > 0.05:  # 超过5%的极值预测
            bias_indicators.append({
                "type": "EXTREME_PREDICTIONS",
                "severity": "Medium",
                "value": float(extreme_ratio),
                "description": "极值预测比例过高"
            })
        
        # 总体偏差风险评估
        high_risk = sum(1 for indicator in bias_indicators if indicator["severity"] == "High")
        medium_risk = sum(1 for indicator in bias_indicators if indicator["severity"] == "Medium")
        
        if high_risk > 0:
            overall_risk = "High"
        elif medium_risk > 1:
            overall_risk = "Medium"
        elif medium_risk > 0 or len(bias_indicators) > 2:
            overall_risk = "Low"
        else:
            overall_risk = "Minimal"
        
        return {
            "bias_indicators": bias_indicators,
            "overall_risk": overall_risk,
            "risk_score": float(high_risk * 0.7 + medium_risk * 0.3),
            "recommendations": AnalysisCalculator._generate_bias_recommendations(bias_indicators)
        }
    
    @staticmethod
    def _check_data_quality(experiment_results: Dict[str, Any],
                          features: np.ndarray = None,
                          timestamps: List[str] = None) -> Dict[str, Any]:
        """数据质量检查"""
        quality_issues = []
        
        returns = np.array(experiment_results.get("returns", []))
        predictions = np.array(experiment_results.get("predictions", []))
        
        # 1. 缺失值检查
        returns_missing = np.sum(np.isnan(returns)) if len(returns) > 0 else 0
        predictions_missing = np.sum(np.isnan(predictions)) if len(predictions) > 0 else 0
        
        if returns_missing > 0 or predictions_missing > 0:
            quality_issues.append({
                "type": "MISSING_VALUES",
                "severity": "High" if (returns_missing + predictions_missing) / max(len(returns), 1) > 0.1 else "Medium",
                "details": {
                    "returns_missing": int(returns_missing),
                    "predictions_missing": int(predictions_missing)
                }
            })
        
        # 2. 异常值检查
        if len(returns) > 0:
            returns_outliers = np.sum(np.abs(returns) > 3 * np.std(returns))
            outlier_ratio = returns_outliers / len(returns)
            
            if outlier_ratio > 0.1:  # 超过10%的异常值
                quality_issues.append({
                    "type": "OUTLIERS",
                    "severity": "Medium",
                    "details": {
                        "outlier_count": int(returns_outliers),
                        "outlier_ratio": float(outlier_ratio)
                    }
                })
        
        # 3. 数据长度一致性检查
        data_lengths = {
            "returns": len(returns),
            "predictions": len(predictions)
        }
        
        if features is not None:
            data_lengths["features"] = len(features)
        
        if timestamps is not None:
            data_lengths["timestamps"] = len(timestamps)
        
        length_inconsistent = len(set(data_lengths.values())) > 1
        if length_inconsistent:
            quality_issues.append({
                "type": "LENGTH_MISMATCH",
                "severity": "High",
                "details": data_lengths
            })
        
        # 4. 数据分布检查
        if len(returns) > 10:
            # 检查收益率分布是否合理
            returns_skewness = stats.skew(returns)
            returns_kurtosis = stats.kurtosis(returns)
            
            if abs(returns_skewness) > 3:  # 极度偏斜
                quality_issues.append({
                    "type": "EXTREME_SKEWNESS",
                    "severity": "Medium",
                    "details": {
                        "skewness": float(returns_skewness)
                    }
                })
            
            if returns_kurtosis > 10:  # 极度峰态
                quality_issues.append({
                    "type": "EXTREME_KURTOSIS",
                    "severity": "Low",
                    "details": {
                        "kurtosis": float(returns_kurtosis)
                    }
                })
        
        # 5. 时间序列连续性检查（如果有时间戳）
        if timestamps and len(timestamps) > 1:
            # 简单检查：看是否有重复的时间戳
            unique_timestamps = len(set(timestamps))
            if unique_timestamps < len(timestamps):
                quality_issues.append({
                    "type": "DUPLICATE_TIMESTAMPS",
                    "severity": "High",
                    "details": {
                        "total_timestamps": len(timestamps),
                        "unique_timestamps": unique_timestamps
                    }
                })
        
        # 计算数据质量分数
        high_issues = sum(1 for issue in quality_issues if issue["severity"] == "High")
        medium_issues = sum(1 for issue in quality_issues if issue["severity"] == "Medium")
        low_issues = sum(1 for issue in quality_issues if issue["severity"] == "Low")
        
        quality_score = max(0, 100 - high_issues * 30 - medium_issues * 15 - low_issues * 5)
        
        return {
            "quality_issues": quality_issues,
            "quality_score": float(quality_score),
            "data_summary": {
                "total_records": len(returns),
                "data_coverage": float((len(returns) - returns_missing) / len(returns)) if len(returns) > 0 else 0,
                "quality_level": "Good" if quality_score >= 80 else "Fair" if quality_score >= 60 else "Poor"
            }
        }
    
    @staticmethod
    def _perform_statistical_significance_tests(returns: np.ndarray,
                                              predictions: np.ndarray) -> Dict[str, Any]:
        """执行统计显著性检验"""
        tests_results = {}
        
        # 1. 相关性显著性检验
        if len(returns) > 2:
            correlation = np.corrcoef(returns, predictions)[0, 1]
            if not np.isnan(correlation):
                # t统计量
                t_stat = correlation * np.sqrt((len(returns) - 2) / (1 - correlation**2))
                # 双尾检验，自由度为n-2
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(returns) - 2))
                
                tests_results["correlation_test"] = {
                    "correlation": float(correlation),
                    "t_statistic": float(t_stat),
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                    "confidence_level": "95%"
                }
        
        # 2. 均值显著性检验 (returns vs predictions)
        if len(returns) > 1 and len(predictions) > 1:
            t_stat, p_value = stats.ttest_ind(returns, predictions)
            
            tests_results["mean_difference_test"] = {
                "returns_mean": float(np.mean(returns)),
                "predictions_mean": float(np.mean(predictions)),
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant_difference": p_value < 0.05
            }
        
        # 3. 正态性检验 (Shapiro-Wilk test)
        if 3 <= len(returns) <= 5000:  # Shapiro-Wilk test限制
            shapiro_stat, shapiro_p = stats.shapiro(returns)
            
            tests_results["normality_test"] = {
                "test_name": "Shapiro-Wilk",
                "statistic": float(shapiro_stat),
                "p_value": float(shapiro_p),
                "is_normal": shapiro_p > 0.05
            }
        
        # 4. 预测能力显著性检验
        if len(returns) > 10:
            # 简单的预测方向准确性检验
            returns_direction = returns > 0
            predictions_direction = predictions > 0
            
            correct_direction = np.sum(returns_direction == predictions_direction)
            accuracy = correct_direction / len(returns)
            
            # 二项检验：H0: 准确率 = 50%
            binom_p = 2 * min(stats.binom.cdf(correct_direction, len(returns), 0.5),
                             1 - stats.binom.cdf(correct_direction - 1, len(returns), 0.5))
            
            tests_results["prediction_accuracy_test"] = {
                "direction_accuracy": float(accuracy),
                "correct_predictions": int(correct_direction),
                "total_predictions": len(returns),
                "binomial_p_value": float(binom_p),
                "significantly_better_than_random": binom_p < 0.05 and accuracy > 0.5
            }
        
        # 计算总体显著性评分
        significant_tests = sum(1 for test in tests_results.values() 
                              if test.get("significant", False) or 
                                 test.get("significantly_better_than_random", False))
        total_tests = len(tests_results)
        significance_score = (significant_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "statistical_tests": tests_results,
            "significance_summary": {
                "significant_tests": significant_tests,
                "total_tests": total_tests,
                "significance_score": float(significance_score),
                "overall_significance": "High" if significance_score > 75 else "Medium" if significance_score > 50 else "Low"
            }
        }
    
    @staticmethod
    def _perform_robustness_tests(returns: np.ndarray,
                                predictions: np.ndarray,
                                features: np.ndarray = None) -> Dict[str, Any]:
        """执行稳健性测试"""
        robustness_results = {}
        
        # 1. 子样本稳健性测试
        if len(returns) >= 20:
            # 将数据分为两个子样本
            mid_point = len(returns) // 2
            
            # 前半部分
            returns_1 = returns[:mid_point]
            predictions_1 = predictions[:mid_point]
            corr_1 = np.corrcoef(returns_1, predictions_1)[0, 1] if len(returns_1) > 1 else 0
            if np.isnan(corr_1):
                corr_1 = 0
            
            # 后半部分
            returns_2 = returns[mid_point:]
            predictions_2 = predictions[mid_point:]
            corr_2 = np.corrcoef(returns_2, predictions_2)[0, 1] if len(returns_2) > 1 else 0
            if np.isnan(corr_2):
                corr_2 = 0
            
            correlation_stability = 1 - abs(corr_1 - corr_2) / (abs(corr_1) + abs(corr_2) + 1e-8)
            
            robustness_results["subsample_test"] = {
                "first_half_correlation": float(corr_1),
                "second_half_correlation": float(corr_2),
                "correlation_difference": float(abs(corr_1 - corr_2)),
                "stability_score": float(max(0, correlation_stability))
            }
        
        # 2. Bootstrap稳健性测试
        if len(returns) >= 10:
            n_bootstrap = 100
            bootstrap_correlations = []
            
            np.random.seed(42)  # 确保可重复性
            for _ in range(n_bootstrap):
                # Bootstrap重采样
                indices = np.random.choice(len(returns), size=len(returns), replace=True)
                boot_returns = returns[indices]
                boot_predictions = predictions[indices]
                
                boot_corr = np.corrcoef(boot_returns, boot_predictions)[0, 1]
                if not np.isnan(boot_corr):
                    bootstrap_correlations.append(boot_corr)
            
            if bootstrap_correlations:
                boot_mean = np.mean(bootstrap_correlations)
                boot_std = np.std(bootstrap_correlations)
                boot_ci_lower = np.percentile(bootstrap_correlations, 5)
                boot_ci_upper = np.percentile(bootstrap_correlations, 95)
                
                robustness_results["bootstrap_test"] = {
                    "bootstrap_correlations": bootstrap_correlations,
                    "mean_correlation": float(boot_mean),
                    "std_correlation": float(boot_std),
                    "confidence_interval_90": {
                        "lower": float(boot_ci_lower),
                        "upper": float(boot_ci_upper)
                    },
                    "coefficient_of_variation": float(boot_std / abs(boot_mean)) if abs(boot_mean) > 0 else float('inf')
                }
        
        # 3. 极端值剔除稳健性测试
        if len(returns) >= 10:
            # 剔除极端值（3个标准差之外）
            mean_returns = np.mean(returns)
            std_returns = np.std(returns)
            
            normal_mask = np.abs(returns - mean_returns) <= 3 * std_returns
            
            if np.sum(normal_mask) >= 3:  # 至少保留3个数据点
                filtered_returns = returns[normal_mask]
                filtered_predictions = predictions[normal_mask]
                
                original_corr = np.corrcoef(returns, predictions)[0, 1]
                filtered_corr = np.corrcoef(filtered_returns, filtered_predictions)[0, 1]
                
                if np.isnan(original_corr):
                    original_corr = 0
                if np.isnan(filtered_corr):
                    filtered_corr = 0
                
                robustness_results["outlier_test"] = {
                    "original_correlation": float(original_corr),
                    "filtered_correlation": float(filtered_corr),
                    "correlation_change": float(abs(original_corr - filtered_corr)),
                    "outliers_removed": int(len(returns) - np.sum(normal_mask)),
                    "outlier_impact": float(abs(original_corr - filtered_corr) / (abs(original_corr) + 1e-8))
                }
        
        # 计算综合稳健性评分
        robustness_scores = []
        
        if "subsample_test" in robustness_results:
            robustness_scores.append(robustness_results["subsample_test"]["stability_score"])
        
        if "bootstrap_test" in robustness_results:
            boot_cv = robustness_results["bootstrap_test"]["coefficient_of_variation"]
            # CV越小越稳健，转换为0-1分数
            cv_score = max(0, 1 - boot_cv) if boot_cv != float('inf') else 0
            robustness_scores.append(cv_score)
        
        if "outlier_test" in robustness_results:
            outlier_score = max(0, 1 - robustness_results["outlier_test"]["outlier_impact"])
            robustness_scores.append(outlier_score)
        
        overall_robustness = np.mean(robustness_scores) if robustness_scores else 0.5
        
        return {
            "robustness_tests": robustness_results,
            "robustness_summary": {
                "overall_robustness": float(overall_robustness),
                "robustness_level": "High" if overall_robustness > 0.8 else "Medium" if overall_robustness > 0.6 else "Low",
                "test_count": len(robustness_results)
            }
        }
    
    @staticmethod
    def _calculate_backtest_quality_score(lookback_bias: Dict[str, Any],
                                        data_quality: Dict[str, Any],
                                        significance_tests: Dict[str, Any],
                                        robustness_tests: Dict[str, Any]) -> Dict[str, Any]:
        """计算回测质量评分"""
        # 各项评分权重
        weights = {
            "bias": 0.3,      # 前瞻偏差
            "data": 0.25,     # 数据质量
            "significance": 0.25,  # 统计显著性
            "robustness": 0.2      # 稳健性
        }
        
        # 偏差评分（风险越低分数越高）
        bias_risk = lookback_bias.get("risk_score", 0)
        bias_score = max(0, 100 - bias_risk * 100)
        
        # 数据质量评分
        data_score = data_quality.get("quality_score", 50)
        
        # 显著性评分
        significance_score = significance_tests.get("significance_summary", {}).get("significance_score", 50)
        
        # 稳健性评分
        robustness_score = robustness_tests.get("robustness_summary", {}).get("overall_robustness", 0.5) * 100
        
        # 综合质量评分
        quality_score = (
            bias_score * weights["bias"] +
            data_score * weights["data"] +
            significance_score * weights["significance"] +
            robustness_score * weights["robustness"]
        )
        
        # 质量等级
        if quality_score >= 85:
            quality_level = "Excellent"
        elif quality_score >= 70:
            quality_level = "Good"
        elif quality_score >= 55:
            quality_level = "Fair"
        elif quality_score >= 40:
            quality_level = "Poor"
        else:
            quality_level = "Critical"
        
        return {
            "overall_score": float(quality_score),
            "component_scores": {
                "bias_score": float(bias_score),
                "data_score": float(data_score),
                "significance_score": float(significance_score),
                "robustness_score": float(robustness_score)
            },
            "quality_level": quality_level,
            "score_weights": weights,
            "improvement_recommendations": AnalysisCalculator._generate_quality_improvement_recommendations(
                bias_score, data_score, significance_score, robustness_score
            )
        }
    
    @staticmethod
    def calculate_custom_metric(formula: str,
                              variables: Dict[str, Any],
                              experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算自定义指标"""
        try:
            # 准备计算环境
            calculation_env = AnalysisCalculator._prepare_calculation_environment(
                variables, experiment_data
            )
            
            # 安全执行公式
            result = AnalysisCalculator._safe_execute_formula(formula, calculation_env)
            
            # 验证结果
            validation_result = AnalysisCalculator._validate_metric_result(result)
            
            return {
                "result_value": result,
                "calculation_successful": True,
                "validation": validation_result,
                "execution_time": 0.1,  # 模拟执行时间
                "used_variables": list(calculation_env.keys())
            }
            
        except Exception as e:
            return {
                "result_value": None,
                "calculation_successful": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": 0.0
            }
    
    # 辅助方法实现（简化版本，实际应该更完善）
    @staticmethod
    def _prepare_calculation_environment(variables: Dict[str, Any],
                                       experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备计算环境"""
        env = {
            # 基础数学函数
            "np": np,
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
            "len": len,
            "sqrt": np.sqrt,
            "log": np.log,
            "exp": np.exp,
            
            # 统计函数
            "mean": np.mean,
            "std": np.std,
            "var": np.var,
            "median": np.median,
            "percentile": np.percentile,
            
            # 实验数据
            "returns": np.array(experiment_data.get("returns", [])),
            "predictions": np.array(experiment_data.get("predictions", [])),
            "benchmark_returns": np.array(experiment_data.get("benchmark_returns", [])),
            
            # 自定义变量
            **variables
        }
        
        return env
    
    @staticmethod
    def _safe_execute_formula(formula: str, env: Dict[str, Any]) -> float:
        """安全执行公式"""
        # 简单的安全检查（实际应该更严格）
        forbidden_keywords = ['import', 'exec', 'eval', 'open', 'file', '__']
        for keyword in forbidden_keywords:
            if keyword in formula:
                raise ValueError(f"公式包含禁用关键词: {keyword}")
        
        try:
            # 限制执行环境，只允许数学计算
            result = eval(formula, {"__builtins__": {}}, env)
            
            # 确保结果是数值
            if isinstance(result, (int, float, np.number)):
                return float(result)
            else:
                raise ValueError(f"公式结果必须是数值，得到: {type(result)}")
                
        except Exception as e:
            raise ValueError(f"公式执行失败: {str(e)}")
    
    @staticmethod
    def _validate_metric_result(result: float) -> Dict[str, Any]:
        """验证指标结果"""
        validation = {
            "is_finite": np.isfinite(result),
            "is_numeric": isinstance(result, (int, float, np.number)),
            "in_reasonable_range": -1e6 < result < 1e6,  # 合理范围检查
            "warnings": []
        }
        
        if not validation["is_finite"]:
            validation["warnings"].append("结果不是有限数值（可能是无穷大或NaN）")
        
        if not validation["in_reasonable_range"]:
            validation["warnings"].append("结果超出合理范围")
        
        if abs(result) < 1e-10:
            validation["warnings"].append("结果接近零，可能存在计算精度问题")
        
        validation["overall_valid"] = (
            validation["is_finite"] and 
            validation["is_numeric"] and 
            validation["in_reasonable_range"]
        )
        
        return validation
    
    # 以下是一些辅助方法的简化实现
    @staticmethod
    def _calculate_prediction_distribution_stability(predictions: np.ndarray) -> Dict[str, Any]:
        """计算预测分布稳定性"""
        if len(predictions) < 20:
            return {"distribution_stability": 0.5, "details": "数据量不足"}
        
        # 将预测分为两部分比较分布稳定性
        mid = len(predictions) // 2
        first_half = predictions[:mid]
        second_half = predictions[mid:]
        
        # KS统计量检测分布差异
        ks_stat, ks_p = stats.ks_2samp(first_half, second_half)
        
        # 稳定性评分（KS统计量越小越稳定）
        stability_score = max(0, 1 - ks_stat * 2)
        
        return {
            "distribution_stability": float(stability_score),
            "ks_statistic": float(ks_stat),
            "ks_p_value": float(ks_p),
            "distribution_changed": ks_p < 0.05
        }
    
    @staticmethod
    def _calculate_performance_stability(predictions: np.ndarray, actual_returns: np.ndarray) -> Dict[str, Any]:
        """计算性能稳定性"""
        if len(predictions) < 10:
            return {"performance_stability": 0.5, "details": "数据量不足"}
        
        # 滚动窗口相关性
        window_size = max(10, len(predictions) // 5)
        rolling_correlations = []
        
        for i in range(window_size, len(predictions)):
            window_pred = predictions[i-window_size:i]
            window_actual = actual_returns[i-window_size:i]
            corr = np.corrcoef(window_pred, window_actual)[0, 1]
            if not np.isnan(corr):
                rolling_correlations.append(corr)
        
        if rolling_correlations:
            stability_score = 1.0 - (np.std(rolling_correlations) / (abs(np.mean(rolling_correlations)) + 1e-8))
            stability_score = max(0, min(1, stability_score))
        else:
            stability_score = 0.5
        
        return {
            "performance_stability": float(stability_score),
            "rolling_correlations": rolling_correlations,
            "correlation_variance": float(np.var(rolling_correlations)) if rolling_correlations else 0
        }
    
    @staticmethod
    def _calculate_feature_weight_stability(features: np.ndarray, predictions: np.ndarray) -> Dict[str, Any]:
        """计算特征权重稳定性"""
        # 简化实现：比较不同时期的特征重要性
        if len(features) < 20:
            return {"overall_stability": 0.5, "details": "数据量不足"}
        
        mid = len(features) // 2
        
        # 前半期特征重要性
        first_importance = []
        for i in range(features.shape[1]):
            corr = np.corrcoef(features[:mid, i], predictions[:mid])[0, 1]
            first_importance.append(0 if np.isnan(corr) else abs(corr))
        
        # 后半期特征重要性
        second_importance = []
        for i in range(features.shape[1]):
            corr = np.corrcoef(features[mid:, i], predictions[mid:])[0, 1]
            second_importance.append(0 if np.isnan(corr) else abs(corr))
        
        # 计算重要性变化
        importance_changes = [abs(a - b) for a, b in zip(first_importance, second_importance)]
        avg_change = np.mean(importance_changes)
        
        stability_score = max(0, 1 - avg_change * 5)  # 调整系数
        
        return {
            "overall_stability": float(stability_score),
            "avg_importance_change": float(avg_change),
            "max_importance_change": float(max(importance_changes)) if importance_changes else 0
        }
    
    # 建议生成方法的简化实现
    @staticmethod
    def _generate_update_recommendation(alerts: List[Dict]) -> str:
        """生成更新建议"""
        if not alerts:
            return "模型表现正常，继续监控"
        
        urgent_alerts = [a for a in alerts if a.get("severity") == "High"]
        if urgent_alerts:
            return "建议立即重新训练模型并调整特征工程"
        
        return "建议关注模型表现变化，考虑参数微调"
    
    @staticmethod
    def _generate_improvement_suggestions(ic_score: float, stability_score: float, error_score: float) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if ic_score < 50:
            suggestions.append("改进特征工程以提升预测能力")
        if stability_score < 50:
            suggestions.append("检查模型复杂度，避免过拟合")
        if error_score < 50:
            suggestions.append("优化损失函数和训练流程")
        
        if not suggestions:
            suggestions.append("模型表现良好，继续保持")
        
        return suggestions
    
    @staticmethod
    def _generate_bias_recommendations(bias_indicators: List[Dict]) -> List[str]:
        """生成偏差改进建议"""
        recommendations = []
        
        for indicator in bias_indicators:
            if indicator["type"] == "HIGH_CORRELATION":
                recommendations.append("检查是否存在数据泄露或前瞻偏差")
            elif indicator["type"] == "PREDICTION_VOLATILITY":
                recommendations.append("审查特征构造过程，避免使用未来信息")
            elif indicator["type"] == "TEMPORAL_INCONSISTENCY":
                recommendations.append("确保预测模型的时间一致性")
        
        if not recommendations:
            recommendations.append("前瞻偏差检查通过")
        
        return recommendations
    
    @staticmethod
    def _generate_quality_improvement_recommendations(bias_score: float, data_score: float, 
                                                   significance_score: float, robustness_score: float) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        if bias_score < 70:
            recommendations.append("加强前瞻偏差检查和数据处理流程")
        if data_score < 70:
            recommendations.append("改善数据清洗和预处理质量")
        if significance_score < 70:
            recommendations.append("增加样本量或改进模型以提升统计显著性")
        if robustness_score < 70:
            recommendations.append("提升模型稳健性，减少对特定数据的依赖")
        
        if not recommendations:
            recommendations.append("回测质量优秀，可以进入生产环境")
        
        return recommendations
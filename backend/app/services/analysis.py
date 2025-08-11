"""
高级分析服务
"""
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from ..models.analysis import (
    AdvancedAnalysis, CustomMetric, MetricUsage, AnalysisTemplate, 
    ModelDiagnostics, AnalysisType, AnalysisStatus
)
from ..models.experiment import Experiment
from ..models.user import User
from ..schemas.analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisResponse, 
    CustomMetricCreate, CustomMetricUpdate, CustomMetricResponse,
    DiagnosticsResponse
)
from ..utils.analysis_calculator import AnalysisCalculator


class AdvancedAnalysisService:
    """高级分析服务"""
    
    def __init__(self):
        self.calculator = AnalysisCalculator()
    
    def create_analysis(self, db: Session, analysis_data: AnalysisCreate, 
                       creator_id: int) -> AdvancedAnalysis:
        """创建分析任务"""
        # 检查实验是否存在
        experiment = db.query(Experiment).filter(
            Experiment.id == analysis_data.experiment_id
        ).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实验不存在"
            )
        
        # 创建分析任务
        analysis = AdvancedAnalysis(
            experiment_id=analysis_data.experiment_id,
            creator_id=creator_id,
            analysis_type=analysis_data.analysis_type.value,
            name=analysis_data.name,
            description=analysis_data.description,
            config=analysis_data.config
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return analysis
    
    def execute_attribution_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行增强归因分析"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            # 更新状态
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取实验结果数据
            experiment_results = self._get_experiment_results(analysis.experiment_id)
            returns = np.array(experiment_results["returns"])
            benchmark_returns = np.array(experiment_results["benchmark_returns"])
            
            # 计算增强归因分析
            attribution_results = self.calculator.calculate_enhanced_attribution(
                returns, benchmark_returns
            )
            
            # 保存结果
            analysis.results = attribution_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            analysis.metrics = {
                "total_return": attribution_results.get("portfolio_return", 0.0),
                "active_return": attribution_results.get("active_return", 0.0),
                "alpha": attribution_results.get("alpha", 0.0),
                "beta": attribution_results.get("beta", 0.0),
                "information_ratio": attribution_results.get("information_ratio", 0.0),
                "industry_contribution": attribution_results.get("industry_contribution", {}),
                "style_factor_analysis": attribution_results.get("style_factor_analysis", {}),
                "stock_selection_effect": attribution_results.get("stock_selection_effect", {})
            }
            
            db.commit()
            return attribution_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"归因分析执行失败: {str(e)}"
            )
    
    def execute_risk_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行高级风险分析"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取实验结果数据
            experiment_results = self._get_experiment_results(analysis.experiment_id)
            returns = np.array(experiment_results["returns"])
            benchmark_returns = np.array(experiment_results["benchmark_returns"])
            
            # 计算高级风险分析
            risk_results = self.calculator.calculate_advanced_risk_analysis(
                returns, benchmark_returns
            )
            
            # 保存结果
            analysis.results = risk_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            analysis.metrics = {
                "annual_return": risk_results.get("annual_return", 0.0),
                "annual_volatility": risk_results.get("annual_volatility", 0.0),
                "sharpe_ratio": risk_results.get("sharpe_ratio", 0.0),
                "max_drawdown": risk_results.get("max_drawdown", 0.0),
                "var_95": risk_results.get("var_95", 0.0),
                "var_99": risk_results.get("var_99", 0.0),
                "sortino_ratio": risk_results.get("sortino_ratio", 0.0),
                "calmar_ratio": risk_results.get("calmar_ratio", 0.0),
                "tail_risk_level": risk_results.get("tail_risk", {}).get("tail_risk_level", "Medium"),
                "liquidity_risk_level": risk_results.get("liquidity_risk", {}).get("liquidity_risk_level", "Medium")
            }
            
            db.commit()
            return risk_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"风险分析执行失败: {str(e)}"
            )
    
    def execute_enhanced_feature_importance_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行增强特征重要性分析"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取模型数据
            model_data = self._get_model_data(analysis.experiment_id)
            features = np.array(model_data["features"])
            predictions = np.array(model_data["predictions"])
            actual_returns = np.array(model_data.get("actual_returns", model_data["predictions"]))
            feature_names = model_data.get("feature_names", [f"feature_{i}" for i in range(features.shape[1])])
            
            # 计算增强特征重要性分析
            importance_results = self.calculator.calculate_enhanced_feature_importance(
                features, predictions, actual_returns, feature_names
            )
            
            # 保存结果
            analysis.results = importance_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            analysis.metrics = {
                "top_features_count": len(importance_results.get("top_features", [])),
                "overall_stability": importance_results.get("stability_analysis", {}).get("overall_stability", 0.0),
                "high_correlation_pairs": len(importance_results.get("correlation_heatmap", {}).get("high_correlation_pairs", [])),
                "feature_diversity": importance_results.get("visualization_data", {}).get("feature_contribution_summary", {}).get("feature_diversity", 0.0),
                "shap_mean_importance": importance_results.get("enhanced_shap", {}).get("global_shap_summary", {}).get("mean_abs_shap", 0.0)
            }
            
            db.commit()
            return importance_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"增强特征重要性分析执行失败: {str(e)}"
            )
    
    # 保持向后兼容的旧方法
    def execute_feature_importance_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行特征重要性分析（向后兼容）"""
        return self.execute_enhanced_feature_importance_analysis(db, analysis_id)
    
    def execute_model_performance_monitoring(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行模型性能监控"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取实验和模型数据
            experiment_results = self._get_experiment_results(analysis.experiment_id)
            model_data = self._get_model_data(analysis.experiment_id)
            
            predictions = np.array(experiment_results["predictions"] if "predictions" in experiment_results else model_data["predictions"])
            actual_returns = np.array(experiment_results["returns"])
            features = np.array(model_data.get("features", []))
            timestamps = experiment_results.get("dates", [])
            
            # 计算模型性能监控
            monitoring_results = self.calculator.calculate_model_performance_monitoring(
                predictions, actual_returns, features if len(features) > 0 else None, timestamps
            )
            
            # 保存结果
            analysis.results = monitoring_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            analysis.metrics = {
                "overall_health_score": monitoring_results.get("overall_health_score", {}).get("overall_score", 0.0),
                "health_level": monitoring_results.get("overall_health_score", {}).get("health_level", "Unknown"),
                "ic_mean": monitoring_results.get("ic_monitoring", {}).get("ic_mean", 0.0),
                "stability_level": monitoring_results.get("stability_metrics", {}).get("stability_level", "Unknown"),
                "alert_count": monitoring_results.get("update_alerts", {}).get("alert_count", 0),
                "overall_alert_level": monitoring_results.get("update_alerts", {}).get("overall_alert_level", "Normal")
            }
            
            db.commit()
            return monitoring_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"模型性能监控执行失败: {str(e)}"
            )
    
    def execute_backtest_quality_check(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行回测质量检验"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取实验结果数据
            experiment_results = self._get_experiment_results(analysis.experiment_id)
            model_data = self._get_model_data(analysis.experiment_id)
            
            features = np.array(model_data.get("features", []))
            timestamps = experiment_results.get("dates", [])
            
            # 计算回测质量检验
            quality_results = self.calculator.calculate_backtest_quality_check(
                experiment_results,
                features if len(features) > 0 else None,
                timestamps
            )
            
            # 保存结果
            analysis.results = quality_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            analysis.metrics = {
                "quality_score": quality_results.get("quality_score", {}).get("overall_score", 0.0),
                "quality_level": quality_results.get("quality_score", {}).get("quality_level", "Unknown"),
                "bias_risk": quality_results.get("lookback_bias", {}).get("overall_risk", "Unknown"),
                "data_quality_score": quality_results.get("data_quality", {}).get("quality_score", 0.0),
                "significance_level": quality_results.get("significance_tests", {}).get("significance_summary", {}).get("overall_significance", "Unknown"),
                "robustness_level": quality_results.get("robustness_tests", {}).get("robustness_summary", {}).get("robustness_level", "Unknown")
            }
            
            db.commit()
            return quality_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"回测质量检验执行失败: {str(e)}"
            )
    
    def execute_ic_decay_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行IC衰减分析"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取预测和实际数据
            prediction_data = self._get_prediction_data(analysis.experiment_id)
            
            # 计算IC衰减
            ic_decay_results = self._calculate_ic_decay(
                prediction_data,
                analysis.config
            )
            
            # 保存结果
            analysis.results = ic_decay_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            analysis.metrics = {
                "ic_mean": ic_decay_results.get("ic_mean", 0.0),
                "ic_std": ic_decay_results.get("ic_std", 0.0),
                "ic_ir": ic_decay_results.get("ic_ir", 0.0),
                "decay_rate": ic_decay_results.get("decay_rate", 0.0),
                "ic_series": ic_decay_results.get("ic_series", [])
            }
            
            db.commit()
            return ic_decay_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"IC衰减分析执行失败: {str(e)}"
            )
    
    def execute_scenario_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行情景分析"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取实验结果数据
            experiment_results = self._get_experiment_results(analysis.experiment_id)
            returns = np.array(experiment_results["returns"])
            benchmark_returns = np.array(experiment_results["benchmark_returns"])
            
            # 获取自定义情景（如果有）
            custom_scenarios = analysis.config.get("custom_scenarios", None)
            
            # 计算增强情景分析
            scenario_results = self.calculator.calculate_enhanced_scenario_analysis(
                returns, benchmark_returns, custom_scenarios
            )
            
            # 保存结果
            analysis.results = scenario_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            base_metrics = scenario_results.get("base_case_metrics", {})
            scenario_summary = scenario_results.get("scenario_summary", {})
            
            analysis.metrics = {
                "base_annual_return": base_metrics.get("annual_return", 0.0),
                "base_volatility": base_metrics.get("annual_volatility", 0.0),
                "base_sharpe_ratio": base_metrics.get("sharpe_ratio", 0.0),
                "best_case_scenario": scenario_summary.get("best_case", ["", {}])[0],
                "worst_case_scenario": scenario_summary.get("worst_case", ["", {}])[0],
                "most_likely_scenario": scenario_summary.get("most_likely", ["", {}])[0],
                "risk_scenarios_count": len(scenario_summary.get("risk_scenarios", []))
            }
            
            db.commit()
            return scenario_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"情景分析执行失败: {str(e)}"
            )
    
    def execute_monte_carlo_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行蒙特卡洛模拟分析"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取实验结果数据
            experiment_results = self._get_experiment_results(analysis.experiment_id)
            returns = np.array(experiment_results["returns"])
            benchmark_returns = np.array(experiment_results["benchmark_returns"])
            
            # 获取模拟参数
            n_simulations = analysis.config.get("n_simulations", 10000)
            time_horizon = analysis.config.get("time_horizon", 252)
            confidence_levels = analysis.config.get("confidence_levels", [0.05, 0.95])
            
            # 计算蒙特卡洛模拟
            mc_results = self.calculator.calculate_monte_carlo_simulation(
                returns, benchmark_returns, n_simulations, time_horizon, confidence_levels
            )
            
            # 保存结果
            analysis.results = mc_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            return_dist = mc_results.get("return_distribution", {})
            risk_metrics = mc_results.get("risk_metrics", {})
            scenario_probs = mc_results.get("scenario_probabilities", {})
            
            analysis.metrics = {
                "expected_return": return_dist.get("mean", 0.0),
                "return_volatility": return_dist.get("std", 0.0),
                "probability_of_loss": risk_metrics.get("probability_of_loss", 0.0),
                "probability_severe_loss": risk_metrics.get("probability_severe_loss", 0.0),
                "var_95": risk_metrics.get("var_95", 0.0),
                "var_99": risk_metrics.get("var_99", 0.0),
                "bull_scenario_prob": scenario_probs.get("bull_scenario", 0.0),
                "bear_scenario_prob": scenario_probs.get("bear_scenario", 0.0),
                "extreme_loss_prob": scenario_probs.get("extreme_loss", 0.0)
            }
            
            db.commit()
            return mc_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"蒙特卡洛分析执行失败: {str(e)}"
            )
    
    def execute_sensitivity_analysis(self, db: Session, analysis_id: int) -> Dict[str, Any]:
        """执行敏感性分析"""
        analysis = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        try:
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()
            
            # 获取实验结果数据
            experiment_results = self._get_experiment_results(analysis.experiment_id)
            returns = np.array(experiment_results["returns"])
            
            # 获取分析参数
            base_parameters = analysis.config.get("base_parameters", None)
            parameter_ranges = analysis.config.get("parameter_ranges", None)
            
            # 计算敏感性分析
            sensitivity_results = self.calculator.calculate_sensitivity_analysis(
                returns, base_parameters, parameter_ranges
            )
            
            # 保存结果
            analysis.results = sensitivity_results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.progress = 100
            
            # 计算关键指标
            base_metrics = sensitivity_results.get("base_case_metrics", {})
            param_importance = sensitivity_results.get("parameter_importance", [])
            stability = sensitivity_results.get("stability_assessment", {})
            
            analysis.metrics = {
                "base_annual_return": base_metrics.get("annual_return", 0.0),
                "base_volatility": base_metrics.get("annual_volatility", 0.0),
                "base_sharpe_ratio": base_metrics.get("sharpe_ratio", 0.0),
                "most_important_parameter": param_importance[0].get("parameter", "") if param_importance else "",
                "most_important_score": param_importance[0].get("importance_score", 0.0) if param_importance else 0.0,
                "stable_parameters": len([k for k, v in stability.items() if v == "Stable"]),
                "unstable_parameters": len([k for k, v in stability.items() if v == "Unstable"])
            }
            
            db.commit()
            return sensitivity_results
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"敏感性分析执行失败: {str(e)}"
            )
    
    def get_analysis_by_id(self, db: Session, analysis_id: int) -> Optional[AdvancedAnalysis]:
        """根据ID获取分析任务"""
        return db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.id == analysis_id
        ).first()
    
    def get_experiment_analyses(self, db: Session, experiment_id: str, 
                               page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取实验的分析任务列表"""
        query = db.query(AdvancedAnalysis).filter(
            AdvancedAnalysis.experiment_id == experiment_id
        ).order_by(desc(AdvancedAnalysis.created_at))
        
        total = query.count()
        offset = (page - 1) * size
        analyses = query.offset(offset).limit(size).all()
        
        pages = (total + size - 1) // size
        
        return {
            "analyses": [AnalysisResponse.from_orm(analysis) for analysis in analyses],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def _get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验结果数据"""
        # 这里应该从实验结果存储中获取数据
        # 模拟返回数据结构
        return {
            "returns": np.random.randn(252).tolist(),  # 模拟收益率序列
            "positions": np.random.randn(252, 10).tolist(),  # 模拟持仓数据
            "benchmark_returns": (np.random.randn(252) * 0.8).tolist(),  # 模拟基准收益
            "dates": pd.date_range("2023-01-01", periods=252).strftime("%Y-%m-%d").tolist()
        }
    
    def _calculate_attribution(self, experiment_results: Dict[str, Any], 
                             config: Dict[str, Any]) -> Dict[str, Any]:
        """计算归因分析"""
        returns = np.array(experiment_results["returns"])
        benchmark_returns = np.array(experiment_results["benchmark_returns"])
        
        # 计算基本归因指标
        total_return = (1 + returns).prod() - 1
        benchmark_return = (1 + benchmark_returns).prod() - 1
        alpha = total_return - benchmark_return
        
        # 计算beta
        covariance = np.cov(returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
        
        # 模拟行业贡献分析
        sectors = ["Technology", "Healthcare", "Financial", "Consumer", "Industrial"]
        sector_contribution = {
            sector: np.random.uniform(-0.02, 0.02) for sector in sectors
        }
        
        # 模拟风格因子暴露
        factor_exposure = {
            "Value": np.random.uniform(-0.5, 0.5),
            "Growth": np.random.uniform(-0.5, 0.5),
            "Quality": np.random.uniform(-0.5, 0.5),
            "Momentum": np.random.uniform(-0.5, 0.5),
            "Size": np.random.uniform(-0.5, 0.5)
        }
        
        return {
            "total_return": float(total_return),
            "benchmark_return": float(benchmark_return),
            "alpha": float(alpha),
            "beta": float(beta),
            "sector_contribution": sector_contribution,
            "factor_exposure": factor_exposure,
            "attribution_summary": {
                "selection_effect": np.random.uniform(-0.01, 0.01),
                "allocation_effect": np.random.uniform(-0.01, 0.01),
                "interaction_effect": np.random.uniform(-0.005, 0.005)
            }
        }
    
    def _calculate_risk_metrics(self, experiment_results: Dict[str, Any], 
                               config: Dict[str, Any]) -> Dict[str, Any]:
        """计算风险指标"""
        returns = np.array(experiment_results["returns"])
        benchmark_returns = np.array(experiment_results["benchmark_returns"])
        
        # VaR计算
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # 最大回撤
        cumulative_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # 波动率
        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
        
        # 夏普比率
        risk_free_rate = config.get("risk_free_rate", 0.03)
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        # 与基准的相关性
        correlation = np.corrcoef(returns, benchmark_returns)[0, 1]
        
        return {
            "var_95": float(var_95),
            "var_99": float(var_99),
            "max_drawdown": float(max_drawdown),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "correlation_with_benchmark": float(correlation),
            "downside_deviation": float(np.std(returns[returns < 0]) * np.sqrt(252)),
            "sortino_ratio": float(np.mean(excess_returns) / np.std(returns[returns < 0]) * np.sqrt(252)),
            "calmar_ratio": float(np.mean(returns) * 252 / abs(max_drawdown)) if max_drawdown != 0 else 0,
            "risk_metrics_series": {
                "rolling_volatility": (pd.Series(returns).rolling(30).std() * np.sqrt(252)).tolist(),
                "rolling_var": (pd.Series(returns).rolling(30).quantile(0.05)).tolist(),
                "drawdown_series": drawdowns.tolist()
            }
        }
    
    def _get_model_data(self, experiment_id: str) -> Dict[str, Any]:
        """获取模型数据"""
        # 模拟模型特征数据
        n_samples, n_features = 1000, 20
        feature_names = [f"feature_{i}" for i in range(n_features)]
        
        return {
            "features": np.random.randn(n_samples, n_features).tolist(),
            "feature_names": feature_names,
            "predictions": np.random.randn(n_samples).tolist(),
            "actual_returns": np.random.randn(n_samples).tolist()
        }
    
    def _calculate_feature_importance(self, model_data: Dict[str, Any], 
                                    config: Dict[str, Any]) -> Dict[str, Any]:
        """计算特征重要性"""
        features = np.array(model_data["features"])
        feature_names = model_data["feature_names"]
        
        # 模拟SHAP值计算
        shap_values = {}
        feature_importance = {}
        
        for i, name in enumerate(feature_names):
            importance = abs(np.random.randn())
            feature_importance[name] = float(importance)
            shap_values[name] = np.random.randn(len(features)).tolist()
        
        # 排序特征重要性
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_features = [{"name": name, "importance": importance} for name, importance in sorted_features[:10]]
        
        # 计算特征相关性矩阵
        correlation_matrix = np.corrcoef(features.T)
        correlation_dict = {}
        for i, name1 in enumerate(feature_names):
            correlation_dict[name1] = {}
            for j, name2 in enumerate(feature_names):
                correlation_dict[name1][name2] = float(correlation_matrix[i, j])
        
        return {
            "feature_importance": feature_importance,
            "shap_values": shap_values,
            "top_features": top_features,
            "correlation_matrix": correlation_dict,
            "feature_stability": np.random.uniform(0.6, 0.9),  # 模拟特征稳定性
            "importance_distribution": {
                name: {
                    "mean": float(np.mean(np.random.randn(100))),
                    "std": float(np.std(np.random.randn(100)))
                } for name in feature_names[:5]
            }
        }
    
    def _get_prediction_data(self, experiment_id: str) -> Dict[str, Any]:
        """获取预测数据"""
        # 模拟预测和实际收益数据
        n_periods = 252
        dates = pd.date_range("2023-01-01", periods=n_periods)
        
        return {
            "dates": dates.strftime("%Y-%m-%d").tolist(),
            "predictions": np.random.randn(n_periods).tolist(),
            "actual_returns": np.random.randn(n_periods).tolist(),
            "stocks": [f"stock_{i}" for i in range(100)]  # 模拟股票池
        }
    
    def _calculate_ic_decay(self, prediction_data: Dict[str, Any], 
                          config: Dict[str, Any]) -> Dict[str, Any]:
        """计算IC衰减"""
        predictions = np.array(prediction_data["predictions"])
        actual_returns = np.array(prediction_data["actual_returns"])
        
        # 计算IC序列
        ic_series = []
        window_size = config.get("window_size", 30)
        
        for i in range(window_size, len(predictions)):
            window_pred = predictions[i-window_size:i]
            window_actual = actual_returns[i-window_size:i]
            ic = np.corrcoef(window_pred, window_actual)[0, 1]
            ic_series.append(float(ic) if not np.isnan(ic) else 0.0)
        
        # 计算IC统计指标
        ic_mean = np.mean(ic_series)
        ic_std = np.std(ic_series)
        ic_ir = ic_mean / ic_std if ic_std != 0 else 0
        
        # 计算衰减率
        if len(ic_series) > 1:
            decay_rate = (ic_series[-1] - ic_series[0]) / len(ic_series)
        else:
            decay_rate = 0
        
        return {
            "ic_series": ic_series,
            "ic_mean": float(ic_mean),
            "ic_std": float(ic_std),
            "ic_ir": float(ic_ir),
            "decay_rate": float(decay_rate),
            "ic_distribution": {
                "positive_ratio": sum(1 for ic in ic_series if ic > 0) / len(ic_series),
                "percentiles": {
                    "5%": float(np.percentile(ic_series, 5)),
                    "25%": float(np.percentile(ic_series, 25)),
                    "50%": float(np.percentile(ic_series, 50)),
                    "75%": float(np.percentile(ic_series, 75)),
                    "95%": float(np.percentile(ic_series, 95))
                }
            }
        }


class CustomMetricService:
    """自定义指标服务"""
    
    def create_metric(self, db: Session, metric_data: CustomMetricCreate, 
                     creator_id: int) -> CustomMetric:
        """创建自定义指标"""
        metric = CustomMetric(
            creator_id=creator_id,
            name=metric_data.name,
            description=metric_data.description,
            category=metric_data.category,
            formula=metric_data.formula,
            formula_type=metric_data.formula_type,
            variables=metric_data.variables,
            is_public=metric_data.is_public
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        return metric
    
    def calculate_metric(self, db: Session, metric_id: int, 
                        experiment_id: str, parameters: Dict[str, Any],
                        user_id: int) -> Dict[str, Any]:
        """计算自定义指标"""
        metric = db.query(CustomMetric).filter(CustomMetric.id == metric_id).first()
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指标不存在"
            )
        
        try:
            # 获取实验数据
            from ..utils.analysis_calculator import AnalysisCalculator
            experiment_data = self._get_experiment_data_for_custom_metric(experiment_id)
            
            # 计算自定义指标
            calculation_result = AnalysisCalculator.calculate_custom_metric(
                metric.formula,
                {**metric.variables, **parameters},
                experiment_data
            )
            
            if calculation_result["calculation_successful"]:
                result_value = calculation_result["result_value"]
                
                # 记录使用
                usage = MetricUsage(
                    metric_id=metric_id,
                    experiment_id=experiment_id,
                    user_id=user_id,
                    parameters=parameters,
                    result_value=result_value,
                    execution_time=calculation_result["execution_time"]
                )
                
                db.add(usage)
                
                # 更新使用次数
                metric.usage_count += 1
                
                db.commit()
                
                return {
                    "result_value": result_value,
                    "calculation_successful": True,
                    "validation": calculation_result["validation"],
                    "execution_time": calculation_result["execution_time"],
                    "metric_name": metric.name,
                    "formula": metric.formula
                }
            else:
                # 计算失败，但不记录使用
                return {
                    "result_value": None,
                    "calculation_successful": False,
                    "error": calculation_result["error"],
                    "error_type": calculation_result["error_type"],
                    "metric_name": metric.name,
                    "formula": metric.formula
                }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"指标计算失败: {str(e)}"
            )
    
    def validate_metric_formula(self, formula: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """验证指标公式"""
        try:
            from ..utils.analysis_calculator import AnalysisCalculator
            
            # 创建模拟数据用于验证
            mock_experiment_data = {
                "returns": np.random.randn(100).tolist(),
                "predictions": np.random.randn(100).tolist(),
                "benchmark_returns": np.random.randn(100).tolist()
            }
            
            # 尝试执行公式
            result = AnalysisCalculator.calculate_custom_metric(
                formula,
                variables or {},
                mock_experiment_data
            )
            
            return {
                "formula_valid": result["calculation_successful"],
                "validation_result": result.get("validation", {}),
                "error_message": result.get("error", None),
                "suggested_improvements": self._generate_formula_suggestions(formula, result)
            }
            
        except Exception as e:
            return {
                "formula_valid": False,
                "validation_result": {},
                "error_message": str(e),
                "suggested_improvements": ["检查公式语法"]
            }
    
    def get_metric_template_library(self, db: Session, category: str = None) -> Dict[str, Any]:
        """获取指标模板库"""
        # 预定义指标模板
        template_library = {
            "risk_metrics": [
                {
                    "name": "改进夏普比率",
                    "formula": "(mean(returns) - 0.03/252) / std(returns) * sqrt(252)",
                    "description": "年化夏普比率，假设无风险利率3%",
                    "variables": {},
                    "category": "风险指标"
                },
                {
                    "name": "最大回撤",
                    "formula": "min((np.cumprod(1 + returns) / np.maximum.accumulate(np.cumprod(1 + returns)) - 1))",
                    "description": "计算最大回撤",
                    "variables": {},
                    "category": "风险指标"
                },
                {
                    "name": "下行标准差",
                    "formula": "std(returns[returns < 0]) * sqrt(252)",
                    "description": "年化下行标准差",
                    "variables": {},
                    "category": "风险指标"
                }
            ],
            "performance_metrics": [
                {
                    "name": "信息比率",
                    "formula": "mean(returns - benchmark_returns) / std(returns - benchmark_returns) * sqrt(252)",
                    "description": "相对基准的信息比率",
                    "variables": {},
                    "category": "业绩指标"
                },
                {
                    "name": "预测准确率",
                    "formula": "mean((returns > 0) == (predictions > 0))",
                    "description": "预测方向准确率",
                    "variables": {},
                    "category": "业绩指标"
                }
            ],
            "custom_metrics": [
                {
                    "name": "自定义风险调整收益",
                    "formula": "mean(returns) * 252 / (std(returns) * sqrt(252) * risk_penalty)",
                    "description": "带风险惩罚的收益率",
                    "variables": {"risk_penalty": 1.2},
                    "category": "自定义指标"
                }
            ]
        }
        
        if category:
            return {
                "templates": template_library.get(category, []),
                "category": category
            }
        
        return {
            "templates": template_library,
            "categories": list(template_library.keys()),
            "total_templates": sum(len(templates) for templates in template_library.values())
        }
    
    def _get_experiment_data_for_custom_metric(self, experiment_id: str) -> Dict[str, Any]:
        """获取用于自定义指标计算的实验数据"""
        # 这里应该从实际存储中获取数据，现在返回模拟数据
        return {
            "returns": np.random.randn(252).tolist(),
            "predictions": np.random.randn(252).tolist(), 
            "benchmark_returns": np.random.randn(252).tolist(),
            "positions": np.random.randn(252, 10).tolist(),
            "dates": pd.date_range("2023-01-01", periods=252).strftime("%Y-%m-%d").tolist()
        }
    
    def _generate_formula_suggestions(self, formula: str, result: Dict[str, Any]) -> List[str]:
        """生成公式改进建议"""
        suggestions = []
        
        if not result.get("calculation_successful", False):
            error = result.get("error", "")
            if "name" in error and "not defined" in error:
                suggestions.append("检查变量名是否正确，可用变量：returns, predictions, benchmark_returns")
            elif "syntax" in error.lower():
                suggestions.append("检查公式语法，确保括号匹配和运算符正确")
            elif "division by zero" in error.lower():
                suggestions.append("避免除零错误，添加保护条件")
        
        # 基于公式内容的建议
        if "std(" in formula and "sqrt(" not in formula:
            suggestions.append("考虑年化处理：乘以 sqrt(252)")
        
        if "mean(" in formula and "252" not in formula:
            suggestions.append("考虑年化处理：乘以 252")
        
        if not suggestions:
            suggestions.append("公式验证通过")
        
        return suggestions
    
    def get_public_metrics(self, db: Session, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取公开指标列表"""
        query = db.query(CustomMetric).filter(
            CustomMetric.is_public == True,
            CustomMetric.is_active == True
        ).order_by(desc(CustomMetric.usage_count))
        
        total = query.count()
        offset = (page - 1) * size
        metrics = query.offset(offset).limit(size).all()
        
        pages = (total + size - 1) // size
        
        return {
            "metrics": [CustomMetricResponse.from_orm(metric) for metric in metrics],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }


# 创建全局服务实例
analysis_service = AdvancedAnalysisService()
custom_metric_service = CustomMetricService()
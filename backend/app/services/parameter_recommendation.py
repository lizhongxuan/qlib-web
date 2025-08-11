"""
智能参数推荐服务
"""
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
from datetime import datetime, timedelta
import json

from app.models.experiment import Experiment
from app.core.config import QLIB_CONFIG
from app.utils.validators import SafeDataProcessor


class ParameterRecommendationService:
    """智能参数推荐服务"""
    
    def __init__(self):
        self.model_params = QLIB_CONFIG["model_params"]
        self.strategy_params = QLIB_CONFIG["strategy_params"]
    
    async def recommend_model_params(self, 
                                   db: Session, 
                                   model_name: str,
                                   stock_pool: str = None,
                                   recent_days: int = 90) -> Dict[str, Any]:
        """基于历史实验推荐模型参数"""
        
        # 获取历史成功实验
        cutoff_date = datetime.utcnow() - timedelta(days=recent_days)
        
        query = db.query(Experiment).filter(
            and_(
                Experiment.status == "completed",
                Experiment.created_at >= cutoff_date,
                Experiment.config.contains({"model_config": {"name": model_name}})
            )
        )
        
        if stock_pool:
            query = query.filter(
                Experiment.config.contains({"data_config": {"stock_pool": stock_pool}})
            )
        
        experiments = query.order_by(Experiment.created_at.desc()).limit(100).all()
        
        if not experiments:
            return self._get_default_params(model_name)
        
        # 提取参数和性能数据
        param_performance_data = []
        for exp in experiments:
            try:
                model_config = exp.config.get("model_config", {})
                params = model_config.get("params", {})
                
                results = exp.results or {}
                performance = results.get("performance", {})
                
                # 计算综合评分
                score = self._calculate_performance_score(performance)
                
                param_performance_data.append({
                    "params": params,
                    "score": score,
                    "experiment_id": exp.id
                })
            except Exception:
                continue
        
        if not param_performance_data:
            return self._get_default_params(model_name)
        
        # 分析参数推荐
        recommendations = self._analyze_parameter_recommendations(
            param_performance_data, model_name
        )
        
        return {
            "model_name": model_name,
            "recommended_params": recommendations["params"],
            "confidence": recommendations["confidence"],
            "explanation": recommendations["explanation"],
            "historical_data": {
                "experiments_analyzed": len(param_performance_data),
                "best_score": max(d["score"] for d in param_performance_data),
                "avg_score": np.mean([d["score"] for d in param_performance_data])
            },
            "parameter_analysis": recommendations["analysis"]
        }
    
    async def recommend_strategy_params(self,
                                      db: Session,
                                      strategy_name: str,
                                      model_name: str = None,
                                      stock_pool: str = None) -> Dict[str, Any]:
        """推荐策略参数"""
        
        # 获取相关历史实验
        query = db.query(Experiment).filter(
            and_(
                Experiment.status == "completed",
                Experiment.config.contains({"strategy_config": {"name": strategy_name}})
            )
        )
        
        if model_name:
            query = query.filter(
                Experiment.config.contains({"model_config": {"name": model_name}})
            )
        
        if stock_pool:
            query = query.filter(
                Experiment.config.contains({"data_config": {"stock_pool": stock_pool}})
            )
        
        experiments = query.order_by(Experiment.created_at.desc()).limit(50).all()
        
        if not experiments:
            return self._get_default_strategy_params(strategy_name)
        
        # 分析策略参数
        param_data = []
        for exp in experiments:
            try:
                strategy_config = exp.config.get("strategy_config", {})
                params = strategy_config.get("params", {})
                
                performance = exp.results.get("performance", {}) if exp.results else {}
                score = self._calculate_performance_score(performance)
                
                param_data.append({"params": params, "score": score})
            except Exception:
                continue
        
        recommendations = self._analyze_strategy_recommendations(param_data, strategy_name)
        
        return {
            "strategy_name": strategy_name,
            "recommended_params": recommendations["params"],
            "confidence": recommendations["confidence"],
            "explanation": recommendations["explanation"],
            "historical_data": {
                "experiments_analyzed": len(param_data),
                "best_score": max(d["score"] for d in param_data) if param_data else 0
            }
        }
    
    async def validate_parameters(self,
                                model_name: str,
                                model_params: Dict[str, Any],
                                strategy_name: str,
                                strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数有效性"""
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        # 验证模型参数
        model_validation = self._validate_model_params(model_name, model_params)
        if model_validation["errors"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(model_validation["errors"])
        validation_result["warnings"].extend(model_validation["warnings"])
        validation_result["suggestions"].extend(model_validation["suggestions"])
        
        # 验证策略参数
        strategy_validation = self._validate_strategy_params(strategy_name, strategy_params)
        if strategy_validation["errors"]:
            validation_result["valid"] = False
            validation_result["errors"].extend(strategy_validation["errors"])
        validation_result["warnings"].extend(strategy_validation["warnings"])
        validation_result["suggestions"].extend(strategy_validation["suggestions"])
        
        # 参数组合验证
        combination_validation = self._validate_parameter_combination(
            model_name, model_params, strategy_name, strategy_params
        )
        validation_result["warnings"].extend(combination_validation["warnings"])
        validation_result["suggestions"].extend(combination_validation["suggestions"])
        
        return validation_result
    
    async def analyze_parameter_sensitivity(self,
                                          db: Session,
                                          model_name: str,
                                          param_name: str,
                                          stock_pool: str = None) -> Dict[str, Any]:
        """参数敏感性分析"""
        
        # 获取相关实验
        query = db.query(Experiment).filter(
            and_(
                Experiment.status == "completed",
                Experiment.config.contains({"model_config": {"name": model_name}})
            )
        )
        
        if stock_pool:
            query = query.filter(
                Experiment.config.contains({"data_config": {"stock_pool": stock_pool}})
            )
        
        experiments = query.limit(200).all()
        
        # 提取参数值和性能数据
        param_performance_pairs = []
        for exp in experiments:
            try:
                params = exp.config.get("model_config", {}).get("params", {})
                if param_name not in params:
                    continue
                
                param_value = params[param_name]
                performance = exp.results.get("performance", {}) if exp.results else {}
                score = self._calculate_performance_score(performance)
                
                param_performance_pairs.append((param_value, score))
            except Exception:
                continue
        
        if len(param_performance_pairs) < 5:
            return {
                "parameter": param_name,
                "sensitivity": "unknown",
                "message": "历史数据不足，无法进行敏感性分析"
            }
        
        # 分析敏感性
        sensitivity_analysis = self._calculate_parameter_sensitivity(
            param_performance_pairs, param_name
        )
        
        return {
            "parameter": param_name,
            "model": model_name,
            "sensitivity": sensitivity_analysis["level"],
            "correlation": sensitivity_analysis["correlation"],
            "optimal_range": sensitivity_analysis["optimal_range"],
            "analysis": sensitivity_analysis["analysis"],
            "data_points": len(param_performance_pairs)
        }
    
    def _get_default_params(self, model_name: str) -> Dict[str, Any]:
        """获取默认参数"""
        default_params = {}
        
        if model_name in self.model_params:
            for param_name, param_config in self.model_params[model_name].items():
                default_params[param_name] = param_config.get("default")
        
        return {
            "model_name": model_name,
            "recommended_params": default_params,
            "confidence": 0.5,
            "explanation": "使用默认参数，无足够历史数据进行推荐",
            "historical_data": {"experiments_analyzed": 0},
            "parameter_analysis": {}
        }
    
    def _get_default_strategy_params(self, strategy_name: str) -> Dict[str, Any]:
        """获取默认策略参数"""
        default_params = {}
        
        if strategy_name in self.strategy_params:
            for param_name, param_config in self.strategy_params[strategy_name].items():
                default_params[param_name] = param_config.get("default")
        
        return {
            "strategy_name": strategy_name,
            "recommended_params": default_params,
            "confidence": 0.5,
            "explanation": "使用默认参数，无足够历史数据进行推荐",
            "historical_data": {"experiments_analyzed": 0}
        }
    
    def _calculate_performance_score(self, performance: Dict[str, Any]) -> float:
        """计算性能综合评分"""
        if not performance:
            return 0.0
        
        try:
            # 使用安全转换避免类型错误
            total_return = SafeDataProcessor.safe_float_conversion(performance.get("total_return", 0))
            sharpe_ratio = SafeDataProcessor.safe_float_conversion(performance.get("sharpe_ratio", 0))
            max_drawdown = SafeDataProcessor.safe_float_conversion(performance.get("max_drawdown", 0))
            
            # 检查数值有效性
            if not all(isinstance(x, (int, float)) and not (isinstance(x, float) and (np.isnan(x) or np.isinf(x))) 
                      for x in [total_return, sharpe_ratio, max_drawdown]):
                return 0.0
            
            # 标准化评分 (0-100)
            score = 0
            score += min(total_return * 100, 50)  # 收益率权重50%
            score += min(max(sharpe_ratio * 20, 0), 30)  # 夏普比率权重30%
            score += min(max((1 + max_drawdown) * 20, 0), 20)  # 回撤权重20%
            
            return max(0, min(100, score))
        except Exception as e:
            # 记录错误但不抛出异常
            print(f"计算性能评分时出错: {e}")
            return 0.0
    
    def _analyze_parameter_recommendations(self,
                                         param_performance_data: List[Dict],
                                         model_name: str) -> Dict[str, Any]:
        """分析参数推荐"""
        
        # 按性能排序，取前20%作为最优实验
        sorted_data = sorted(param_performance_data, key=lambda x: x["score"], reverse=True)
        top_performers = sorted_data[:max(1, len(sorted_data) // 5)]
        
        # 分析每个参数的最优值
        param_analysis = {}
        recommended_params = {}
        
        if model_name in self.model_params:
            for param_name, param_config in self.model_params[model_name].items():
                values = []
                for exp_data in top_performers:
                    if param_name in exp_data["params"]:
                        values.append(exp_data["params"][param_name])
                
                if values:
                    if param_config["type"] == "int" or param_config["type"] == "float":
                        # 数值参数：计算最优范围
                        mean_val = np.mean(values)
                        std_val = np.std(values) if len(values) > 1 else 0
                        
                        if param_config["type"] == "int":
                            recommended_params[param_name] = int(round(mean_val))
                        else:
                            recommended_params[param_name] = round(mean_val, 4)
                        
                        param_analysis[param_name] = {
                            "recommended_value": recommended_params[param_name],
                            "optimal_range": [
                                max(param_config.get("min", mean_val - 2*std_val), mean_val - 2*std_val),
                                min(param_config.get("max", mean_val + 2*std_val), mean_val + 2*std_val)
                            ],
                            "confidence": min(1.0, len(values) / 10)
                        }
                    
                    elif param_config["type"] == "bool":
                        # 布尔参数：选择出现频率最高的值
                        true_count = sum(1 for v in values if v)
                        recommended_params[param_name] = true_count > len(values) / 2
                        
                        param_analysis[param_name] = {
                            "recommended_value": recommended_params[param_name],
                            "confidence": abs(true_count - len(values)/2) / (len(values)/2)
                        }
                else:
                    # 使用默认值
                    recommended_params[param_name] = param_config.get("default")
                    param_analysis[param_name] = {
                        "recommended_value": recommended_params[param_name],
                        "confidence": 0.3,
                        "note": "使用默认值"
                    }
        
        # 计算整体置信度
        overall_confidence = np.mean([
            analysis.get("confidence", 0.5) 
            for analysis in param_analysis.values()
        ]) if param_analysis else 0.5
        
        explanation = f"基于 {len(top_performers)} 个最优实验的参数分析推荐"
        
        return {
            "params": recommended_params,
            "confidence": overall_confidence,
            "explanation": explanation,
            "analysis": param_analysis
        }
    
    def _analyze_strategy_recommendations(self,
                                        param_data: List[Dict],
                                        strategy_name: str) -> Dict[str, Any]:
        """分析策略参数推荐"""
        
        if not param_data:
            return self._get_default_strategy_params(strategy_name)
        
        # 类似模型参数的分析逻辑
        sorted_data = sorted(param_data, key=lambda x: x["score"], reverse=True)
        top_performers = sorted_data[:max(1, len(sorted_data) // 3)]
        
        recommended_params = {}
        
        if strategy_name in self.strategy_params:
            for param_name, param_config in self.strategy_params[strategy_name].items():
                values = [
                    exp["params"].get(param_name, param_config.get("default"))
                    for exp in top_performers
                    if param_name in exp["params"]
                ]
                
                if values:
                    if param_config["type"] == "int":
                        recommended_params[param_name] = int(round(np.mean(values)))
                    elif param_config["type"] == "float":
                        recommended_params[param_name] = round(np.mean(values), 4)
                    else:
                        recommended_params[param_name] = param_config.get("default")
                else:
                    recommended_params[param_name] = param_config.get("default")
        
        confidence = min(1.0, len(top_performers) / 10)
        
        return {
            "params": recommended_params,
            "confidence": confidence,
            "explanation": f"基于 {len(top_performers)} 个最优策略实验推荐"
        }
    
    def _validate_model_params(self, model_name: str, params: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证模型参数"""
        errors = []
        warnings = []
        suggestions = []
        
        if model_name not in self.model_params:
            errors.append(f"未知模型: {model_name}")
            return {"errors": errors, "warnings": warnings, "suggestions": suggestions}
        
        param_configs = self.model_params[model_name]
        
        for param_name, param_value in params.items():
            if param_name not in param_configs:
                warnings.append(f"未知参数 {param_name}，将被忽略")
                continue
            
            config = param_configs[param_name]
            
            # 类型检查
            expected_type = config["type"]
            if expected_type == "int" and not isinstance(param_value, int):
                errors.append(f"参数 {param_name} 应为整数类型")
            elif expected_type == "float" and not isinstance(param_value, (int, float)):
                errors.append(f"参数 {param_name} 应为数值类型")
            elif expected_type == "bool" and not isinstance(param_value, bool):
                errors.append(f"参数 {param_name} 应为布尔类型")
            
            # 范围检查
            if "min" in config and param_value < config["min"]:
                errors.append(f"参数 {param_name} 小于最小值 {config['min']}")
            if "max" in config and param_value > config["max"]:
                errors.append(f"参数 {param_name} 大于最大值 {config['max']}")
            
            # 建议检查
            default_val = config.get("default")
            if default_val is not None and abs(param_value - default_val) / default_val > 2:
                suggestions.append(f"参数 {param_name} 偏离默认值较多，建议谨慎调整")
        
        return {"errors": errors, "warnings": warnings, "suggestions": suggestions}
    
    def _validate_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证策略参数"""
        errors = []
        warnings = []
        suggestions = []
        
        if strategy_name not in self.strategy_params:
            errors.append(f"未知策略: {strategy_name}")
            return {"errors": errors, "warnings": warnings, "suggestions": suggestions}
        
        # 类似的验证逻辑...
        return {"errors": errors, "warnings": warnings, "suggestions": suggestions}
    
    def _validate_parameter_combination(self,
                                      model_name: str,
                                      model_params: Dict[str, Any],
                                      strategy_name: str,
                                      strategy_params: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证参数组合"""
        warnings = []
        suggestions = []
        
        # 检查模型和策略的兼容性
        if model_name in ["LSTM", "GRU"] and strategy_name == "TopkDropoutStrategy":
            topk = strategy_params.get("topk", 50)
            if topk > 100:
                warnings.append("深度学习模型配合过大的topk可能导致过拟合")
        
        # 检查资源使用
        if model_name == "LightGBM":
            n_estimators = model_params.get("n_estimators", 100)
            max_depth = model_params.get("max_depth", 6)
            if n_estimators > 500 and max_depth > 10:
                warnings.append("模型复杂度较高，可能导致训练时间过长")
        
        return {"warnings": warnings, "suggestions": suggestions}
    
    def _calculate_parameter_sensitivity(self,
                                       param_performance_pairs: List[Tuple],
                                       param_name: str) -> Dict[str, Any]:
        """计算参数敏感性"""
        
        if len(param_performance_pairs) < 5:
            return {
                "level": "unknown",
                "correlation": 0,
                "optimal_range": None,
                "analysis": "数据不足"
            }
        
        # 计算相关性
        param_values = [pair[0] for pair in param_performance_pairs]
        performance_scores = [pair[1] for pair in param_performance_pairs]
        
        correlation = np.corrcoef(param_values, performance_scores)[0, 1]
        
        # 敏感性等级
        if abs(correlation) > 0.7:
            sensitivity_level = "high"
        elif abs(correlation) > 0.4:
            sensitivity_level = "medium"
        else:
            sensitivity_level = "low"
        
        # 最优范围（基于前25%的表现）
        sorted_pairs = sorted(param_performance_pairs, key=lambda x: x[1], reverse=True)
        top_25_percent = sorted_pairs[:max(1, len(sorted_pairs) // 4)]
        optimal_values = [pair[0] for pair in top_25_percent]
        
        optimal_range = [min(optimal_values), max(optimal_values)]
        
        analysis = f"参数敏感性: {sensitivity_level}, 相关系数: {correlation:.3f}"
        
        return {
            "level": sensitivity_level,
            "correlation": correlation,
            "optimal_range": optimal_range,
            "analysis": analysis
        }
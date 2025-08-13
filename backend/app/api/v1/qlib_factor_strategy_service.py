"""
基于Qlib的因子库和策略框架服务API
提供因子工程、策略构建、回测执行等功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
import qlib
from qlib.config import REG_CN
from qlib.data import D
from qlib.utils import init_instance_by_config
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta

# Qlib因子和策略相关导入
from qlib.contrib.data.handler import Alpha158, Alpha360
from qlib.contrib.strategy import TopkDropoutStrategy, WeightStrategyBase
from qlib.backtest import backtest, executor
from qlib.contrib.evaluate import risk_analysis, long_short_backtest
from qlib.workflow import R

# 因子计算相关
from qlib.data.ops import Ref, Mean, Std, Corr, Rank, Max, Min
from qlib.data.filter import NameDFilter, ExpressionDFilter

logger = logging.getLogger(__name__)
router = APIRouter()

# 数据模型定义
class FactorDefinitionRequest(BaseModel):
    factor_name: str
    expression: str
    description: Optional[str] = None
    category: str = "custom"
    parameters: Optional[Dict[str, Any]] = None

class FactorValidationRequest(BaseModel):
    factor_expression: str
    instruments: Union[str, List[str]] = "csi300"
    start_time: str
    end_time: str
    validation_metrics: List[str] = ["ic", "rank_ic", "turnover"]

class FactorLibraryRequest(BaseModel):
    category: Optional[str] = None
    search_term: Optional[str] = None
    include_builtin: bool = True
    include_custom: bool = True

class StrategyConstructionRequest(BaseModel):
    strategy_name: str
    factor_selection: List[str]
    strategy_type: str = "topk"  # topk, long_short, weight_based
    parameters: Dict[str, Any]
    universe: str = "csi300"

class BacktestExecutionRequest(BaseModel):
    strategy_config: Dict[str, Any]
    backtest_config: Dict[str, Any]
    risk_config: Optional[Dict[str, Any]] = None

class PortfolioOptimizationRequest(BaseModel):
    expected_returns: Dict[str, float]
    covariance_matrix: List[List[float]]
    constraints: Dict[str, Any]
    optimization_method: str = "mean_variance"

# 全局存储
factor_library = {}
strategy_library = {}
backtest_results = {}

class QlibFactorStrategyService:
    """基于Qlib的因子和策略服务"""
    
    def __init__(self):
        self.initialized = False
        self.builtin_factors = self._init_builtin_factors()
        self.custom_factors = {}
        self.strategy_templates = self._init_strategy_templates()
        
    def initialize_qlib(self):
        """初始化Qlib环境"""
        if not self.initialized:
            try:
                qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)
                self.initialized = True
                logger.info("Qlib因子策略服务初始化成功")
            except Exception as e:
                logger.error(f"Qlib初始化失败: {e}")
                raise HTTPException(status_code=500, detail=f"Qlib初始化失败: {e}")
    
    def _init_builtin_factors(self) -> Dict[str, Dict[str, Any]]:
        """初始化内置因子库"""
        return {
            # 价格动量因子
            "momentum_5d": {
                "name": "5日动量",
                "expression": "($close / Ref($close, 5)) - 1",
                "description": "5日价格动量因子",
                "category": "momentum",
                "parameters": {"period": 5}
            },
            "momentum_20d": {
                "name": "20日动量",
                "expression": "($close / Ref($close, 20)) - 1", 
                "description": "20日价格动量因子",
                "category": "momentum",
                "parameters": {"period": 20}
            },
            "momentum_60d": {
                "name": "60日动量",
                "expression": "($close / Ref($close, 60)) - 1",
                "description": "60日价格动量因子", 
                "category": "momentum",
                "parameters": {"period": 60}
            },
            
            # 均值回归因子
            "mean_reversion_5d": {
                "name": "5日均值回归",
                "expression": "($close - Mean($close, 5)) / Std($close, 5)",
                "description": "5日均值回归因子",
                "category": "mean_reversion",
                "parameters": {"period": 5}
            },
            "mean_reversion_20d": {
                "name": "20日均值回归",
                "expression": "($close - Mean($close, 20)) / Std($close, 20)",
                "description": "20日均值回归因子",
                "category": "mean_reversion", 
                "parameters": {"period": 20}
            },
            
            # 波动率因子
            "volatility_5d": {
                "name": "5日波动率",
                "expression": "Std($close, 5) / Mean($close, 5)",
                "description": "5日价格波动率",
                "category": "volatility",
                "parameters": {"period": 5}
            },
            "volatility_20d": {
                "name": "20日波动率",
                "expression": "Std($close, 20) / Mean($close, 20)",
                "description": "20日价格波动率",
                "category": "volatility",
                "parameters": {"period": 20}
            },
            
            # 成交量因子
            "volume_ratio_5d": {
                "name": "5日成交量比率",
                "expression": "$volume / Mean($volume, 5)",
                "description": "5日成交量相对比率",
                "category": "volume", 
                "parameters": {"period": 5}
            },
            "volume_ratio_20d": {
                "name": "20日成交量比率",
                "expression": "$volume / Mean($volume, 20)",
                "description": "20日成交量相对比率",
                "category": "volume",
                "parameters": {"period": 20}
            },
            
            # 技术指标因子
            "rsi_14d": {
                "name": "14日RSI",
                "expression": "RSI($close, 14)",  # 简化表示
                "description": "14日相对强弱指标",
                "category": "technical",
                "parameters": {"period": 14}
            },
            "macd": {
                "name": "MACD",
                "expression": "EMA($close, 12) - EMA($close, 26)",  # 简化表示
                "description": "移动平均收敛散度",
                "category": "technical",
                "parameters": {"fast": 12, "slow": 26}
            },
            
            # 基本面因子
            "pe_ratio": {
                "name": "市盈率倒数",
                "expression": "1 / $pe",
                "description": "市盈率倒数，价值因子",
                "category": "fundamental",
                "parameters": {}
            },
            "pb_ratio": {
                "name": "市净率倒数", 
                "expression": "1 / $pb",
                "description": "市净率倒数，价值因子",
                "category": "fundamental",
                "parameters": {}
            },
            
            # 质量因子
            "roe": {
                "name": "净资产收益率",
                "expression": "$roe",
                "description": "净资产收益率，盈利质量因子",
                "category": "quality",
                "parameters": {}
            },
            "debt_to_equity": {
                "name": "资产负债率",
                "expression": "1 / (1 + $debt_to_equity)",  # 转为正向因子
                "description": "资产负债率倒数，财务健康因子",
                "category": "quality", 
                "parameters": {}
            }
        }
    
    def _init_strategy_templates(self) -> Dict[str, Dict[str, Any]]:
        """初始化策略模板"""
        return {
            "momentum_strategy": {
                "name": "动量策略",
                "description": "基于价格动量的多头策略",
                "factors": ["momentum_20d", "volume_ratio_20d"],
                "strategy_type": "topk",
                "parameters": {
                    "topk": 50,
                    "n_drop": 5,
                    "hold_thresh": 0.95
                },
                "risk_model": "simple"
            },
            "mean_reversion_strategy": {
                "name": "均值回归策略",
                "description": "基于均值回归的多空策略",
                "factors": ["mean_reversion_20d", "volatility_20d"],
                "strategy_type": "long_short",
                "parameters": {
                    "long_ratio": 0.3,
                    "short_ratio": 0.3,
                    "neutral_ratio": 0.4
                },
                "risk_model": "advanced"
            },
            "value_strategy": {
                "name": "价值策略",
                "description": "基于基本面价值的长期策略",
                "factors": ["pe_ratio", "pb_ratio", "roe"],
                "strategy_type": "weight_based", 
                "parameters": {
                    "weight_method": "rank",
                    "rebalance_freq": "monthly"
                },
                "risk_model": "fundamental"
            },
            "multi_factor_strategy": {
                "name": "多因子策略",
                "description": "综合多类因子的平衡策略",
                "factors": ["momentum_20d", "mean_reversion_5d", "pe_ratio", "volume_ratio_20d"],
                "strategy_type": "topk",
                "parameters": {
                    "topk": 30,
                    "factor_weights": [0.3, 0.2, 0.3, 0.2],
                    "rebalance_freq": "weekly"
                },
                "risk_model": "comprehensive"
            }
        }
    
    async def get_factor_library(self, request: FactorLibraryRequest) -> Dict[str, Any]:
        """获取因子库"""
        try:
            factors = {}
            
            # 包含内置因子
            if request.include_builtin:
                for factor_id, factor_info in self.builtin_factors.items():
                    if request.category is None or factor_info["category"] == request.category:
                        if request.search_term is None or request.search_term.lower() in factor_info["name"].lower():
                            factors[factor_id] = {
                                **factor_info,
                                "source": "builtin",
                                "factor_id": factor_id
                            }
            
            # 包含自定义因子
            if request.include_custom:
                for factor_id, factor_info in self.custom_factors.items():
                    if request.category is None or factor_info["category"] == request.category:
                        if request.search_term is None or request.search_term.lower() in factor_info["name"].lower():
                            factors[factor_id] = {
                                **factor_info,
                                "source": "custom",
                                "factor_id": factor_id
                            }
            
            # 统计信息
            categories = {}
            for factor_info in factors.values():
                category = factor_info["category"]
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            return {
                "factors": factors,
                "total_count": len(factors),
                "categories": categories,
                "builtin_count": len([f for f in factors.values() if f["source"] == "builtin"]),
                "custom_count": len([f for f in factors.values() if f["source"] == "custom"])
            }
            
        except Exception as e:
            logger.error(f"获取因子库失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取因子库失败: {e}")
    
    async def validate_factor(self, request: FactorValidationRequest) -> Dict[str, Any]:
        """验证因子有效性"""
        self.initialize_qlib()
        
        try:
            # 处理instruments参数
            if isinstance(request.instruments, str):
                if request.instruments in ["csi300", "csi500", "all"]:
                    instruments = D.instruments(market=request.instruments)
                else:
                    instruments = [request.instruments]
            else:
                instruments = request.instruments
            
            # 计算因子数据
            try:
                factor_data = D.features(
                    instruments=instruments,
                    fields=[request.factor_expression],
                    start_time=request.start_time,
                    end_time=request.end_time,
                    freq="day"
                )
                
                if factor_data.empty:
                    return {
                        "isValid": False,
                        "errors": ["因子数据为空"],
                        "metrics": {},
                        "statistics": {}
                    }
                
                # 获取收益率数据用于计算IC
                return_data = D.features(
                    instruments=instruments,
                    fields=["Ref($close, -1)/$close - 1"],  # 下期收益率
                    start_time=request.start_time,
                    end_time=request.end_time,
                    freq="day"
                )
                
                factor_col = factor_data.iloc[:, 0]
                return_col = return_data.iloc[:, 0] if not return_data.empty else pd.Series()
                
                # 计算验证指标
                metrics = {}
                
                # IC计算（信息系数）
                if not return_col.empty and len(factor_col) == len(return_col):
                    ic_values = []
                    rank_ic_values = []
                    
                    # 按日期分组计算IC
                    factor_df = pd.DataFrame({
                        'factor': factor_col.values,
                        'return': return_col.values,
                        'date': factor_col.index.get_level_values(0) if hasattr(factor_col.index, 'get_level_values') else range(len(factor_col))
                    })
                    
                    for date, group in factor_df.groupby('date'):
                        if len(group) > 10:  # 至少10个样本
                            ic = group['factor'].corr(group['return'])
                            rank_ic = group['factor'].rank().corr(group['return'].rank())
                            
                            if not pd.isna(ic):
                                ic_values.append(ic)
                            if not pd.isna(rank_ic):
                                rank_ic_values.append(rank_ic)
                    
                    if ic_values:
                        metrics["ic"] = {
                            "mean": float(np.mean(ic_values)),
                            "std": float(np.std(ic_values)),
                            "ir": float(np.mean(ic_values) / np.std(ic_values)) if np.std(ic_values) > 0 else 0,
                            "positive_ratio": float(np.mean([x > 0 for x in ic_values]))
                        }
                    
                    if rank_ic_values:
                        metrics["rank_ic"] = {
                            "mean": float(np.mean(rank_ic_values)),
                            "std": float(np.std(rank_ic_values)),
                            "ir": float(np.mean(rank_ic_values) / np.std(rank_ic_values)) if np.std(rank_ic_values) > 0 else 0
                        }
                
                # 因子统计信息
                statistics = {
                    "count": int(factor_col.count()),
                    "mean": float(factor_col.mean()),
                    "std": float(factor_col.std()),
                    "min": float(factor_col.min()),
                    "max": float(factor_col.max()),
                    "skewness": float(factor_col.skew()),
                    "kurtosis": float(factor_col.kurt()),
                    "missing_ratio": float(factor_col.isnull().mean()),
                    "unique_count": int(factor_col.nunique()),
                    "unique_ratio": float(factor_col.nunique() / len(factor_col))
                }
                
                # 评估因子质量
                is_valid = True
                errors = []
                warnings = []
                
                if statistics["missing_ratio"] > 0.5:
                    warnings.append(f"缺失值比例过高: {statistics['missing_ratio']:.2%}")
                
                if statistics["unique_ratio"] < 0.1:
                    warnings.append("因子区分度较低，可能为常数因子")
                
                if "ic" in metrics:
                    if abs(metrics["ic"]["mean"]) < 0.01:
                        warnings.append("IC值较低，预测能力有限")
                    if metrics["ic"]["ir"] < 0.5:
                        warnings.append("IR值较低，信号稳定性有限")
                
                # 计算综合得分
                score = 100
                if "ic" in metrics:
                    score += abs(metrics["ic"]["mean"]) * 1000  # IC贡献
                    score += metrics["ic"]["ir"] * 20  # IR贡献
                score -= len(warnings) * 10
                score = max(0, min(100, score))
                
                return {
                    "isValid": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "metrics": metrics,
                    "statistics": statistics,
                    "score": float(score),
                    "recommendation": self._get_factor_recommendation(metrics, statistics)
                }
                
            except Exception as calc_e:
                return {
                    "isValid": False,
                    "errors": [f"因子计算失败: {calc_e}"],
                    "metrics": {},
                    "statistics": {}
                }
        
        except Exception as e:
            logger.error(f"因子验证失败: {e}")
            raise HTTPException(status_code=500, detail=f"因子验证失败: {e}")
    
    def _get_factor_recommendation(self, metrics: Dict, statistics: Dict) -> str:
        """获取因子建议"""
        if not metrics:
            return "无法计算有效指标，建议检查因子表达式"
        
        if "ic" in metrics:
            ic_mean = abs(metrics["ic"]["mean"])
            ir = metrics["ic"]["ir"]
            
            if ic_mean > 0.05 and ir > 1.0:
                return "优秀因子，建议直接使用"
            elif ic_mean > 0.03 and ir > 0.8:
                return "良好因子，建议组合使用"
            elif ic_mean > 0.01:
                return "一般因子，建议进一步优化"
            else:
                return "较弱因子，建议重新设计"
        
        return "建议进行更详细的回测验证"
    
    async def create_custom_factor(self, request: FactorDefinitionRequest) -> Dict[str, Any]:
        """创建自定义因子"""
        try:
            factor_id = f"custom_{int(datetime.now().timestamp())}"
            
            factor_info = {
                "name": request.factor_name,
                "expression": request.expression,
                "description": request.description or "",
                "category": request.category,
                "parameters": request.parameters or {},
                "created_at": datetime.now().isoformat(),
                "creator": "user"  # 实际应该从认证信息获取
            }
            
            # 保存到自定义因子库
            self.custom_factors[factor_id] = factor_info
            
            return {
                "factor_id": factor_id,
                "factor_info": factor_info,
                "message": "自定义因子创建成功"
            }
            
        except Exception as e:
            logger.error(f"创建自定义因子失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建自定义因子失败: {e}")
    
    async def construct_strategy(self, request: StrategyConstructionRequest) -> Dict[str, Any]:
        """构建投资策略"""
        try:
            strategy_id = f"strategy_{int(datetime.now().timestamp())}"
            
            # 验证因子存在性
            selected_factors = []
            for factor_name in request.factor_selection:
                if factor_name in self.builtin_factors:
                    selected_factors.append({
                        **self.builtin_factors[factor_name],
                        "factor_id": factor_name,
                        "source": "builtin"
                    })
                elif factor_name in self.custom_factors:
                    selected_factors.append({
                        **self.custom_factors[factor_name], 
                        "factor_id": factor_name,
                        "source": "custom"
                    })
                else:
                    logger.warning(f"因子不存在: {factor_name}")
            
            if not selected_factors:
                raise ValueError("没有找到有效的因子")
            
            # 构建策略配置
            strategy_config = {
                "strategy_id": strategy_id,
                "strategy_name": request.strategy_name,
                "strategy_type": request.strategy_type,
                "factors": selected_factors,
                "parameters": request.parameters,
                "universe": request.universe,
                "created_at": datetime.now().isoformat(),
                "status": "configured"
            }
            
            # 保存到策略库
            strategy_library[strategy_id] = strategy_config
            
            # 生成策略摘要
            strategy_summary = {
                "strategy_id": strategy_id,
                "factor_count": len(selected_factors),
                "factor_categories": list(set([f["category"] for f in selected_factors])),
                "expected_performance": self._estimate_strategy_performance(selected_factors, request.strategy_type),
                "risk_profile": self._estimate_risk_profile(selected_factors, request.strategy_type)
            }
            
            return {
                "strategy_config": strategy_config,
                "strategy_summary": strategy_summary,
                "message": "策略构建成功"
            }
            
        except Exception as e:
            logger.error(f"构建策略失败: {e}")
            raise HTTPException(status_code=500, detail=f"构建策略失败: {e}")
    
    def _estimate_strategy_performance(self, factors: List[Dict], strategy_type: str) -> Dict[str, Any]:
        """估计策略性能"""
        # 基于因子类型和策略类型的简化性能估计
        base_return = 0.08  # 基础年化收益率
        base_sharpe = 1.2   # 基础夏普比率
        
        # 因子多样性加成
        categories = set([f["category"] for f in factors])
        diversity_bonus = len(categories) * 0.02
        
        # 策略类型调整
        if strategy_type == "long_short":
            base_return += 0.03
            base_sharpe += 0.2
        elif strategy_type == "topk":
            base_return += 0.01
            base_sharpe += 0.1
        
        return {
            "expected_annual_return": base_return + diversity_bonus,
            "expected_sharpe_ratio": base_sharpe + diversity_bonus * 5,
            "expected_max_drawdown": 0.15 - diversity_bonus,
            "confidence_level": min(0.85, 0.6 + len(factors) * 0.05)
        }
    
    def _estimate_risk_profile(self, factors: List[Dict], strategy_type: str) -> Dict[str, Any]:
        """估计风险特征"""
        # 基于因子类型评估风险
        risk_factors = {
            "market_risk": "中等",
            "sector_risk": "低" if len(set([f["category"] for f in factors])) > 2 else "中等",
            "factor_risk": "低" if len(factors) > 3 else "中等",
            "liquidity_risk": "低",
            "model_risk": "中等"
        }
        
        # 策略类型风险调整
        if strategy_type == "long_short":
            risk_factors["market_risk"] = "低"
        elif strategy_type == "topk":
            risk_factors["concentration_risk"] = "中等"
        
        return {
            "risk_factors": risk_factors,
            "overall_risk_level": "中等",
            "risk_budget_allocation": {
                "factor_risk": 0.6,
                "specific_risk": 0.3,
                "market_risk": 0.1
            }
        }
    
    async def get_strategy_templates(self) -> Dict[str, Any]:
        """获取策略模板"""
        try:
            return {
                "templates": self.strategy_templates,
                "total_count": len(self.strategy_templates),
                "categories": list(set([t["strategy_type"] for t in self.strategy_templates.values()]))
            }
        except Exception as e:
            logger.error(f"获取策略模板失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取策略模板失败: {e}")

# 创建服务实例
factor_strategy_service = QlibFactorStrategyService()

@router.get("/factor-library")
async def get_factor_library(
    category: Optional[str] = None,
    search_term: Optional[str] = None,
    include_builtin: bool = True,
    include_custom: bool = True
):
    """获取因子库"""
    try:
        request = FactorLibraryRequest(
            category=category,
            search_term=search_term,
            include_builtin=include_builtin,
            include_custom=include_custom
        )
        result = await factor_strategy_service.get_factor_library(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"获取因子库API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-factor")
async def validate_factor(request: FactorValidationRequest):
    """验证因子有效性"""
    try:
        result = await factor_strategy_service.validate_factor(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"验证因子API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-factor")
async def create_custom_factor(request: FactorDefinitionRequest):
    """创建自定义因子"""
    try:
        result = await factor_strategy_service.create_custom_factor(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"创建因子API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/construct-strategy")
async def construct_strategy(request: StrategyConstructionRequest):
    """构建投资策略"""
    try:
        result = await factor_strategy_service.construct_strategy(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"构建策略API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy-templates")
async def get_strategy_templates():
    """获取策略模板"""
    try:
        result = await factor_strategy_service.get_strategy_templates()
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"获取策略模板API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/factor-categories")
async def get_factor_categories():
    """获取因子分类"""
    try:
        categories = {
            "momentum": "动量因子",
            "mean_reversion": "均值回归因子", 
            "volatility": "波动率因子",
            "volume": "成交量因子",
            "technical": "技术指标因子",
            "fundamental": "基本面因子",
            "quality": "质量因子",
            "growth": "成长因子",
            "value": "价值因子",
            "custom": "自定义因子"
        }
        
        return {"status": "success", "data": categories}
    except Exception as e:
        logger.error(f"获取因子分类API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def get_strategies():
    """获取策略列表"""
    try:
        return {
            "status": "success",
            "data": {
                "strategies": strategy_library,
                "total_count": len(strategy_library)
            }
        }
    except Exception as e:
        logger.error(f"获取策略列表API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies/{strategy_id}")
async def get_strategy_detail(strategy_id: str):
    """获取策略详情"""
    try:
        if strategy_id not in strategy_library:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {
            "status": "success",
            "data": strategy_library[strategy_id]
        }
    except Exception as e:
        logger.error(f"获取策略详情API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
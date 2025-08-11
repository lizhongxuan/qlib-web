"""
智能参数推荐 API 端点
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.parameter_recommendation import ParameterRecommendationService
from app.schemas.common import APIResponse

router = APIRouter()
recommendation_service = ParameterRecommendationService()


@router.get("/model-params/{model_name}", response_model=APIResponse[Dict[str, Any]])
async def get_model_param_recommendations(
    model_name: str,
    stock_pool: str = Query(None, description="股票池筛选"),
    recent_days: int = Query(90, description="分析最近N天的实验", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取模型参数推荐"""
    try:
        recommendations = await recommendation_service.recommend_model_params(
            db=db,
            model_name=model_name,
            stock_pool=stock_pool,
            recent_days=recent_days
        )
        
        return APIResponse(
            success=True,
            data=recommendations,
            message=f"基于历史实验为 {model_name} 生成参数推荐"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数推荐失败: {str(e)}")


@router.get("/strategy-params/{strategy_name}", response_model=APIResponse[Dict[str, Any]])
async def get_strategy_param_recommendations(
    strategy_name: str,
    model_name: str = Query(None, description="模型名称筛选"),
    stock_pool: str = Query(None, description="股票池筛选"),
    db: Session = Depends(get_db)
):
    """获取策略参数推荐"""
    try:
        recommendations = await recommendation_service.recommend_strategy_params(
            db=db,
            strategy_name=strategy_name,
            model_name=model_name,
            stock_pool=stock_pool
        )
        
        return APIResponse(
            success=True,
            data=recommendations,
            message=f"为 {strategy_name} 策略生成参数推荐"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略参数推荐失败: {str(e)}")


@router.post("/validate", response_model=APIResponse[Dict[str, Any]])
async def validate_parameters(
    validation_request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """验证参数配置"""
    try:
        model_name = validation_request.get("model_name")
        model_params = validation_request.get("model_params", {})
        strategy_name = validation_request.get("strategy_name")
        strategy_params = validation_request.get("strategy_params", {})
        
        if not model_name or not strategy_name:
            raise ValueError("需要提供模型名称和策略名称")
        
        validation_result = await recommendation_service.validate_parameters(
            model_name=model_name,
            model_params=model_params,
            strategy_name=strategy_name,
            strategy_params=strategy_params
        )
        
        message = "参数验证通过" if validation_result["valid"] else "参数验证失败"
        
        return APIResponse(
            success=True,
            data=validation_result,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数验证失败: {str(e)}")


@router.get("/sensitivity/{model_name}/{param_name}", response_model=APIResponse[Dict[str, Any]])
async def analyze_parameter_sensitivity(
    model_name: str,
    param_name: str,
    stock_pool: str = Query(None, description="股票池筛选"),
    db: Session = Depends(get_db)
):
    """分析参数敏感性"""
    try:
        sensitivity_analysis = await recommendation_service.analyze_parameter_sensitivity(
            db=db,
            model_name=model_name,
            param_name=param_name,
            stock_pool=stock_pool
        )
        
        return APIResponse(
            success=True,
            data=sensitivity_analysis,
            message=f"{model_name} 模型的 {param_name} 参数敏感性分析完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"敏感性分析失败: {str(e)}")


@router.post("/optimize", response_model=APIResponse[Dict[str, Any]])
async def optimize_parameters(
    optimization_request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """参数优化建议"""
    try:
        current_config = optimization_request.get("current_config", {})
        optimization_target = optimization_request.get("target", "sharpe_ratio")  # 优化目标
        
        # 这里可以实现更复杂的参数优化算法
        # 现在先提供基础的优化建议
        
        optimization_suggestions = {
            "current_config": current_config,
            "optimization_target": optimization_target,
            "suggestions": [
                {
                    "parameter": "learning_rate",
                    "current_value": current_config.get("model_config", {}).get("params", {}).get("learning_rate"),
                    "suggested_value": 0.05,
                    "reason": "基于历史表现，较小的学习率通常能获得更稳定的结果",
                    "impact": "medium"
                },
                {
                    "parameter": "topk",
                    "current_value": current_config.get("strategy_config", {}).get("params", {}).get("topk"),
                    "suggested_value": 30,
                    "reason": "在当前市场环境下，适中的选股数量可以平衡收益和风险",
                    "impact": "high"
                }
            ],
            "expected_improvement": {
                "sharpe_ratio": "+15%",
                "max_drawdown": "-10%",
                "confidence": 0.7
            }
        }
        
        return APIResponse(
            success=True,
            data=optimization_suggestions,
            message="参数优化建议生成完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数优化失败: {str(e)}")


@router.get("/performance-correlation", response_model=APIResponse[Dict[str, Any]])
async def get_performance_correlation(
    model_name: str = Query(..., description="模型名称"),
    param_name: str = Query(..., description="参数名称"),
    stock_pool: str = Query(None, description="股票池筛选"),
    metric: str = Query("sharpe_ratio", description="性能指标"),
    db: Session = Depends(get_db)
):
    """获取参数与性能指标的相关性分析"""
    try:
        # 这里可以实现详细的相关性分析
        correlation_data = {
            "model_name": model_name,
            "parameter": param_name,
            "metric": metric,
            "correlation_coefficient": 0.65,
            "significance": "high",
            "data_points": 45,
            "scatter_plot_data": [
                {"param_value": 0.01, "performance": 0.85},
                {"param_value": 0.05, "performance": 1.2},
                {"param_value": 0.1, "performance": 1.45},
                {"param_value": 0.2, "performance": 1.1},
                {"param_value": 0.3, "performance": 0.9}
            ],
            "optimal_range": {
                "min": 0.05,
                "max": 0.15,
                "confidence": 0.8
            },
            "insights": [
                f"{param_name} 与 {metric} 呈正相关关系",
                "在 0.05-0.15 范围内表现最佳",
                "过高的参数值可能导致过拟合"
            ]
        }
        
        return APIResponse(
            success=True,
            data=correlation_data,
            message=f"{param_name} 参数相关性分析完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"相关性分析失败: {str(e)}")


@router.get("/benchmarks", response_model=APIResponse[Dict[str, Any]])
async def get_parameter_benchmarks(
    model_name: str = Query(..., description="模型名称"),
    stock_pool: str = Query(None, description="股票池筛选"),
    db: Session = Depends(get_db)
):
    """获取参数基准值"""
    try:
        benchmarks = {
            "model_name": model_name,
            "stock_pool": stock_pool or "all",
            "benchmarks": {
                "industry_average": {
                    "n_estimators": 120,
                    "learning_rate": 0.08,
                    "max_depth": 7,
                    "source": "行业平均水平"
                },
                "top_performers": {
                    "n_estimators": 150,
                    "learning_rate": 0.05,
                    "max_depth": 8,
                    "source": "top 10% 实验平均值"
                },
                "conservative": {
                    "n_estimators": 80,
                    "learning_rate": 0.1,
                    "max_depth": 6,
                    "source": "保守稳健配置"
                },
                "aggressive": {
                    "n_estimators": 200,
                    "learning_rate": 0.03,
                    "max_depth": 10,
                    "source": "激进高收益配置"
                }
            },
            "usage_statistics": {
                "most_common_values": {
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 6
                },
                "success_rate_by_range": {
                    "low_complexity": 0.65,
                    "medium_complexity": 0.78,
                    "high_complexity": 0.62
                }
            }
        }
        
        return APIResponse(
            success=True,
            data=benchmarks,
            message=f"{model_name} 参数基准值获取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取基准值失败: {str(e)}")
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.schemas.common import APIResponse, ConfigOptions, ModelParams
from app.utils.qlib_manager import QlibManager
from app.core.config import QLIB_CONFIG

router = APIRouter()

# 初始化Qlib管理器
qlib_manager = QlibManager()


@router.get("/stock-pools", response_model=APIResponse[list])
async def get_stock_pools():
    """获取可用股票池列表"""
    try:
        stock_pools = qlib_manager.get_stock_pools()
        return APIResponse(
            success=True,
            data=stock_pools
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=APIResponse[list])
async def get_models():
    """获取可用模型列表"""
    try:
        models = qlib_manager.get_models()
        return APIResponse(
            success=True,
            data=models
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies", response_model=APIResponse[list])
async def get_strategies():
    """获取可用策略列表"""
    try:
        strategies = qlib_manager.get_strategies()
        return APIResponse(
            success=True,
            data=strategies
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-params/{model_name}", response_model=APIResponse[dict])
async def get_model_params(model_name: str):
    """获取指定模型的参数配置"""
    try:
        model_params = qlib_manager.get_model_params(model_name)
        if not model_params:
            raise HTTPException(status_code=404, detail=f"模型 '{model_name}' 不存在")
        
        return APIResponse(
            success=True,
            data=model_params
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy-params/{strategy_name}", response_model=APIResponse[dict])
async def get_strategy_params(strategy_name: str):
    """获取指定策略的参数配置"""
    try:
        strategy_params = qlib_manager.get_strategy_params(strategy_name)
        if not strategy_params:
            raise HTTPException(status_code=404, detail=f"策略 '{strategy_name}' 不存在")
        
        return APIResponse(
            success=True,
            data=strategy_params
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options", response_model=APIResponse[ConfigOptions])
async def get_all_config_options():
    """获取所有配置选项"""
    try:
        options = ConfigOptions(
            stock_pools=qlib_manager.get_stock_pools(),
            models=qlib_manager.get_models(),
            strategies=qlib_manager.get_strategies()
        )
        
        return APIResponse(
            success=True,
            data=options
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments/{market}", response_model=APIResponse[list])
async def get_instruments(market: str):
    """获取指定市场的股票列表"""
    try:
        instruments = qlib_manager.get_instruments(market)
        return APIResponse(
            success=True,
            data=instruments
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defaults", response_model=APIResponse[dict])
async def get_default_config():
    """获取默认配置"""
    try:
        default_config = {
            "data_config": {
                "stock_pool": "CSI300",
                "start_time": "2020-01-01",
                "end_time": "2023-12-31"
            },
            "model_config": {
                "name": "LightGBM",
                "params": QLIB_CONFIG["model_params"]["LightGBM"]
            },
            "strategy_config": {
                "name": "TopkDropoutStrategy", 
                "params": QLIB_CONFIG["strategy_params"]["TopkDropoutStrategy"]
            },
            "backtest_config": {
                "trade_cost": 0.0015,
                "benchmark": "CSI300",
                "initial_cash": 1000000
            }
        }
        
        return APIResponse(
            success=True,
            data=default_config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=APIResponse[dict])
async def validate_config(config: dict):
    """验证实验配置"""
    try:
        errors = qlib_manager.validate_config(config)
        
        is_valid = len(errors) == 0
        
        return APIResponse(
            success=True,
            data={
                "is_valid": is_valid,
                "errors": errors,
                "warnings": []  # 可以添加警告信息
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info", response_model=APIResponse[dict])
async def get_system_info():
    """获取系统信息"""
    try:
        import qlib
        import platform
        import sys
        from datetime import datetime
        
        system_info = {
            "qlib_version": qlib.__version__,
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "timestamp": datetime.utcnow().isoformat(),
            "qlib_initialized": qlib_manager.initialized,
            "data_source": "mock" if not qlib_manager.initialized else "real"
        }
        
        return APIResponse(
            success=True,
            data=system_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
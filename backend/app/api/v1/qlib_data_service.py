"""
基于Qlib的数据服务API
提供金融数据获取、因子计算、数据预处理等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
import qlib
from qlib.config import REG_CN
from qlib.data import D
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta

# Qlib因子库导入
from qlib.contrib.data.handler import Alpha158, Alpha360
from qlib.data.filter import NameDFilter, ExpressionDFilter

logger = logging.getLogger(__name__)
router = APIRouter()

# 数据模型定义
class MarketDataRequest(BaseModel):
    instruments: Union[str, List[str]]  # 'csi300', 'csi500' or specific codes
    fields: List[str]
    start_time: str
    end_time: str
    freq: str = "day"

class FactorDataRequest(BaseModel):
    factor_names: List[str]
    instruments: Union[str, List[str]]
    start_time: str
    end_time: str
    standardize: bool = True

class DatasetRequest(BaseModel):
    handler_config: Dict[str, Any]
    segments: Dict[str, tuple]  # train, valid, test segments

class FactorCalculationRequest(BaseModel):
    expression: str
    instruments: Union[str, List[str]]
    start_time: str
    end_time: str
    freq: str = "day"

class QlibDataService:
    """基于Qlib的数据服务"""
    
    def __init__(self):
        self.initialized = False
        self.data_handlers = {
            'Alpha158': Alpha158,
            'Alpha360': Alpha360,
        }
        
    def initialize_qlib(self):
        """初始化Qlib环境"""
        if not self.initialized:
            try:
                qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)
                self.initialized = True
                logger.info("Qlib数据服务初始化成功")
            except Exception as e:
                logger.error(f"Qlib初始化失败: {e}")
                raise HTTPException(status_code=500, detail=f"Qlib初始化失败: {e}")
    
    async def get_market_data(self, request: MarketDataRequest) -> Dict[str, Any]:
        """获取市场数据"""
        self.initialize_qlib()
        
        try:
            # 处理instruments参数
            if isinstance(request.instruments, str):
                if request.instruments == "csi300":
                    instruments = D.instruments(market="csi300")
                elif request.instruments == "csi500":
                    instruments = D.instruments(market="csi500")
                elif request.instruments == "all":
                    instruments = D.instruments(market="all")
                else:
                    instruments = [request.instruments]
            else:
                instruments = request.instruments
            
            # 获取数据
            data = D.features(
                instruments=instruments,
                fields=request.fields,
                start_time=request.start_time,
                end_time=request.end_time,
                freq=request.freq
            )
            
            # 转换为前端可用格式
            if isinstance(data, pd.DataFrame):
                # 重置索引以便序列化
                data_reset = data.reset_index()
                
                # 转换为JSON可序列化的格式
                result = {
                    "data": data_reset.to_dict('records'),
                    "columns": list(data_reset.columns),
                    "shape": list(data.shape),
                    "instruments": list(instruments) if hasattr(instruments, '__iter__') else [instruments],
                    "timeRange": {
                        "start": request.start_time,
                        "end": request.end_time
                    },
                    "fields": request.fields,
                    "summary": {
                        "totalRecords": len(data),
                        "missingValues": data.isnull().sum().sum(),
                        "dataQuality": self._assess_data_quality(data)
                    }
                }
                
                return result
            else:
                raise ValueError("返回的数据格式不正确")
                
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取市场数据失败: {e}")
    
    async def get_factor_data(self, request: FactorDataRequest) -> Dict[str, Any]:
        """获取因子数据"""
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
            
            # 构建因子表达式字段
            factor_fields = []
            for factor_name in request.factor_names:
                # 基础因子表达式映射
                factor_expressions = {
                    'roc_5': '($close / Ref($close, 5)) - 1',  # 5日收益率
                    'roc_10': '($close / Ref($close, 10)) - 1',  # 10日收益率
                    'roc_20': '($close / Ref($close, 20)) - 1',  # 20日收益率
                    'ma_5': 'Mean($close, 5)',  # 5日均线
                    'ma_10': 'Mean($close, 10)',  # 10日均线
                    'ma_20': 'Mean($close, 20)',  # 20日均线
                    'std_5': 'Std($close, 5)',  # 5日波动率
                    'std_10': 'Std($close, 10)',  # 10日波动率
                    'std_20': 'Std($close, 20)',  # 20日波动率
                    'volume_ratio': '$volume / Mean($volume, 20)',  # 成交量比率
                    'high_low': '($high - $low) / $close',  # 振幅
                    'open_close': '($close - $open) / $open',  # 开收盘价比
                    'vwap_close': '($vwap - $close) / $close',  # VWAP与收盘价差
                    'turnover': '$volume * $close',  # 成交额
                    'pe_ratio': '1 / $pe',  # 市盈率倒数（简化）
                    'pb_ratio': '1 / $pb'   # 市净率倒数（简化）
                }
                
                if factor_name in factor_expressions:
                    factor_fields.append(factor_expressions[factor_name])
                else:
                    # 如果不在预定义中，直接使用因子名
                    factor_fields.append(f"${factor_name}")
            
            # 获取因子数据
            data = D.features(
                instruments=instruments,
                fields=factor_fields,
                start_time=request.start_time,
                end_time=request.end_time,
                freq="day"
            )
            
            # 数据标准化
            if request.standardize and not data.empty:
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                
                # 对数值列进行标准化
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                data[numeric_cols] = scaler.fit_transform(data[numeric_cols])
            
            # 计算因子统计信息
            factor_stats = {}
            for i, factor_name in enumerate(request.factor_names):
                if i < len(factor_fields) and i < len(data.columns):
                    col_data = data.iloc[:, i]
                    factor_stats[factor_name] = {
                        "mean": float(col_data.mean()) if not col_data.empty else 0.0,
                        "std": float(col_data.std()) if not col_data.empty else 0.0,
                        "min": float(col_data.min()) if not col_data.empty else 0.0,
                        "max": float(col_data.max()) if not col_data.empty else 0.0,
                        "missing_ratio": float(col_data.isnull().mean()) if not col_data.empty else 0.0,
                        "expression": factor_fields[i] if i < len(factor_fields) else factor_name
                    }
            
            # 转换为前端格式
            data_reset = data.reset_index()
            
            result = {
                "data": data_reset.to_dict('records'),
                "columns": list(data_reset.columns),
                "shape": list(data.shape),
                "factorStats": factor_stats,
                "instruments": list(instruments) if hasattr(instruments, '__iter__') else [instruments],
                "timeRange": {
                    "start": request.start_time,
                    "end": request.end_time
                },
                "standardized": request.standardize,
                "summary": {
                    "totalFactors": len(request.factor_names),
                    "totalRecords": len(data),
                    "dataQuality": self._assess_data_quality(data)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取因子数据失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取因子数据失败: {e}")
    
    async def create_dataset(self, request: DatasetRequest) -> Dict[str, Any]:
        """创建数据集"""
        self.initialize_qlib()
        
        try:
            handler_config = request.handler_config
            segments = request.segments
            
            # 创建数据处理器
            if handler_config.get('class') == 'Alpha158':
                handler = Alpha158(**handler_config.get('kwargs', {}))
            elif handler_config.get('class') == 'Alpha360':
                handler = Alpha360(**handler_config.get('kwargs', {}))
            else:
                # 使用通用DataHandlerLP
                handler = DataHandlerLP(**handler_config.get('kwargs', {}))
            
            # 创建数据集
            dataset = DatasetH(
                handler=handler,
                segments=segments
            )
            
            # 获取各段数据统计
            dataset_info = {
                "handlerType": handler_config.get('class', 'DataHandlerLP'),
                "segments": {},
                "totalSamples": 0
            }
            
            for segment_name, (start_time, end_time) in segments.items():
                try:
                    segment_data = dataset.prepare(segment_name, col_set="feature")
                    if segment_data is not None:
                        dataset_info["segments"][segment_name] = {
                            "timeRange": [start_time, end_time],
                            "sampleCount": len(segment_data),
                            "featureCount": segment_data.shape[1] if hasattr(segment_data, 'shape') else 0
                        }
                        dataset_info["totalSamples"] += len(segment_data)
                except Exception as seg_e:
                    logger.warning(f"处理数据段{segment_name}失败: {seg_e}")
                    dataset_info["segments"][segment_name] = {
                        "timeRange": [start_time, end_time],
                        "sampleCount": 0,
                        "featureCount": 0,
                        "error": str(seg_e)
                    }
            
            return dataset_info
            
        except Exception as e:
            logger.error(f"创建数据集失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建数据集失败: {e}")
    
    async def calculate_custom_factor(self, request: FactorCalculationRequest) -> Dict[str, Any]:
        """计算自定义因子"""
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
            
            # 计算自定义因子
            try:
                factor_data = D.features(
                    instruments=instruments,
                    fields=[request.expression],
                    start_time=request.start_time,
                    end_time=request.end_time,
                    freq=request.freq
                )
                
                # 因子有效性检查
                validity_check = self._validate_factor(factor_data, request.expression)
                
                # 因子统计信息
                factor_col = factor_data.iloc[:, 0] if not factor_data.empty else pd.Series()
                
                stats = {
                    "mean": float(factor_col.mean()) if not factor_col.empty else 0.0,
                    "std": float(factor_col.std()) if not factor_col.empty else 0.0,
                    "skewness": float(factor_col.skew()) if not factor_col.empty else 0.0,
                    "kurtosis": float(factor_col.kurt()) if not factor_col.empty else 0.0,
                    "missing_ratio": float(factor_col.isnull().mean()) if not factor_col.empty else 1.0,
                    "unique_ratio": float(factor_col.nunique() / len(factor_col)) if len(factor_col) > 0 else 0.0
                }
                
                # 转换数据格式
                data_reset = factor_data.reset_index()
                
                result = {
                    "data": data_reset.to_dict('records'),
                    "expression": request.expression,
                    "statistics": stats,
                    "validity": validity_check,
                    "shape": list(factor_data.shape),
                    "instruments": list(instruments) if hasattr(instruments, '__iter__') else [instruments],
                    "timeRange": {
                        "start": request.start_time,
                        "end": request.end_time
                    }
                }
                
                return result
                
            except Exception as calc_e:
                # 因子表达式计算失败
                return {
                    "error": f"因子表达式计算失败: {calc_e}",
                    "expression": request.expression,
                    "validity": {
                        "isValid": False,
                        "errors": [str(calc_e)],
                        "suggestions": ["检查表达式语法", "确认字段名称正确", "检查时间范围"]
                    }
                }
        
        except Exception as e:
            logger.error(f"计算自定义因子失败: {e}")
            raise HTTPException(status_code=500, detail=f"计算自定义因子失败: {e}")
    
    def _assess_data_quality(self, data: pd.DataFrame) -> str:
        """评估数据质量"""
        if data.empty:
            return "无数据"
        
        missing_ratio = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
        
        if missing_ratio < 0.01:
            return "优秀"
        elif missing_ratio < 0.05:
            return "良好"
        elif missing_ratio < 0.1:
            return "一般"
        else:
            return "较差"
    
    def _validate_factor(self, factor_data: pd.DataFrame, expression: str) -> Dict[str, Any]:
        """验证因子有效性"""
        is_valid = True
        errors = []
        warnings = []
        suggestions = []
        
        if factor_data.empty:
            is_valid = False
            errors.append("因子数据为空")
            suggestions.append("检查时间范围和股票代码")
        else:
            factor_col = factor_data.iloc[:, 0]
            
            # 检查缺失值比例
            missing_ratio = factor_col.isnull().mean()
            if missing_ratio > 0.5:
                warnings.append(f"缺失值比例过高: {missing_ratio:.2%}")
                suggestions.append("考虑调整因子表达式或数据范围")
            
            # 检查数值有效性
            if factor_col.dtype in ['object', 'string']:
                is_valid = False
                errors.append("因子值不是数值类型")
                suggestions.append("检查因子表达式是否正确")
            
            # 检查常数因子
            if factor_col.nunique() <= 1:
                warnings.append("因子值为常数")
                suggestions.append("因子可能没有区分度，考虑调整表达式")
            
            # 检查极值
            if not factor_col.empty:
                q99 = factor_col.quantile(0.99)
                q01 = factor_col.quantile(0.01)
                extreme_ratio = ((factor_col > q99) | (factor_col < q01)).mean()
                
                if extreme_ratio > 0.05:
                    warnings.append(f"极值比例较高: {extreme_ratio:.2%}")
                    suggestions.append("考虑进行数据清洗或winsorize处理")
        
        return {
            "isValid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "score": max(0, 100 - len(errors) * 30 - len(warnings) * 10)
        }

# 创建服务实例
data_service = QlibDataService()

@router.post("/market-data")
async def get_market_data(request: MarketDataRequest):
    """获取市场数据"""
    try:
        result = await data_service.get_market_data(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"市场数据API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/factor-data")  
async def get_factor_data(request: FactorDataRequest):
    """获取因子数据"""
    try:
        result = await data_service.get_factor_data(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"因子数据API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-dataset")
async def create_dataset(request: DatasetRequest):
    """创建训练数据集"""
    try:
        result = await data_service.create_dataset(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"创建数据集API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-factor")
async def calculate_custom_factor(request: FactorCalculationRequest):
    """计算自定义因子"""
    try:
        result = await data_service.calculate_custom_factor(request)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"计算因子API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instruments/{market}")
async def get_instruments(market: str = "csi300"):
    """获取股票列表"""
    try:
        data_service.initialize_qlib()
        instruments = D.instruments(market=market)
        
        # 转换为列表格式
        if hasattr(instruments, 'tolist'):
            instrument_list = instruments.tolist()
        else:
            instrument_list = list(instruments)
        
        return {
            "status": "success", 
            "data": {
                "market": market,
                "instruments": instrument_list,
                "count": len(instrument_list)
            }
        }
    except Exception as e:
        logger.error(f"获取股票列表API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-fields")
async def get_available_fields():
    """获取可用的数据字段"""
    try:
        # 预定义的可用字段
        available_fields = {
            "basic": {
                "price": ["$open", "$high", "$low", "$close", "$vwap"],
                "volume": ["$volume", "$amount"],
                "derived": ["$change", "$pct_chg"]
            },
            "technical": {
                "ma": ["Mean($close, 5)", "Mean($close, 10)", "Mean($close, 20)", "Mean($close, 60)"],
                "volatility": ["Std($close, 5)", "Std($close, 10)", "Std($close, 20)"],
                "momentum": ["($close/Ref($close, 5))-1", "($close/Ref($close, 10))-1", "($close/Ref($close, 20))-1"]
            },
            "fundamental": {
                "valuation": ["$pe", "$pb", "$ps", "$pcf"],
                "financial": ["$roe", "$roa", "$debt_to_equity"]
            }
        }
        
        return {"status": "success", "data": available_fields}
    except Exception as e:
        logger.error(f"获取可用字段API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-calendar")
async def get_data_calendar():
    """获取交易日历"""
    try:
        data_service.initialize_qlib()
        
        # 获取最近一年的交易日历
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 这里应该使用Qlib的calendar功能，暂时用简化版本
        calendar_info = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": 365,
            "trading_days": 244,  # 大约的交易天数
            "latest_trading_day": end_date
        }
        
        return {"status": "success", "data": calendar_info}
    except Exception as e:
        logger.error(f"获取交易日历API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
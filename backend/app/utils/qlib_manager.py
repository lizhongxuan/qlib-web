import os
import qlib
from qlib.data import D
from qlib.config import REG_CN, REG_US
from qlib.utils import init_instance_by_config
from loguru import logger
from typing import Dict, Any, List, Optional
import pandas as pd

from app.core.config import settings, QLIB_CONFIG


class QlibManager:
    """Qlib管理器"""
    
    def __init__(self):
        self.initialized = False
        self.region = settings.QLIB_REGION
        self.provider_uri = settings.QLIB_PROVIDER_URI
        
    def init_qlib(self):
        """初始化Qlib"""
        try:
            # 检查数据路径
            if not os.path.exists(os.path.expanduser(self.provider_uri)):
                logger.warning(f"Qlib data path not found: {self.provider_uri}")
                logger.info("Using mock mode for development")
                # 开发环境下可以不初始化真实数据
                self.initialized = True
                return
            
            # 初始化Qlib
            region = REG_CN if self.region == "cn" else REG_US
            qlib.init(
                provider_uri=self.provider_uri,
                region=region,
                auto_mount=True,
                clear_mem_cache=False
            )
            
            self.initialized = True
            logger.success("Qlib initialized successfully")
            
            # 验证数据访问
            try:
                instruments = D.instruments("csi300")[:5]  # 测试获取前5只股票
                logger.info(f"Data validation successful, found {len(instruments)} test instruments")
            except Exception as e:
                logger.warning(f"Data validation failed: {e}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Qlib: {e}")
            raise
    
    def get_stock_pools(self) -> List[str]:
        """获取可用股票池列表"""
        return QLIB_CONFIG["stock_pools"]
    
    def get_models(self) -> List[str]:
        """获取可用模型列表"""
        return QLIB_CONFIG["models"]
    
    def get_strategies(self) -> List[str]:
        """获取可用策略列表"""
        return QLIB_CONFIG["strategies"]
    
    def get_model_params(self, model_name: str) -> Dict[str, Any]:
        """获取模型参数配置"""
        return QLIB_CONFIG["model_params"].get(model_name, {})
    
    def get_strategy_params(self, strategy_name: str) -> Dict[str, Any]:
        """获取策略参数配置"""
        return QLIB_CONFIG["strategy_params"].get(strategy_name, {})
    
    def get_instruments(self, market: str = "csi300") -> List[str]:
        """获取股票列表"""
        if not self.initialized:
            # 返回mock数据用于开发
            return [
                "000001.XSHE", "000002.XSHE", "000858.XSHE",
                "600000.XSHG", "600036.XSHG", "600519.XSHG"
            ]
        
        try:
            instruments = D.instruments(market)
            return instruments.tolist() if hasattr(instruments, 'tolist') else list(instruments)
        except Exception as e:
            logger.warning(f"Failed to get instruments: {e}")
            return []
    
    def get_data(self, 
                 instruments: List[str], 
                 start_time: str, 
                 end_time: str,
                 fields: List[str] = None) -> Optional[pd.DataFrame]:
        """获取股票数据"""
        if not self.initialized:
            logger.warning("Qlib not initialized, returning mock data")
            return self._generate_mock_data(instruments, start_time, end_time, fields)
        
        try:
            if fields is None:
                fields = ["$open", "$high", "$low", "$close", "$volume", "$factor"]
                
            data = D.history(
                instruments=instruments,
                fields=fields,
                start_time=start_time,
                end_time=end_time
            )
            return data
        except Exception as e:
            logger.error(f"Failed to get data: {e}")
            return None
    
    def _generate_mock_data(self, 
                           instruments: List[str], 
                           start_time: str, 
                           end_time: str,
                           fields: List[str] = None) -> pd.DataFrame:
        """生成模拟数据用于开发测试"""
        import numpy as np
        from datetime import datetime, timedelta
        
        if fields is None:
            fields = ["$open", "$high", "$low", "$close", "$volume"]
        
        # 生成日期范围
        start_date = datetime.strptime(start_time, "%Y-%m-%d")
        end_date = datetime.strptime(end_time, "%Y-%m-%d")
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 过滤工作日
        date_range = date_range[date_range.weekday < 5]  # 只保留工作日
        
        data_list = []
        for instrument in instruments[:3]:  # 限制数量用于演示
            for date in date_range:
                # 生成模拟价格数据
                base_price = np.random.uniform(10, 100)
                open_price = base_price * np.random.uniform(0.95, 1.05)
                high_price = open_price * np.random.uniform(1.0, 1.1)
                low_price = open_price * np.random.uniform(0.9, 1.0)
                close_price = open_price * np.random.uniform(0.95, 1.05)
                volume = np.random.randint(1000000, 10000000)
                
                row_data = {
                    "datetime": date,
                    "instrument": instrument,
                    "$open": open_price,
                    "$high": high_price,
                    "$low": low_price,
                    "$close": close_price,
                    "$volume": volume
                }
                data_list.append(row_data)
        
        df = pd.DataFrame(data_list)
        df.set_index(["datetime", "instrument"], inplace=True)
        
        # 只返回请求的字段
        return df[[col for col in fields if col in df.columns]]
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证实验配置"""
        errors = {}
        
        # 验证股票池
        if config.get("data_config", {}).get("stock_pool") not in self.get_stock_pools():
            errors["stock_pool"] = "Invalid stock pool"
        
        # 验证模型
        if config.get("model_config", {}).get("name") not in self.get_models():
            errors["model"] = "Invalid model"
        
        # 验证策略
        if config.get("strategy_config", {}).get("name") not in self.get_strategies():
            errors["strategy"] = "Invalid strategy"
        
        return errors
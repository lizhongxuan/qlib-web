import os
import json
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from loguru import logger

from app.core.config import settings
from app.utils.qlib_manager import QlibManager


class ExperimentRunner:
    """实验运行器"""
    
    def __init__(self):
        self.qlib_manager = QlibManager()
        self.results_path = settings.RESULTS_PATH
        os.makedirs(self.results_path, exist_ok=True)
        
    async def run_backtest(self, 
                          experiment_id: str, 
                          config: Dict[str, Any],
                          progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """运行回测实验"""
        logger.info(f"Starting backtest for experiment {experiment_id}")
        
        try:
            # 更新进度：开始运行
            if progress_callback:
                await progress_callback(10, "正在初始化实验...")
            
            # 1. 验证配置
            validation_errors = self.qlib_manager.validate_config(config)
            if validation_errors:
                raise ValueError(f"Configuration validation failed: {validation_errors}")
            
            # 更新进度：配置验证完成
            if progress_callback:
                await progress_callback(20, "配置验证完成，开始加载数据...")
            
            # 2. 加载数据
            data_config = config["data_config"]
            stock_pool = data_config["stock_pool"]
            start_time = data_config["start_time"]
            end_time = data_config["end_time"]
            
            # 获取股票列表
            instruments = self.qlib_manager.get_instruments(stock_pool.lower())
            
            # 获取历史数据
            historical_data = self.qlib_manager.get_data(
                instruments=instruments[:10],  # 限制数量用于演示
                start_time=start_time,
                end_time=end_time
            )
            
            if historical_data is None or historical_data.empty:
                raise ValueError("No data available for the specified period and instruments")
            
            # 更新进度：数据加载完成
            if progress_callback:
                await progress_callback(40, "数据加载完成，开始模型训练...")
            
            # 3. 模拟模型训练
            model_config = config["model_config"]
            await self._simulate_model_training(model_config, progress_callback)
            
            # 更新进度：模型训练完成
            if progress_callback:
                await progress_callback(70, "模型训练完成，开始策略回测...")
            
            # 4. 模拟策略回测
            strategy_config = config["strategy_config"]
            backtest_config = config.get("backtest_config", {})
            
            results = await self._simulate_backtest(
                historical_data, 
                model_config, 
                strategy_config, 
                backtest_config,
                progress_callback
            )
            
            # 更新进度：回测完成
            if progress_callback:
                await progress_callback(90, "回测完成，正在生成报告...")
            
            # 5. 保存结果文件
            result_file_path = await self._save_results(experiment_id, results)
            results["result_file_path"] = result_file_path
            
            # 更新进度：完成
            if progress_callback:
                await progress_callback(100, "实验完成")
            
            logger.success(f"Backtest completed for experiment {experiment_id}")
            return results
            
        except Exception as e:
            logger.error(f"Backtest failed for experiment {experiment_id}: {e}")
            raise
    
    async def _simulate_model_training(self, 
                                     model_config: Dict[str, Any], 
                                     progress_callback: Optional[Callable] = None):
        """模拟模型训练过程"""
        import asyncio
        
        model_name = model_config["name"]
        logger.info(f"Training {model_name} model...")
        
        # 模拟训练时间
        training_steps = 5
        for step in range(training_steps):
            await asyncio.sleep(0.5)  # 模拟训练时间
            progress = 40 + (step + 1) * 6  # 40-70之间
            if progress_callback:
                await progress_callback(progress, f"训练{model_name}模型... ({step+1}/{training_steps})")
        
        logger.info("Model training completed")
    
    async def _simulate_backtest(self, 
                               data: pd.DataFrame,
                               model_config: Dict[str, Any],
                               strategy_config: Dict[str, Any],
                               backtest_config: Dict[str, Any],
                               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """模拟策略回测"""
        import asyncio
        
        logger.info("Running strategy backtest...")
        
        # 模拟回测计算
        await asyncio.sleep(1)
        if progress_callback:
            await progress_callback(85, "正在计算策略收益...")
        
        # 生成模拟结果
        results = self._generate_mock_results(backtest_config)
        
        logger.info("Strategy backtest completed")
        return results
    
    def _generate_mock_results(self, backtest_config: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟回测结果"""
        
        # 生成模拟收益序列
        np.random.seed(42)  # 固定种子保证结果一致
        trading_days = 252
        daily_returns = np.random.normal(0.001, 0.02, trading_days)  # 日收益率
        cumulative_returns = np.cumprod(1 + daily_returns) - 1
        
        # 生成日期序列
        start_date = datetime(2023, 1, 1)
        dates = [start_date + timedelta(days=i) for i in range(trading_days)]
        dates = [d for d in dates if d.weekday() < 5][:trading_days]  # 只保留工作日
        
        # 计算绩效指标
        total_return = cumulative_returns[-1]
        annual_return = (1 + total_return) ** (252 / trading_days) - 1
        volatility = np.std(daily_returns) * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 计算最大回撤
        cumulative_curve = 1 + cumulative_returns
        running_max = np.maximum.accumulate(cumulative_curve)
        drawdown = (cumulative_curve - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # 生成模拟持仓数据
        positions = []
        stocks = ["000001.XSHE", "000002.XSHE", "600000.XSHG", "600036.XSHG", "600519.XSHG"]
        for i in range(0, len(dates), 5):  # 每5天记录一次持仓
            date = dates[i].strftime("%Y-%m-%d")
            for j, stock in enumerate(stocks):
                weight = np.random.uniform(0.1, 0.3)
                positions.append({
                    "date": date,
                    "symbol": stock,
                    "weight": weight,
                    "return": np.random.uniform(-0.05, 0.05)
                })
        
        # 生成性能曲线数据
        performance_data = []
        benchmark_returns = np.random.normal(0.0005, 0.015, trading_days)
        benchmark_cumulative = np.cumprod(1 + benchmark_returns) - 1
        
        for i, date in enumerate(dates):
            performance_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "strategy_return": cumulative_returns[i],
                "benchmark_return": benchmark_cumulative[i],
                "daily_return": daily_returns[i],
                "daily_benchmark": benchmark_returns[i]
            })
        
        return {
            "performance": {
                "total_return": float(total_return),
                "annual_return": float(annual_return),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "volatility": float(volatility),
                "win_rate": float(np.random.uniform(0.45, 0.65)),
                "profit_loss_ratio": float(np.random.uniform(1.1, 1.8))
            },
            "positions": positions,
            "performance_data": performance_data,
            "statistics": {
                "total_trades": len(positions),
                "winning_trades": int(len(positions) * np.random.uniform(0.4, 0.7)),
                "avg_holding_period": float(np.random.uniform(3, 10)),
                "turnover_rate": float(np.random.uniform(0.5, 2.0))
            }
        }
    
    async def _save_results(self, experiment_id: str, results: Dict[str, Any]) -> str:
        """保存结果到文件"""
        try:
            filename = f"experiment_{experiment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = os.path.join(self.results_path, filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存结果
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Results saved to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def load_results(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从文件加载结果"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Results file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to load results: {e}")
            return None
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
import json
import os

from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentUpdate, ExperimentLogResponse
from app.utils.experiment_runner import ExperimentRunner
from app.utils.validators import DataValidator, SafeDataProcessor, ValidationError


class ExperimentService:
    """实验服务类"""
    
    def __init__(self):
        self.experiment_runner = ExperimentRunner()
    
    async def get_experiments(self, 
                            db: Session,
                            page: int = 1,
                            page_size: int = 20,
                            status: Optional[str] = None,
                            search: Optional[str] = None) -> Tuple[List[Experiment], int]:
        """获取实验列表"""
        
        # 构建查询条件
        conditions = [Experiment.is_deleted == False]
        
        if status:
            conditions.append(Experiment.status == status)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Experiment.name.ilike(search_term),
                    Experiment.description.ilike(search_term)
                )
            )
        
        # 查询总数
        total = db.query(Experiment).filter(and_(*conditions)).count()
        
        # 分页查询
        experiments = db.query(Experiment).filter(
            and_(*conditions)
        ).order_by(
            desc(Experiment.created_at)
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return experiments, total
    
    async def get_experiment(self, db: Session, experiment_id: str) -> Optional[Experiment]:
        """获取单个实验"""
        return db.query(Experiment).filter(
            Experiment.id == experiment_id,
            Experiment.is_deleted == False
        ).first()
    
    async def update_experiment(self, 
                              db: Session, 
                              experiment_id: str, 
                              update_data: ExperimentUpdate) -> Optional[Experiment]:
        """更新实验"""
        experiment = await self.get_experiment(db, experiment_id)
        if not experiment:
            return None
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(experiment, field):
                setattr(experiment, field, value)
        
        experiment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(experiment)
        
        return experiment
    
    async def delete_experiment(self, db: Session, experiment_id: str) -> bool:
        """删除实验（软删除）"""
        experiment = await self.get_experiment(db, experiment_id)
        if not experiment:
            return False
        
        experiment.is_deleted = True
        experiment.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    async def get_performance_data(self, 
                                 db: Session, 
                                 experiment_id: str) -> Optional[Dict[str, Any]]:
        """获取性能数据"""
        experiment = await self.get_experiment(db, experiment_id)
        if not experiment or not experiment.results:
            return None
        
        results = experiment.results
        
        # 提取性能数据
        performance_data = {
            "experiment_id": experiment_id,
            "performance_metrics": results.get("performance", {}),
            "performance_curve": results.get("performance_data", []),
            "statistics": results.get("statistics", {}),
            "benchmark_comparison": {
                "strategy_return": results.get("performance", {}).get("total_return", 0),
                "benchmark_return": 0.08,  # 模拟基准收益
                "excess_return": results.get("performance", {}).get("total_return", 0) - 0.08,
                "tracking_error": 0.15,
                "information_ratio": 0.5
            }
        }
        
        return performance_data
    
    async def get_positions_data(self, 
                               db: Session, 
                               experiment_id: str) -> Optional[Dict[str, Any]]:
        """获取持仓数据"""
        experiment = await self.get_experiment(db, experiment_id)
        if not experiment or not experiment.results:
            return None
        
        results = experiment.results
        positions = results.get("positions", [])
        
        # 处理持仓数据
        positions_data = {
            "experiment_id": experiment_id,
            "positions": positions,
            "position_summary": self._calculate_position_summary(positions),
            "turnover_analysis": self._calculate_turnover_analysis(positions)
        }
        
        return positions_data
    
    def _calculate_position_summary(self, positions: List[Dict]) -> Dict[str, Any]:
        """计算持仓摘要"""
        if not positions:
            return {}
        
        # 按股票聚合
        stock_summary = {}
        for pos in positions:
            symbol = pos.get("symbol")
            if symbol not in stock_summary:
                stock_summary[symbol] = {
                    "symbol": symbol,
                    "total_weight": 0,
                    "avg_weight": 0,
                    "days_held": 0,
                    "total_return": 0
                }
            stock_summary[symbol]["total_weight"] += pos.get("weight", 0)
            stock_summary[symbol]["days_held"] += 1
            stock_summary[symbol]["total_return"] += pos.get("return", 0)
        
        # 计算平均值
        for stock_data in stock_summary.values():
            stock_data["avg_weight"] = stock_data["total_weight"] / stock_data["days_held"]
            stock_data["avg_return"] = stock_data["total_return"] / stock_data["days_held"]
        
        return {
            "total_stocks": len(stock_summary),
            "stock_details": list(stock_summary.values()),
            "concentration": {
                "top_5_weight": sum(sorted([s["avg_weight"] for s in stock_summary.values()], reverse=True)[:5]),
                "top_10_weight": sum(sorted([s["avg_weight"] for s in stock_summary.values()], reverse=True)[:10])
            }
        }
    
    def _calculate_turnover_analysis(self, positions: List[Dict]) -> Dict[str, Any]:
        """计算换手率分析"""
        if not positions:
            return {}
        
        # 按日期分组
        daily_positions = {}
        for pos in positions:
            date = pos.get("date")
            if date not in daily_positions:
                daily_positions[date] = []
            daily_positions[date].append(pos)
        
        dates = sorted(daily_positions.keys())
        turnovers = []
        
        for i in range(1, len(dates)):
            prev_date = dates[i-1]
            curr_date = dates[i]
            
            prev_positions = {p["symbol"]: p["weight"] for p in daily_positions[prev_date]}
            curr_positions = {p["symbol"]: p["weight"] for p in daily_positions[curr_date]}
            
            # 计算换手率
            total_change = 0
            all_symbols = set(prev_positions.keys()) | set(curr_positions.keys())
            
            for symbol in all_symbols:
                prev_weight = prev_positions.get(symbol, 0)
                curr_weight = curr_positions.get(symbol, 0)
                total_change += abs(curr_weight - prev_weight)
            
            turnovers.append({
                "date": curr_date,
                "turnover_rate": total_change / 2  # 双边换手率的一半
            })
        
        avg_turnover = sum(t["turnover_rate"] for t in turnovers) / len(turnovers) if turnovers else 0
        
        return {
            "daily_turnovers": turnovers,
            "average_turnover": avg_turnover,
            "total_trading_days": len(turnovers)
        }
    
    async def get_experiment_logs(self, 
                                db: Session, 
                                experiment_id: str, 
                                lines: int = 100) -> Optional[ExperimentLogResponse]:
        """获取实验日志"""
        experiment = await self.get_experiment(db, experiment_id)
        if not experiment:
            return None
        
        # 模拟日志数据
        logs = []
        log_entries = [
            {"timestamp": "2024-01-01 10:00:00", "level": "INFO", "message": "实验开始执行"},
            {"timestamp": "2024-01-01 10:00:01", "level": "INFO", "message": "正在加载数据..."},
            {"timestamp": "2024-01-01 10:00:05", "level": "INFO", "message": "数据加载完成，共处理1000只股票"},
            {"timestamp": "2024-01-01 10:00:10", "level": "INFO", "message": "开始模型训练..."},
            {"timestamp": "2024-01-01 10:05:00", "level": "INFO", "message": "模型训练完成，准确率: 0.78"},
            {"timestamp": "2024-01-01 10:05:01", "level": "INFO", "message": "开始策略回测..."},
            {"timestamp": "2024-01-01 10:10:00", "level": "INFO", "message": "回测完成，总收益率: 15.6%"},
            {"timestamp": "2024-01-01 10:10:01", "level": "SUCCESS", "message": "实验执行成功"}
        ]
        
        # 根据实验状态生成对应的日志
        if experiment.status == "completed":
            logs = log_entries
        elif experiment.status == "running":
            logs = log_entries[:6]  # 部分日志
        elif experiment.status == "failed":
            logs = log_entries[:4] + [
                {"timestamp": "2024-01-01 10:05:00", "level": "ERROR", "message": "模型训练失败: 数据不足"}
            ]
        elif experiment.status == "pending":
            logs = [
                {"timestamp": "2024-01-01 09:59:00", "level": "INFO", "message": "实验已提交，等待执行..."}
            ]
        
        return ExperimentLogResponse(
            experiment_id=experiment_id,
            logs=logs[:lines],
            total_lines=len(logs),
            last_updated=experiment.updated_at
        )
    
    async def cancel_experiment(self, db: Session, experiment_id: str) -> bool:
        """取消实验"""
        experiment = await self.get_experiment(db, experiment_id)
        if not experiment:
            return False
        
        # 只有运行中或等待中的实验才能被取消
        if experiment.status not in ["running", "pending"]:
            return False
        
        experiment.status = "cancelled"
        experiment.completed_at = datetime.utcnow()
        experiment.error_message = "实验已被用户取消"
        experiment.updated_at = datetime.utcnow()
        
        db.commit()
        return True
"""
测试 Pydantic 数据模型验证
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.experiment import (
    DataConfigBase,
    ModelConfigBase,
    StrategyConfigBase,
    BacktestConfigBase,
    ExperimentCreate,
    ExperimentUpdate
)


class TestDataConfigValidation:
    """测试数据配置验证"""
    
    def test_valid_data_config(self):
        """测试有效的数据配置"""
        config = DataConfigBase(
            stock_pool="CSI300",
            start_time="2020-01-01",
            end_time="2021-12-31"
        )
        assert config.stock_pool == "CSI300"
        assert config.start_time == "2020-01-01"
        assert config.end_time == "2021-12-31"
    
    def test_invalid_stock_pool(self):
        """测试无效股票池"""
        with pytest.raises(ValidationError) as exc_info:
            DataConfigBase(
                stock_pool="INVALID_POOL",
                start_time="2020-01-01",
                end_time="2021-12-31"
            )
        
        error = exc_info.value.errors()[0]
        assert "股票池必须是以下之一" in error["msg"]
    
    def test_invalid_date_format(self):
        """测试无效日期格式"""
        with pytest.raises(ValidationError):
            DataConfigBase(
                stock_pool="CSI300",
                start_time="20200101",  # 错误格式
                end_time="2021-12-31"
            )
    
    def test_end_time_before_start_time(self):
        """测试结束时间早于开始时间"""
        with pytest.raises(ValidationError) as exc_info:
            DataConfigBase(
                stock_pool="CSI300",
                start_time="2021-01-01",
                end_time="2020-01-01"  # 早于开始时间
            )
        
        error = exc_info.value.errors()[0]
        assert "结束时间必须大于开始时间" in error["msg"]
    
    def test_date_range_too_long(self):
        """测试时间范围过长"""
        with pytest.raises(ValidationError) as exc_info:
            DataConfigBase(
                stock_pool="CSI300",
                start_time="2000-01-01",
                end_time="2025-01-01"  # 超过10年
            )
        
        error = exc_info.value.errors()[0]
        assert "时间范围不能超过10年" in error["msg"]


class TestModelConfigValidation:
    """测试模型配置验证"""
    
    def test_valid_model_config(self):
        """测试有效的模型配置"""
        config = ModelConfigBase(
            name="LightGBM",
            params={"n_estimators": 100, "learning_rate": 0.1}
        )
        assert config.name == "LightGBM"
        assert config.params["n_estimators"] == 100
    
    def test_invalid_model_name(self):
        """测试无效模型名称"""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfigBase(
                name="InvalidModel",
                params={}
            )
        
        error = exc_info.value.errors()[0]
        assert "模型必须是以下之一" in error["msg"]
    
    def test_params_too_large(self):
        """测试参数过大"""
        large_params = {"param_" + str(i): f"value_{i}" * 100 for i in range(100)}
        
        with pytest.raises(ValidationError) as exc_info:
            ModelConfigBase(
                name="LightGBM",
                params=large_params
            )
        
        error = exc_info.value.errors()[0]
        assert "模型参数过大" in error["msg"]


class TestExperimentValidation:
    """测试实验验证"""
    
    def test_valid_experiment_create(self):
        """测试有效的实验创建"""
        experiment = ExperimentCreate(
            name="测试实验_001",
            description="这是一个测试实验",
            config={
                "data_config": {
                    "stock_pool": "CSI300",
                    "start_time": "2020-01-01",
                    "end_time": "2021-12-31"
                },
                "model_config": {
                    "name": "LightGBM",
                    "params": {}
                },
                "strategy_config": {
                    "name": "TopkDropoutStrategy",
                    "params": {}
                }
            },
            tags=["测试", "示例"]
        )
        assert experiment.name == "测试实验_001"
        assert len(experiment.tags) == 2
    
    def test_invalid_experiment_name_special_chars(self):
        """测试包含特殊字符的实验名称"""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentCreate(
                name="测试<script>alert('xss')</script>",
                config={
                    "data_config": {
                        "stock_pool": "CSI300",
                        "start_time": "2020-01-01",
                        "end_time": "2021-12-31"
                    },
                    "model_config": {"name": "LightGBM", "params": {}},
                    "strategy_config": {"name": "TopkDropoutStrategy", "params": {}}
                }
            )
        
        error = exc_info.value.errors()[0]
        assert "只能包含字母、数字、中文、下划线、连字符和空格" in error["msg"]
    
    def test_experiment_name_with_leading_trailing_spaces(self):
        """测试前后有空格的实验名称"""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentCreate(
                name="  测试实验  ",
                config={
                    "data_config": {
                        "stock_pool": "CSI300",
                        "start_time": "2020-01-01",
                        "end_time": "2021-12-31"
                    },
                    "model_config": {"name": "LightGBM", "params": {}},
                    "strategy_config": {"name": "TopkDropoutStrategy", "params": {}}
                }
            )
        
        error = exc_info.value.errors()[0]
        assert "不能以空格开始或结束" in error["msg"]
    
    def test_too_many_tags(self):
        """测试标签过多"""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentCreate(
                name="测试实验",
                config={
                    "data_config": {
                        "stock_pool": "CSI300",
                        "start_time": "2020-01-01",
                        "end_time": "2021-12-31"
                    },
                    "model_config": {"name": "LightGBM", "params": {}},
                    "strategy_config": {"name": "TopkDropoutStrategy", "params": {}}
                },
                tags=[f"标签{i}" for i in range(11)]  # 超过10个标签
            )
        
        error = exc_info.value.errors()[0]
        assert "标签数量不能超过10个" in error["msg"]


class TestBacktestConfigValidation:
    """测试回测配置验证"""
    
    def test_valid_backtest_config(self):
        """测试有效的回测配置"""
        config = BacktestConfigBase(
            trade_cost=0.0015,
            benchmark="CSI300",
            initial_cash=1000000
        )
        assert config.trade_cost == 0.0015
        assert config.benchmark == "CSI300"
        assert config.initial_cash == 1000000
    
    def test_negative_trade_cost(self):
        """测试负数交易费用"""
        with pytest.raises(ValidationError):
            BacktestConfigBase(trade_cost=-0.01)
    
    def test_excessive_trade_cost(self):
        """测试过高的交易费用"""
        with pytest.raises(ValidationError):
            BacktestConfigBase(trade_cost=0.2)  # 超过10%
    
    def test_zero_initial_cash(self):
        """测试零初始资金"""
        with pytest.raises(ValidationError):
            BacktestConfigBase(initial_cash=0)
    
    def test_negative_initial_cash(self):
        """测试负初始资金"""
        with pytest.raises(ValidationError):
            BacktestConfigBase(initial_cash=-1000)
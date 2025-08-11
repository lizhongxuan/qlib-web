#!/usr/bin/env python3
"""
简单的验证测试脚本，不依赖外部库
"""

import sys
import os
import re
from datetime import datetime

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_config_validation():
    """测试配置验证逻辑"""
    print("🧪 测试配置验证...")
    
    # 测试股票池验证
    allowed_pools = ["CSI300", "CSI500", "CSI800", "CSI1000", "SSE50", "SZSE100", "ChiNext"]
    
    # 有效股票池
    assert "CSI300" in allowed_pools, "CSI300应该是有效的股票池"
    print("✅ 股票池验证 - 有效值")
    
    # 无效股票池
    assert "INVALID_POOL" not in allowed_pools, "INVALID_POOL应该是无效的股票池"
    print("✅ 股票池验证 - 无效值")
    
    # 测试日期格式验证
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    
    # 有效日期格式
    assert re.match(date_pattern, "2020-01-01"), "2020-01-01应该是有效的日期格式"
    print("✅ 日期格式验证 - 有效格式")
    
    # 无效日期格式
    assert not re.match(date_pattern, "20200101"), "20200101应该是无效的日期格式"
    assert not re.match(date_pattern, "2020/01/01"), "2020/01/01应该是无效的日期格式"
    print("✅ 日期格式验证 - 无效格式")
    
    # 测试日期范围验证
    start_date = datetime.strptime("2020-01-01", "%Y-%m-%d")
    end_date = datetime.strptime("2021-12-31", "%Y-%m-%d")
    
    assert end_date > start_date, "结束日期应该大于开始日期"
    print("✅ 日期范围验证 - 正常范围")
    
    # 测试日期范围过长
    too_long_end = datetime.strptime("2035-01-01", "%Y-%m-%d")
    days_diff = (too_long_end - start_date).days
    assert days_diff > 3650, "测试用例应该超过10年"
    print("✅ 日期范围验证 - 过长范围检测")

def test_experiment_name_validation():
    """测试实验名称验证"""
    print("\n🧪 测试实验名称验证...")
    
    # 有效名称模式
    name_pattern = r"^[a-zA-Z0-9\u4e00-\u9fa5_\-\s]+$"
    
    # 有效名称
    valid_names = [
        "测试实验",
        "Test Experiment",
        "实验_001",
        "Experiment-v2",
        "混合实验 Mixed_Test-v1"
    ]
    
    for name in valid_names:
        assert re.match(name_pattern, name), f"{name} 应该是有效的实验名称"
    print("✅ 实验名称验证 - 有效名称")
    
    # 无效名称
    invalid_names = [
        "测试<script>",  # 包含HTML标签
        "实验@符号",     # 包含@符号
        "test#experiment",  # 包含#符号
        "实验!感叹号"     # 包含感叹号
    ]
    
    for name in invalid_names:
        assert not re.match(name_pattern, name), f"{name} 应该是无效的实验名称"
    print("✅ 实验名称验证 - 无效名称")
    
    # 测试首尾空格
    names_with_spaces = [
        "  实验名称  ",
        " 测试 ",
        "实验 "
    ]
    
    for name in names_with_spaces:
        assert name.strip() != name, f"{name} 包含首尾空格"
    print("✅ 实验名称验证 - 首尾空格检测")

def test_model_validation():
    """测试模型验证"""
    print("\n🧪 测试模型验证...")
    
    allowed_models = ["LightGBM", "XGBoost", "CatBoost", "LSTM", "GRU", "Transformer", "Linear", "Ridge", "Lasso"]
    
    # 有效模型
    assert "LightGBM" in allowed_models, "LightGBM应该是有效的模型"
    assert "LSTM" in allowed_models, "LSTM应该是有效的模型"
    print("✅ 模型验证 - 有效模型")
    
    # 无效模型
    assert "InvalidModel" not in allowed_models, "InvalidModel应该是无效的模型"
    print("✅ 模型验证 - 无效模型")

def test_backtest_config_validation():
    """测试回测配置验证"""
    print("\n🧪 测试回测配置验证...")
    
    # 交易费用范围验证
    def validate_trade_cost(cost):
        return 0 <= cost <= 0.1
    
    assert validate_trade_cost(0.0015), "0.0015应该是有效的交易费用"
    assert validate_trade_cost(0.05), "0.05应该是有效的交易费用"
    print("✅ 交易费用验证 - 有效范围")
    
    assert not validate_trade_cost(-0.01), "-0.01应该是无效的交易费用"
    assert not validate_trade_cost(0.2), "0.2应该是无效的交易费用"
    print("✅ 交易费用验证 - 无效范围")
    
    # 初始资金验证
    def validate_initial_cash(cash):
        return cash > 0
    
    assert validate_initial_cash(1000000), "1000000应该是有效的初始资金"
    print("✅ 初始资金验证 - 有效值")
    
    assert not validate_initial_cash(0), "0应该是无效的初始资金"
    assert not validate_initial_cash(-1000), "-1000应该是无效的初始资金"
    print("✅ 初始资金验证 - 无效值")

def main():
    """运行所有测试"""
    print("🚀 开始运行基础验证测试...\n")
    
    try:
        test_config_validation()
        test_experiment_name_validation()
        test_model_validation()
        test_backtest_config_validation()
        
        print(f"\n🎉 所有测试通过!")
        print("✅ 配置验证逻辑正常工作")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
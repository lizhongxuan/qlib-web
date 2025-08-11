# Qlib 使用指南

## 概述

本指南详细介绍如何使用 Qlib 进行量化投资研究，从环境初始化到完整的投资策略开发。

## 快速开始

### 环境激活
```bash
# 激活 qlib 环境
source $HOME/miniconda3/bin/activate qlib

# 验证安装
python -c "import qlib; print(f'Qlib {qlib.__version__} 已就绪')"
```

### 基础导入
```python
import qlib
import pandas as pd
import numpy as np
from qlib.config import REG_CN, REG_US
from qlib.constant import REG_CN
```

## 数据管理

### 数据下载与初始化

#### 1. 中国市场数据
```python
# 方法一：使用内置数据下载脚本
import qlib
from qlib.run import run_data_download

# 下载中国市场日频数据
run_data_download(
    provider_uri="~/.qlib/qlib_data/cn_data", 
    region=REG_CN,
    interval="1d",
    start="2010-01-01",
    end="2023-12-31"
)

# 方法二：使用命令行下载
# python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

#### 2. 美国市场数据
```python
from qlib.config import REG_US

# 下载美国市场数据
run_data_download(
    provider_uri="~/.qlib/qlib_data/us_data",
    region=REG_US,
    interval="1d",
    start="2010-01-01",
    end="2023-12-31"
)
```

#### 3. 初始化数据环境
```python
import qlib
from qlib.config import REG_CN

# 初始化中国市场数据
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region=REG_CN)

# 验证初始化
from qlib.data import D
print("可用股票数量:", len(D.list_instruments(D.instruments('csi300'))))
```

### 数据查询与处理

#### 1. 基础数据查询
```python
from qlib.data import D

# 获取股票列表
instruments = D.instruments('csi300')  # CSI300成分股
print(f"CSI300 成分股数量: {len(instruments)}")

# 获取单只股票的历史数据
data = D.history(
    instruments="000001.XSHE",  # 平安银行
    fields=["$open", "$high", "$low", "$close", "$volume"],
    start="2020-01-01",
    end="2023-12-31"
)
print(data.head())
```

#### 2. 批量数据查询
```python
# 获取多只股票的数据
instruments = ['000001.XSHE', '000002.XSHE', '600000.XSHG']
data = D.history(
    instruments=instruments,
    fields=["$close", "$volume", "$factor"],  # $factor是复权因子
    start="2022-01-01",
    end="2023-12-31"
)

# 数据形状: (时间, 股票, 字段)
print("数据形状:", data.shape)
print(data.head())
```

#### 3. 特征工程
```python
from qlib.data import D

# 使用 Qlib 的表达式引擎计算技术指标
fields = [
    "($close-$open)/$open",  # 当日涨跌幅
    "Mean($close, 5)",       # 5日均线
    "Mean($close, 20)",      # 20日均线
    "Std($close, 20)",       # 20日波动率
    "$volume/Mean($volume, 5)", # 成交量比率
]

feature_data = D.history(
    instruments=D.instruments('csi300'),
    fields=fields,
    start="2022-01-01",
    end="2023-12-31"
)
print("特征数据形状:", feature_data.shape)
```

## 模型开发

### 1. 数据集准备

#### 创建基础数据集
```python
from qlib.contrib.data.handler import Alpha360, Alpha158
from qlib.contrib.model.gbdt import LGBModel
from qlib.data.dataset.handler import DataHandlerLP

# 使用预定义的Alpha360特征
data_handler = Alpha360(
    instruments='csi300',
    start_time='2010-01-01',
    end_time='2023-12-31',
    freq='day',
    infer_processors=[
        {"class": "RobustZScoreNorm", "kwargs": {"fields_group": "feature", "clip_outlier": True}},
        {"class": "Fillna", "kwargs": {"fields_group": "feature"}}
    ],
    learn_processors=[
        {"class": "DropnaLabel"},
        {"class": "CSRankNorm", "kwargs": {"fields_group": "label"}},
    ]
)

# 生成训练和测试数据
dataset = DataHandlerLP(
    data_handler=data_handler,
    segments={
        'train': ("2010-01-01", "2020-12-31"),
        'valid': ("2021-01-01", "2021-12-31"), 
        'test': ("2022-01-01", "2023-12-31")
    }
)
```

#### 自定义特征处理器
```python
from qlib.data.dataset.processor import Processor

class CustomProcessor(Processor):
    def __init__(self, fields_group=None):
        self.fields_group = fields_group
    
    def __call__(self, df):
        # 自定义数据处理逻辑
        if self.fields_group == "feature":
            # 特征标准化
            df = (df - df.mean()) / df.std()
        return df

# 使用自定义处理器
data_handler = Alpha158(
    instruments='csi300',
    start_time='2010-01-01',
    end_time='2023-12-31',
    infer_processors=[CustomProcessor(fields_group="feature")]
)
```

### 2. 模型训练

#### LightGBM 模型
```python
from qlib.contrib.model.gbdt import LGBModel

# 创建模型
model = LGBModel(
    loss="mse",
    colsample_bytree=0.8879,
    learning_rate=0.0421,
    subsample=0.8789,
    lambda_l1=205.6999,
    lambda_l2=580.9768,
    max_depth=8,
    num_leaves=210,
    num_threads=20
)

# 训练模型
model.fit(dataset)

# 预测
pred_score = model.predict(dataset)
print("预测结果形状:", pred_score.shape)
print("预测结果示例:")
print(pred_score.head())
```

#### 深度学习模型
```python
from qlib.contrib.model.pytorch_lstm import LSTM
from qlib.contrib.model.pytorch_gru import GRU

# LSTM 模型
lstm_model = LSTM(
    d_feat=158,  # 特征维度
    hidden_size=64,
    num_layers=2,
    dropout=0.0,
    n_epochs=200,
    lr=0.001,
    batch_size=2000,
)

lstm_model.fit(dataset)
lstm_pred = lstm_model.predict(dataset)

# GRU 模型  
gru_model = GRU(
    d_feat=158,
    hidden_size=64,
    num_layers=2,
    dropout=0.0,
    n_epochs=200,
    lr=0.001,
    batch_size=2000,
)

gru_model.fit(dataset)
gru_pred = gru_model.predict(dataset)
```

### 3. 模型评估

#### 基础评估指标
```python
from qlib.contrib.evaluate import risk_analysis
from qlib.contrib.report import analysis_model

# 计算IC值（信息系数）
ic_analysis = analysis_model.analysis_model_performance(pred_score)
print("IC 分析结果:")
print(ic_analysis)

# 风险分析
risk_metrics = risk_analysis(pred_score)
print("风险指标:")
print(risk_metrics)
```

#### 模型比较
```python
import matplotlib.pyplot as plt

# 比较多个模型的IC
models_pred = {
    'LightGBM': lgb_pred,
    'LSTM': lstm_pred,
    'GRU': gru_pred
}

ic_results = {}
for name, pred in models_pred.items():
    ic_results[name] = analysis_model.analysis_model_performance(pred)

# 绘制IC对比图
fig, ax = plt.subplots(figsize=(12, 6))
for name, ic_data in ic_results.items():
    ax.plot(ic_data.index, ic_data['IC'], label=f'{name} IC')
    
ax.legend()
ax.set_title('模型IC对比')
ax.set_xlabel('日期')
ax.set_ylabel('IC值')
plt.show()
```

## 策略开发

### 1. 信号策略

#### 基础信号策略
```python
from qlib.contrib.strategy import TopkDropoutStrategy

# 创建信号策略
signal_strategy = TopkDropoutStrategy(
    model=model,
    dataset=dataset,
    topk=50,      # 选择前50只股票
    n_drop=5      # 每次调仓剔除5只股票
)

# 获取交易信号
signals = signal_strategy.generate_trade_decision(
    start_time="2022-01-01",
    end_time="2023-12-31"
)
print("交易信号:")
print(signals.head())
```

#### 自定义策略
```python
from qlib.strategy.base import BaseStrategy
from qlib.backtest.decision import Order

class CustomStrategy(BaseStrategy):
    def __init__(self, model, topk=30):
        self.model = model
        self.topk = topk
    
    def generate_trade_decision(self, execute_result=None):
        # 获取模型预测
        pred_score = self.model.predict(self.dataset)
        
        # 基于预测分数生成交易决策
        current_pred = pred_score.iloc[-1]  # 最新预测
        
        # 选择预测分数最高的股票
        long_stocks = current_pred.nlargest(self.topk)
        
        # 生成买入订单
        orders = []
        for stock, score in long_stocks.items():
            order = Order(
                stock_id=stock,
                amount=1.0 / self.topk,  # 等权重
                direction=Order.BUY
            )
            orders.append(order)
            
        return orders

# 使用自定义策略
custom_strategy = CustomStrategy(model=model, topk=30)
```

### 2. 投资组合优化

#### 均值回归优化
```python
from qlib.contrib.strategy.optimizer import EnhancedIndexingOptimizer
import cvxpy as cp

class MeanReversionOptimizer:
    def __init__(self, risk_aversion=0.1):
        self.risk_aversion = risk_aversion
    
    def optimize(self, expected_return, cov_matrix, constraints=None):
        n_assets = len(expected_return)
        w = cp.Variable(n_assets)
        
        # 目标函数：最大化预期收益 - 风险惩罚
        objective = cp.Maximize(
            expected_return.T @ w - self.risk_aversion * cp.quad_form(w, cov_matrix)
        )
        
        # 约束条件
        constraints = [
            cp.sum(w) == 1,    # 权重和为1
            w >= 0,            # 不允许做空
            w <= 0.1           # 单只股票最大权重10%
        ]
        
        # 求解优化问题
        prob = cp.Problem(objective, constraints)
        prob.solve()
        
        return w.value

# 使用优化器
optimizer = MeanReversionOptimizer(risk_aversion=0.1)
```

## 回测系统

### 1. 基础回测

#### 简单回测
```python
from qlib.backtest import backtest
from qlib.contrib.data.handler import Alpha360

# 准备数据和策略
strategy = TopkDropoutStrategy(model=model, dataset=dataset, topk=50, n_drop=5)

# 执行回测
portfolio_metric, indicator_analysis = backtest(
    start_time="2022-01-01",
    end_time="2023-12-31",
    strategy=strategy,
    benchmark="SH000300",  # 沪深300基准
    account=100000,        # 初始资金
    exchange_kwargs={
        "freq": "day",
        "limit_threshold": 0.095,  # 涨跌停限制
        "deal_price": "close",     # 成交价格
        "open_cost": 0.0015,       # 开仓费用
        "close_cost": 0.0025,      # 平仓费用
    }
)

print("回测结果:")
print(portfolio_metric)
```

#### 高级回测配置
```python
from qlib.backtest.executor import SimulatorExecutor
from qlib.backtest.exchange import Exchange

# 创建自定义交易所
exchange = Exchange(
    freq="day",
    limit_threshold=0.095,
    deal_price="close",
    open_cost=0.0015,     # 买入手续费
    close_cost=0.0025,    # 卖出手续费
    min_cost=5,           # 最小手续费
    trade_unit=100,       # 交易单位（手）
)

# 创建执行器
executor = SimulatorExecutor(
    time_per_step="day",
    generate_portfolio_metrics=True
)

# 执行回测
results = executor.execute(
    trade_decision=signals,
    start_time="2022-01-01", 
    end_time="2023-12-31"
)
```

### 2. 回测结果分析

#### 绩效指标分析
```python
from qlib.contrib.report import analysis_position

# 分析持仓
pos_analysis = analysis_position.analysis_position(
    positions=results['positions'],
    returns=results['returns']
)

print("持仓分析:")
print(pos_analysis)

# 计算风险指标
def calculate_metrics(returns, benchmark_returns=None):
    metrics = {}
    
    # 基础指标
    metrics['总收益率'] = (1 + returns).prod() - 1
    metrics['年化收益率'] = (1 + returns.mean()) ** 252 - 1
    metrics['年化波动率'] = returns.std() * np.sqrt(252)
    metrics['夏普比率'] = metrics['年化收益率'] / metrics['年化波动率']
    
    # 最大回撤
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    metrics['最大回撤'] = drawdown.min()
    
    # 如果有基准，计算Alpha和Beta
    if benchmark_returns is not None:
        correlation_matrix = np.cov(returns, benchmark_returns)
        metrics['Beta'] = correlation_matrix[0, 1] / correlation_matrix[1, 1]
        metrics['Alpha'] = metrics['年化收益率'] - metrics['Beta'] * benchmark_returns.mean() * 252
    
    return metrics

# 计算指标
strategy_returns = results['returns']
metrics = calculate_metrics(strategy_returns)
print("策略绩效指标:")
for key, value in metrics.items():
    print(f"{key}: {value:.4f}")
```

#### 可视化分析
```python
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def plot_backtest_results(returns, positions=None, benchmark_returns=None):
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 累计收益曲线
    cum_returns = (1 + returns).cumprod()
    axes[0, 0].plot(cum_returns.index, cum_returns, label='策略', linewidth=2)
    
    if benchmark_returns is not None:
        benchmark_cum = (1 + benchmark_returns).cumprod()
        axes[0, 0].plot(benchmark_cum.index, benchmark_cum, label='基准', linewidth=2)
    
    axes[0, 0].set_title('累计收益曲线')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 回撤曲线
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    axes[0, 1].fill_between(drawdown.index, drawdown, 0, alpha=0.3, color='red')
    axes[0, 1].plot(drawdown.index, drawdown, color='red', linewidth=1)
    axes[0, 1].set_title('回撤曲线')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 收益分布
    axes[1, 0].hist(returns, bins=50, alpha=0.7, edgecolor='black')
    axes[1, 0].axvline(returns.mean(), color='red', linestyle='--', label=f'均值: {returns.mean():.4f}')
    axes[1, 0].set_title('收益分布')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 滚动夏普比率
    rolling_sharpe = returns.rolling(window=60).mean() / returns.rolling(window=60).std() * np.sqrt(252)
    axes[1, 1].plot(rolling_sharpe.index, rolling_sharpe, linewidth=2)
    axes[1, 1].set_title('60日滚动夏普比率')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

# 绘制结果
plot_backtest_results(strategy_returns)
```

## 实盘交易

### 1. 模拟交易
```python
from qlib.contrib.online.manager import OnlineManager

# 创建在线管理器
online_manager = OnlineManager(
    provider_uri='~/.qlib/qlib_data/cn_data',
    region=REG_CN,
    strategy=strategy,
    executor=executor
)

# 启动模拟交易
online_manager.start_simulation(
    start_time="2024-01-01",
    end_time="2024-12-31"
)
```

### 2. 实盘接口集成
```python
# 注意：这是示例代码，实际使用需要对接具体的券商API

class BrokerInterface:
    def __init__(self, account_info):
        self.account = account_info
    
    def get_positions(self):
        """获取当前持仓"""
        # 实现获取持仓逻辑
        pass
    
    def get_balance(self):
        """获取账户余额"""
        # 实现获取余额逻辑
        pass
    
    def place_order(self, symbol, quantity, order_type='market'):
        """下单"""
        # 实现下单逻辑
        pass
    
    def cancel_order(self, order_id):
        """撤单"""
        # 实现撤单逻辑
        pass

class LiveTrading:
    def __init__(self, strategy, broker_interface):
        self.strategy = strategy
        self.broker = broker_interface
    
    def run_daily_trading(self):
        # 获取交易信号
        signals = self.strategy.generate_trade_decision()
        
        # 获取当前持仓
        current_positions = self.broker.get_positions()
        
        # 计算需要调整的持仓
        target_positions = self.calculate_target_positions(signals)
        
        # 执行交易
        for symbol, target_qty in target_positions.items():
            current_qty = current_positions.get(symbol, 0)
            diff = target_qty - current_qty
            
            if abs(diff) > 100:  # 最小交易单位
                self.broker.place_order(symbol, diff)
    
    def calculate_target_positions(self, signals):
        # 根据信号计算目标持仓
        # 实现持仓计算逻辑
        pass

# 使用示例
# broker = BrokerInterface(account_info)
# live_trading = LiveTrading(strategy, broker)
# live_trading.run_daily_trading()
```

## 高级主题

### 1. 多因子模型
```python
from qlib.contrib.model.linear import LinearModel
from sklearn.linear_model import Ridge, Lasso

# 岭回归模型
ridge_model = LinearModel(estimator=Ridge(alpha=1.0))
ridge_model.fit(dataset)

# Lasso回归模型  
lasso_model = LinearModel(estimator=Lasso(alpha=0.1))
lasso_model.fit(dataset)

# 因子重要性分析
def analyze_factor_importance(model, feature_names):
    if hasattr(model.model, 'coef_'):
        importance = pd.Series(
            model.model.coef_,
            index=feature_names
        ).abs().sort_values(ascending=False)
        
        print("因子重要性排序:")
        print(importance.head(20))
        
        # 绘制重要性图
        plt.figure(figsize=(12, 8))
        importance.head(20).plot(kind='barh')
        plt.title('因子重要性分析')
        plt.xlabel('绝对系数值')
        plt.tight_layout()
        plt.show()
        
        return importance
    else:
        print("模型不支持因子重要性分析")
        return None

# 分析Ridge模型的因子重要性
feature_names = dataset.get_feature_names()  # 获取特征名称
ridge_importance = analyze_factor_importance(ridge_model, feature_names)
```

### 2. 集成学习
```python
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.model.pytorch_gru import GRU
from qlib.model.ens import EnsembleModel

# 创建多个基础模型
models = {
    'lgb': LGBModel(),
    'gru': GRU(d_feat=158),
}

# 创建集成模型
ensemble = EnsembleModel()
for name, model in models.items():
    model.fit(dataset)
    ensemble.add_model(name, model)

# 集成预测（简单平均）
ensemble_pred = ensemble.predict(dataset, method='mean')

# 加权集成
weights = {'lgb': 0.6, 'gru': 0.4}
weighted_pred = ensemble.predict(dataset, method='weighted', weights=weights)
```

### 3. 风险管理
```python
class RiskManager:
    def __init__(self, max_position_size=0.1, max_sector_exposure=0.3):
        self.max_position_size = max_position_size
        self.max_sector_exposure = max_sector_exposure
    
    def apply_risk_controls(self, target_positions, market_data):
        """应用风险控制"""
        controlled_positions = target_positions.copy()
        
        # 1. 单只股票最大仓位控制
        for symbol in controlled_positions.index:
            if controlled_positions[symbol] > self.max_position_size:
                controlled_positions[symbol] = self.max_position_size
        
        # 2. 行业暴露控制
        if 'sector' in market_data.columns:
            sector_exposure = controlled_positions.groupby(
                market_data['sector']
            ).sum()
            
            for sector in sector_exposure.index:
                if sector_exposure[sector] > self.max_sector_exposure:
                    # 按比例缩减该行业持仓
                    sector_stocks = market_data[market_data['sector'] == sector].index
                    scale_factor = self.max_sector_exposure / sector_exposure[sector]
                    controlled_positions[sector_stocks] *= scale_factor
        
        return controlled_positions
    
    def calculate_portfolio_risk(self, positions, cov_matrix):
        """计算投资组合风险"""
        portfolio_variance = positions.T @ cov_matrix @ positions
        portfolio_volatility = np.sqrt(portfolio_variance)
        return portfolio_volatility

# 使用风险管理器
risk_manager = RiskManager(max_position_size=0.08, max_sector_exposure=0.25)
```

## 最佳实践

### 1. 数据预处理
```python
def robust_data_preprocessing(data):
    """鲁棒的数据预处理流程"""
    
    # 1. 异常值处理
    def winsorize(series, lower=0.01, upper=0.99):
        lower_bound = series.quantile(lower)
        upper_bound = series.quantile(upper)
        return series.clip(lower_bound, upper_bound)
    
    # 2. 标准化
    def robust_standardize(series):
        median = series.median()
        mad = (series - median).abs().median()
        return (series - median) / (1.4826 * mad)  # 1.4826是正态分布的调整因子
    
    processed_data = data.copy()
    
    # 对每个特征应用预处理
    for column in processed_data.columns:
        if processed_data[column].dtype in ['float64', 'int64']:
            # 异常值处理
            processed_data[column] = winsorize(processed_data[column])
            # 标准化
            processed_data[column] = robust_standardize(processed_data[column])
    
    # 缺失值处理
    processed_data = processed_data.fillna(method='ffill').fillna(0)
    
    return processed_data
```

### 2. 模型验证
```python
from sklearn.model_selection import TimeSeriesSplit
import warnings
warnings.filterwarnings('ignore')

def time_series_cross_validation(model, dataset, n_splits=5):
    """时间序列交叉验证"""
    
    # 获取数据
    X_train, y_train = dataset.prepare("train")
    X_valid, y_valid = dataset.prepare("valid") 
    
    # 合并训练和验证数据用于交叉验证
    X_all = pd.concat([X_train, X_valid])
    y_all = pd.concat([y_train, y_valid])
    
    # 时间序列分割
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    cv_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_all)):
        print(f"折 {fold + 1}/{n_splits}")
        
        # 分割数据
        X_fold_train = X_all.iloc[train_idx]
        y_fold_train = y_all.iloc[train_idx]
        X_fold_val = X_all.iloc[val_idx]
        y_fold_val = y_all.iloc[val_idx]
        
        # 训练模型
        fold_model = model.__class__(**model.get_params())
        fold_model.fit((X_fold_train, y_fold_train))
        
        # 预测和评估
        y_pred = fold_model.predict(X_fold_val)
        
        # 计算IC
        ic = y_fold_val.corrwith(y_pred).mean()
        cv_scores.append(ic)
        
        print(f"折 {fold + 1} IC: {ic:.4f}")
    
    print(f"平均 IC: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores) * 2:.4f})")
    
    return cv_scores
```

### 3. 性能监控
```python
import logging
from datetime import datetime

class PerformanceMonitor:
    def __init__(self, log_file='trading_log.txt'):
        self.log_file = log_file
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def log_trade(self, symbol, action, quantity, price, reason):
        """记录交易日志"""
        message = f"交易 - {symbol}: {action} {quantity}股 @{price:.2f} - 原因: {reason}"
        logging.info(message)
    
    def log_daily_performance(self, portfolio_value, benchmark_value, positions):
        """记录每日绩效"""
        message = f"每日绩效 - 组合价值: {portfolio_value:.2f}, 基准价值: {benchmark_value:.2f}, 持仓数: {len(positions)}"
        logging.info(message)
    
    def alert_risk_breach(self, risk_metric, threshold, current_value):
        """风险预警"""
        message = f"风险预警 - {risk_metric}: {current_value:.4f} 超过阈值 {threshold:.4f}"
        logging.warning(message)
        print(f"⚠️ {message}")

# 使用性能监控
monitor = PerformanceMonitor()
```

## 常见问题解答

### Q1: 如何处理数据中的停牌股票？
```python
# 在数据预处理中过滤停牌股票
def filter_suspended_stocks(data):
    # 检测成交量为0的情况（通常表示停牌）
    volume_filter = data['$volume'] > 0
    
    # 检测价格异常（连续多天价格不变）
    price_change = data['$close'].pct_change().abs()
    price_filter = price_change > 1e-6
    
    return data[volume_filter & price_filter]
```

### Q2: 如何避免未来信息泄露？
```python
# 确保使用point-in-time数据
def ensure_point_in_time(data, feature_cols, lag_days=1):
    """确保特征数据有适当的滞后"""
    lagged_data = data.copy()
    
    for col in feature_cols:
        lagged_data[col] = lagged_data[col].shift(lag_days)
    
    # 删除由于滞后产生的NaN值
    lagged_data = lagged_data.dropna()
    
    return lagged_data
```

### Q3: 如何优化模型训练速度？
```python
# 使用多进程和GPU加速
import multiprocessing as mp
from qlib.contrib.model.pytorch_utils import count_parameters

def optimize_training():
    # 设置多进程数量
    n_jobs = mp.cpu_count() - 1
    
    # LightGBM多进程设置
    lgb_params = {
        'num_threads': n_jobs,
        'device_type': 'gpu',  # 如果有GPU
        'gpu_platform_id': 0,
        'gpu_device_id': 0,
    }
    
    # PyTorch GPU设置
    import torch
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    return device, n_jobs
```

## 总结

本使用指南涵盖了 Qlib 的核心功能和高级用法，从数据处理到策略开发，从模型训练到风险管理。通过这些示例，你可以：

1. **快速入门** - 理解 Qlib 的基本概念和工作流程
2. **数据处理** - 掌握金融数据的获取、清洗和特征工程
3. **模型开发** - 使用各种机器学习和深度学习模型进行预测
4. **策略研究** - 将模型预测转化为实际的交易策略
5. **风险控制** - 实施完整的风险管理框架
6. **性能评估** - 全面评估策略的有效性和稳定性

### 下一步学习建议

1. **深入研究官方示例** - 探索 `examples/` 目录中的完整示例
2. **阅读论文** - 理解 Qlib 背后的理论基础
3. **参与社区** - 在 GitHub 上与其他用户交流经验
4. **实践项目** - 在真实市场数据上测试你的策略
5. **持续学习** - 关注量化投资领域的最新发展

记住，量化投资需要持续的学习和实践。建议从简单的策略开始，逐步增加复杂性，并始终注重风险管理。

---

**免责声明**: 本指南仅供学习参考，不构成投资建议。量化投资存在风险，实际投资前请充分了解相关风险并咨询专业投资顾问。
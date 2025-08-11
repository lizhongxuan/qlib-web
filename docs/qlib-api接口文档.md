## Qlib Web Console API 接口设计 (V1)

本文档定义了 Qlib Web Console 前后端交互所需的 RESTful API 接口。所有接口均以 `/api/v1` 为前缀。

---

### 1. 实验接口 (Experiments)

**资源路径**: `/api/v1/experiments`

#### 1.1 创建并启动一个新实验
* **Endpoint**: `POST /experiments`
* **功能**: 接收前端传来的回测配置，创建一个异步计算任务，并立即返回任务ID。
* **请求体 (Request Body)**:
  ```json
  {
    "name": "我的第一次动量策略实验",
    "data_config": {
      "stock_pool": "CSI300",
      "start_time": "2018-01-01",
      "end_time": "2022-12-31"
    },
    "model_config": {
      "name": "LightGBM",
      "params": { "n_estimators": 100 }
    },
    "strategy_config": {
      "name": "TopkDropoutStrategy",
      "params": { "topk": 50, "n_drop_days": 5 }
    },
    "backtest_config": {
      "trade_cost": 0.0015
    }
  }
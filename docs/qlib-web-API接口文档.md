# Qlib Web 核心 API 接口文档

本文档定义了 Qlib Web 量化研究平台的核心 RESTful API 接口。所有接口均以 `/api/v1` 为前缀。

---

## 目录

- [1. 认证管理](#1-认证管理)
- [2. 实验管理](#2-实验管理)
- [3. 配置管理](#3-配置管理)
- [4. 模板管理](#4-模板管理)
- [5. 基础分析](#5-基础分析)
- [6. 系统接口](#6-系统接口)

---

## 1. 认证管理

### 1.1 用户登录
- **Endpoint**: `POST /auth/login`
- **功能**: 用户身份验证
- **请求体**:
```json
{
  "username": "user123",
  "password": "secure_password"
}
```
- **响应**:
```json
{
  "success": true,
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "user": {
    "id": "uuid-string",
    "username": "user123",
    "email": "user@example.com"
  }
}
```

### 1.2 用户注册
- **Endpoint**: `POST /auth/register`
- **请求体**:
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "张三"
}
```

### 1.3 刷新令牌
- **Endpoint**: `POST /auth/refresh`
- **请求头**: `Authorization: Bearer <refresh_token>`
- **响应**:
```json
{
  "success": true,
  "access_token": "new-jwt-token"
}
```

### 1.4 获取用户信息
- **Endpoint**: `GET /users/me`
- **请求头**: `Authorization: Bearer <access_token>`

---

## 2. 实验管理

### 2.1 创建实验
- **Endpoint**: `POST /experiments`
- **功能**: 创建新的量化实验
- **请求体**:
```json
{
  "name": "动量策略实验_20240808",
  "description": "测试动量因子在CSI300的表现",
  "data_config": {
    "stock_pool": "CSI300",
    "start_time": "2020-01-01",
    "end_time": "2023-12-31",
    "features": ["close", "volume", "factor1"]
  },
  "model_config": {
    "name": "LightGBM",
    "params": {
      "n_estimators": 100,
      "learning_rate": 0.1,
      "max_depth": 6
    }
  },
  "strategy_config": {
    "name": "TopkDropoutStrategy",
    "params": {
      "topk": 50,
      "n_drop_days": 5
    }
  },
  "backtest_config": {
    "trade_cost": 0.0015,
    "min_periods": 20
  }
}
```
- **响应**:
```json
{
  "success": true,
  "experiment_id": "exp_uuid_string",
  "task_id": "task_uuid_string",
  "message": "实验创建成功，正在执行中"
}
```

### 2.2 获取实验列表
- **Endpoint**: `GET /experiments`
- **查询参数**:
  - `page`: 页码 (默认: 1)
  - `page_size`: 每页大小 (默认: 20)
  - `status`: 状态筛选 (`pending`, `running`, `completed`, `failed`)
  - `search`: 名称搜索关键词
- **响应**:
```json
{
  "success": true,
  "data": {
    "experiments": [
      {
        "id": "exp_uuid_string",
        "name": "动量策略实验_20240808",
        "status": "completed",
        "created_at": "2024-08-08T10:00:00Z",
        "completed_at": "2024-08-08T10:30:00Z",
        "performance_summary": {
          "annual_return": 0.15,
          "sharpe_ratio": 1.2,
          "max_drawdown": 0.08
        }
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 2.3 获取实验详情
- **Endpoint**: `GET /experiments/{experiment_id}`
- **功能**: 获取指定实验的详细信息
- **响应**:
```json
{
  "success": true,
  "data": {
    "id": "exp_uuid_string",
    "name": "动量策略实验_20240808",
    "description": "测试动量因子在CSI300的表现",
    "status": "completed",
    "created_at": "2024-08-08T10:00:00Z",
    "completed_at": "2024-08-08T10:30:00Z",
    "config": {
      "data_config": {...},
      "model_config": {...},
      "strategy_config": {...},
      "backtest_config": {...}
    },
    "performance_metrics": {
      "annual_return": 0.15,
      "sharpe_ratio": 1.2,
      "max_drawdown": 0.08,
      "calmar_ratio": 1.875,
      "information_ratio": 0.8
    }
  }
}
```

### 2.4 获取实验性能数据
- **Endpoint**: `GET /experiments/{experiment_id}/performance`
- **功能**: 获取实验的性能时序数据
- **响应**:
```json
{
  "success": true,
  "data": {
    "returns": [
      {
        "date": "2020-01-01",
        "portfolio_return": 0.002,
        "benchmark_return": 0.001,
        "cumulative_return": 0.002
      }
    ],
    "positions": [
      {
        "date": "2020-01-01",
        "holdings": {
          "000001.SZ": 0.05,
          "000002.SZ": 0.03
        }
      }
    ]
  }
}
```

### 2.5 删除实验
- **Endpoint**: `DELETE /experiments/{experiment_id}`
- **功能**: 删除指定实验

### 2.6 停止实验
- **Endpoint**: `POST /experiments/{experiment_id}/stop`
- **功能**: 停止正在运行的实验

---

## 3. 配置管理

### 3.1 获取股票池列表
- **Endpoint**: `GET /config/stock-pools`
- **响应**:
```json
{
  "success": true,
  "data": [
    {
      "name": "CSI300",
      "display_name": "沪深300",
      "description": "沪深两市市值最大的300只股票"
    },
    {
      "name": "CSI500",
      "display_name": "中证500",
      "description": "中证500指数成分股"
    }
  ]
}
```

### 3.2 获取模型列表
- **Endpoint**: `GET /config/models`
- **响应**:
```json
{
  "success": true,
  "data": [
    {
      "name": "LightGBM",
      "display_name": "LightGBM",
      "category": "tree_based",
      "description": "轻量级梯度提升机"
    },
    {
      "name": "LinearRegression",
      "display_name": "线性回归",
      "category": "linear",
      "description": "线性回归模型"
    }
  ]
}
```

### 3.3 获取模型参数配置
- **Endpoint**: `GET /config/model-params/{model_name}`
- **响应**:
```json
{
  "success": true,
  "data": {
    "model": "LightGBM",
    "parameters": [
      {
        "name": "n_estimators",
        "type": "int",
        "default": 100,
        "min": 10,
        "max": 1000,
        "description": "决策树数量"
      },
      {
        "name": "learning_rate",
        "type": "float",
        "default": 0.1,
        "min": 0.01,
        "max": 1.0,
        "description": "学习率"
      }
    ]
  }
}
```

---

## 4. 模板管理

### 4.1 获取模板列表
- **Endpoint**: `GET /templates`
- **查询参数**:
  - `category`: 模板分类
- **响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "template_uuid",
      "name": "动量策略模板",
      "description": "基于价格动量的选股策略模板",
      "category": "momentum",
      "created_at": "2024-08-08T10:00:00Z"
    }
  ]
}
```

### 4.2 使用模板创建实验
- **Endpoint**: `POST /templates/{template_id}/create-experiment`
- **请求体**:
```json
{
  "name": "基于模板的实验",
  "data_config": {
    "start_time": "2023-01-01",
    "end_time": "2023-12-31"
  }
}
```

### 4.3 保存实验为模板
- **Endpoint**: `POST /experiments/{experiment_id}/save-as-template`
- **请求体**:
```json
{
  "name": "我的策略模板",
  "description": "基于成功实验创建的模板",
  "category": "custom"
}
```

---

## 5. 基础分析

### 5.1 获取实验统计摘要
- **Endpoint**: `GET /analysis/{experiment_id}/summary`
- **响应**:
```json
{
  "success": true,
  "data": {
    "performance_metrics": {
      "total_return": 0.258,
      "annual_return": 0.15,
      "sharpe_ratio": 1.2,
      "max_drawdown": 0.08,
      "volatility": 0.18,
      "win_rate": 0.62
    },
    "trade_statistics": {
      "total_trades": 156,
      "avg_holding_days": 12.5,
      "turnover_rate": 2.1
    }
  }
}
```

### 5.2 获取持仓分析
- **Endpoint**: `GET /analysis/{experiment_id}/positions`
- **查询参数**:
  - `date`: 指定日期 (可选)
- **响应**:
```json
{
  "success": true,
  "data": {
    "date": "2023-12-31",
    "holdings": [
      {
        "symbol": "000001.SZ",
        "name": "平安银行",
        "weight": 0.05,
        "sector": "金融",
        "return": 0.12
      }
    ],
    "sector_allocation": {
      "金融": 0.25,
      "科技": 0.30,
      "医药": 0.15
    }
  }
}
```

---

## 6. 系统接口

### 6.1 获取系统状态
- **Endpoint**: `GET /system/status`
- **响应**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "v2.0.0",
    "uptime": 86400,
    "active_experiments": 5,
    "queue_length": 2
  }
}
```

### 6.2 获取仪表盘数据
- **Endpoint**: `GET /dashboard/summary`
- **功能**: 获取仪表盘概览数据
- **响应**:
```json
{
  "success": true,
  "data": {
    "total_experiments": 50,
    "recent_experiments": [
      {
        "id": "exp_uuid",
        "name": "最新实验",
        "status": "completed",
        "performance": {
          "annual_return": 0.15,
          "sharpe_ratio": 1.2
        }
      }
    ],
    "system_metrics": {
      "cpu_usage": 45.6,
      "memory_usage": 62.3,
      "active_tasks": 3
    }
  }
}
```

---

## 认证与错误处理

### JWT Token 认证
- 需要认证的API在请求头中包含：`Authorization: Bearer <access_token>`
- Token有效期为2小时，使用refresh token进行刷新

### 统一错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "start_time",
      "reason": "日期格式不正确"
    }
  },
  "request_id": "req_uuid_string"
}
```

### 常见错误码
- `AUTHENTICATION_ERROR`: 认证失败
- `AUTHORIZATION_ERROR`: 权限不足  
- `VALIDATION_ERROR`: 参数验证失败
- `RESOURCE_NOT_FOUND`: 资源不存在
- `INTERNAL_SERVER_ERROR`: 服务器内部错误

---

## API限流策略
- 认证用户：1000次/小时
- 匿名用户：100次/小时

---

*本文档最后更新时间: 2024-08-12*
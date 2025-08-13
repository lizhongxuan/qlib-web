# Qlib Web 完整 API 接口文档 (V2.0)

本文档定义了 Qlib Web 量化研究平台的完整 RESTful API 接口规范。所有接口均以 `/api/v1` 为前缀。

---

## 目录

- [1. 认证与用户管理](#1-认证与用户管理)
- [2. 实验管理](#2-实验管理)
- [3. 配置管理](#3-配置管理)
- [4. 模板管理](#4-模板管理)
- [5. 团队协作](#5-团队协作)
- [6. 分享系统](#6-分享系统)
- [7. 高级分析](#7-高级分析)
- [8. 系统监控](#8-系统监控)
- [9. 数据备份](#9-数据备份)
- [10. 通知系统](#10-通知系统)

---

## 1. 认证与用户管理

### 1.1 用户注册
- **Endpoint**: `POST /auth/register`
- **功能**: 注册新用户账号
- **请求体**:
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "张三"
}
```
- **响应**:
```json
{
  "success": true,
  "message": "注册成功，请检查邮箱进行验证",
  "user_id": "uuid-string"
}
```

### 1.2 用户登录
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
    "email": "user@example.com",
    "role": "ANALYST"
  }
}
```

### 1.3 刷新令牌
- **Endpoint**: `POST /auth/refresh`
- **功能**: 使用刷新令牌获取新的访问令牌
- **请求头**: `Authorization: Bearer <refresh_token>`
- **响应**:
```json
{
  "success": true,
  "access_token": "new-jwt-token"
}
```

### 1.4 用户信息
- **Endpoint**: `GET /users/me`
- **功能**: 获取当前用户信息
- **请求头**: `Authorization: Bearer <access_token>`
- **响应**:
```json
{
  "id": "uuid-string",
  "username": "user123",
  "email": "user@example.com",
  "full_name": "张三",
  "role": "ANALYST",
  "status": "ACTIVE",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-08-08T12:00:00Z"
}
```

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
- **功能**: 分页获取实验列表
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

### 4.1 创建模板
- **Endpoint**: `POST /templates`
- **功能**: 创建实验模板
- **请求体**:
```json
{
  "name": "动量策略模板",
  "description": "基于价格动量的选股策略模板",
  "category": "momentum",
  "config": {
    "model_config": {...},
    "strategy_config": {...}
  },
  "is_public": true
}
```

### 4.2 获取模板列表
- **Endpoint**: `GET /templates`
- **查询参数**:
  - `category`: 模板分类
  - `is_public`: 是否公开模板
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
      "creator": "user123",
      "created_at": "2024-08-08T10:00:00Z",
      "usage_count": 25
    }
  ]
}
```

### 4.3 使用模板创建实验
- **Endpoint**: `POST /templates/{template_id}/create-experiment`
- **功能**: 基于模板创建新实验
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

---

## 5. 团队协作

### 5.1 创建团队
- **Endpoint**: `POST /teams`
- **请求体**:
```json
{
  "name": "量化研究团队",
  "description": "专注于量化投资研究的团队"
}
```

### 5.2 邀请成员
- **Endpoint**: `POST /teams/{team_id}/members`
- **请求体**:
```json
{
  "username": "user456",
  "role": "ANALYST"
}
```

### 5.3 获取团队实验列表
- **Endpoint**: `GET /teams/{team_id}/experiments`
- **响应**:
```json
{
  "success": true,
  "data": {
    "experiments": [
      {
        "id": "exp_uuid",
        "name": "团队实验1",
        "creator": "user123",
        "status": "completed",
        "permissions": ["view", "edit", "share"]
      }
    ]
  }
}
```

---

## 6. 分享系统

### 6.1 创建分享链接
- **Endpoint**: `POST /shares`
- **请求体**:
```json
{
  "experiment_id": "exp_uuid",
  "share_type": "public",
  "permissions": ["view"],
  "password": "optional_password",
  "expires_at": "2024-12-31T23:59:59Z",
  "max_views": 100
}
```
- **响应**:
```json
{
  "success": true,
  "data": {
    "share_id": "share_uuid",
    "share_url": "https://qlib-web.example.com/share/share_uuid",
    "qr_code": "data:image/png;base64,..."
  }
}
```

### 6.2 访问分享内容
- **Endpoint**: `GET /shares/{share_id}`
- **查询参数**:
  - `password`: 访问密码 (如果需要)
- **响应**:
```json
{
  "success": true,
  "data": {
    "experiment": {
      "id": "exp_uuid",
      "name": "分享的实验",
      "performance_metrics": {...},
      "charts_data": {...}
    },
    "share_info": {
      "creator": "user123",
      "created_at": "2024-08-08T10:00:00Z",
      "view_count": 25
    }
  }
}
```

---

## 7. 高级分析

### 7.1 归因分析
- **Endpoint**: `GET /analysis/{experiment_id}/attribution`
- **响应**:
```json
{
  "success": true,
  "data": {
    "industry_attribution": {
      "金融": 0.025,
      "科技": 0.018,
      "医药": -0.005
    },
    "style_attribution": {
      "size": 0.012,
      "value": -0.008,
      "momentum": 0.020
    },
    "stock_selection_effect": 0.015,
    "timing_effect": -0.003
  }
}
```

### 7.2 风险分析
- **Endpoint**: `GET /analysis/{experiment_id}/risk`
- **响应**:
```json
{
  "success": true,
  "data": {
    "var_metrics": {
      "var_95": 0.025,
      "var_99": 0.045,
      "cvar_95": 0.032
    },
    "drawdown_analysis": {
      "max_drawdown": 0.08,
      "max_drawdown_duration": 45,
      "current_drawdown": 0.02
    },
    "correlation_analysis": {
      "market_correlation": 0.75,
      "sector_correlations": {...}
    }
  }
}
```

### 7.3 情景分析
- **Endpoint**: `POST /analysis/{experiment_id}/scenario`
- **请求体**:
```json
{
  "scenarios": [
    {
      "name": "市场下跌",
      "market_shock": -0.20,
      "sector_shocks": {
        "金融": -0.25,
        "科技": -0.15
      }
    }
  ]
}
```

### 7.4 蒙特卡洛模拟
- **Endpoint**: `POST /analysis/{experiment_id}/monte-carlo`
- **请求体**:
```json
{
  "simulation_count": 1000,
  "time_horizon": 252,
  "confidence_levels": [0.05, 0.95]
}
```

---

## 8. 系统监控

### 8.1 系统状态
- **Endpoint**: `GET /monitoring/system-status`
- **响应**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "uptime": 86400,
    "version": "v2.0.0",
    "components": {
      "database": "healthy",
      "redis": "healthy",
      "celery": "healthy"
    },
    "metrics": {
      "active_experiments": 5,
      "queue_length": 2,
      "cpu_usage": 45.6,
      "memory_usage": 62.3
    }
  }
}
```

### 8.2 资源监控
- **Endpoint**: `GET /monitoring/resources`
- **响应**:
```json
{
  "success": true,
  "data": {
    "cpu": {
      "usage_percent": 45.6,
      "load_average": [1.2, 1.5, 1.8]
    },
    "memory": {
      "total": 16000000000,
      "used": 9984000000,
      "available": 6016000000,
      "percent": 62.4
    },
    "disk": {
      "total": 500000000000,
      "used": 200000000000,
      "free": 300000000000,
      "percent": 40.0
    }
  }
}
```

---

## 9. 数据备份

### 9.1 创建备份
- **Endpoint**: `POST /backup/create`
- **请求体**:
```json
{
  "backup_type": "full",
  "description": "周备份_20240808",
  "include_files": true
}
```

### 9.2 获取备份列表
- **Endpoint**: `GET /backup/list`
- **响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "backup_uuid",
      "filename": "qlib_web_backup_20240808.tar.gz",
      "size": 1048576000,
      "created_at": "2024-08-08T02:00:00Z",
      "status": "completed"
    }
  ]
}
```

### 9.3 恢复备份
- **Endpoint**: `POST /backup/restore/{backup_id}`
- **请求体**:
```json
{
  "restore_type": "selective",
  "components": ["experiments", "users"]
}
```

---

## 10. 通知系统

### 10.1 获取通知列表
- **Endpoint**: `GET /notifications`
- **响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "notification_uuid",
      "type": "experiment_completed",
      "title": "实验完成",
      "message": "您的实验 '动量策略实验' 已完成",
      "is_read": false,
      "created_at": "2024-08-08T10:30:00Z"
    }
  ]
}
```

### 10.2 标记通知已读
- **Endpoint**: `PUT /notifications/{notification_id}/read`

### 10.3 通知设置
- **Endpoint**: `POST /notifications/settings`
- **请求体**:
```json
{
  "email_enabled": true,
  "browser_enabled": true,
  "experiment_completion": true,
  "system_alerts": true
}
```

---

## 错误处理

所有API响应都遵循统一的错误格式：

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
- `RESOURCE_CONFLICT`: 资源冲突
- `RATE_LIMIT_EXCEEDED`: 请求频率超限
- `INTERNAL_SERVER_ERROR`: 服务器内部错误

---

## 认证机制

### JWT Token 认证
- 所有需要认证的API都需要在请求头中包含：`Authorization: Bearer <access_token>`
- Token有效期为2小时，可使用refresh token进行刷新
- Token包含用户ID、权限等信息

### API密钥认证
- 适用于程序化访问
- 在请求头中包含：`X-API-Key: <api_key>`

---

## 版本控制

- 当前API版本：v1
- API版本通过URL路径指定：`/api/v1/`
- 向后兼容策略：维护至少两个主要版本

---

## 限流策略

- 匿名用户：100次/小时
- 认证用户：1000次/小时
- 高级用户：5000次/小时
- 企业用户：无限制

---

*本文档最后更新时间: 2024-08-08*
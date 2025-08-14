# Qlib-Web 项目架构设计文档

## 项目概述

### 1.1 项目定位
Qlib-Web 是基于 Microsoft Qlib 量化投资框架构建的 Web 应用平台，旨在为量化投资研究人员和交易者提供一站式的量化研发环境。通过直观的 Web 界面，用户可以便捷地进行因子开发、模型训练、策略回测、实盘部署等量化投资全流程操作。

### 1.2 核心价值
- **降低门槛**：通过图形化界面简化 Qlib 的使用复杂度
- **提升效率**：可视化的工作流程和自动化功能
- **增强协作**：多用户支持和团队协作功能
- **风险控制**：完善的风险管理和监控体系
- **易于扩展**：模块化设计支持功能扩展

### 1.3 目标用户
- 量化研究员和分析师
- 基金经理和投资顾问
- 金融科技公司开发者
- 高校量化金融教育工作者

---

## 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Qlib-Web Platform                    │
├─────────────────────────────────────────────────────────────┤
│                       前端层 (Frontend)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │  用户界面   │ │   数据可视化 │ │   交互组件   │ │  状态管理│ │
│  │    (UI)     │ │  (Charts)   │ │ (Components) │ │(Store) │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                       后端层 (Backend)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │  Web API    │ │   业务逻辑   │ │   数据访问   │ │  任务队列│ │
│  │ (FastAPI)   │ │  (Services) │ │    (ORM)    │ │(Celery)│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Qlib 集成层                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │  数据管理   │ │   模型训练   │ │   策略回测   │ │  因子计算│ │
│  │(Data Mgmt)  │ │ (Training)  │ │ (Backtest)  │ │(Factor)│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                       数据层 (Data)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │  业务数据库  │ │   Qlib数据   │ │   缓存系统   │ │  文件存储│ │
│  │(PostgreSQL) │ │  (Provider) │ │   (Redis)   │ │(Local) │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块架构

#### 2.2.1 前端架构 (Vue 3 + TypeScript)
```
frontend/
├── src/
│   ├── components/        # 组件库
│   │   ├── charts/       # 图表组件
│   │   ├── forms/        # 表单组件
│   │   ├── layout/       # 布局组件
│   │   └── business/     # 业务组件
│   ├── views/            # 页面视图
│   │   ├── Dashboard.vue
│   │   ├── FactorDevelopment.vue
│   │   ├── ModelTraining.vue
│   │   └── StrategyBacktest.vue
│   ├── stores/           # 状态管理 (Pinia)
│   │   ├── auth.ts
│   │   ├── experiment.ts
│   │   └── factors.ts
│   ├── api/              # API 接口
│   ├── utils/            # 工具函数
│   └── types/            # TypeScript 类型定义
```

#### 2.2.2 后端架构 (FastAPI + Python)
```
backend/
├── app/
│   ├── api/              # API 路由
│   │   └── v1/
│   │       ├── experiments.py
│   │       ├── qlib_data_service.py
│   │       └── qlib_model_service.py
│   ├── core/             # 核心配置
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/           # 数据模型
│   ├── schemas/          # API 模式
│   ├── services/         # 业务服务
│   ├── utils/            # 工具模块
│   │   └── qlib_manager.py
│   └── tasks/            # 异步任务
```

---

## 技术栈

### 3.1 前端技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue.js | 3.4+ | 前端框架 |
| TypeScript | 5.3+ | 类型安全 |
| Vite | 5.0+ | 构建工具 |
| Element Plus | 2.8+ | UI 组件库 |
| ECharts | 5.4+ | 数据可视化 |
| Pinia | 2.1+ | 状态管理 |
| Vue Router | 4.2+ | 路由管理 |
| Axios | 1.6+ | HTTP 客户端 |

### 3.2 后端技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 开发语言 |
| FastAPI | 0.104+ | Web 框架 |
| Qlib | Latest | 量化框架 |
| SQLAlchemy | 2.0+ | ORM 框架 |
| PostgreSQL | 13+ | 主数据库 |
| Redis | 7.0+ | 缓存和队列 |
| Celery | 5.3+ | 异步任务 |
| Uvicorn | 0.24+ | ASGI 服务器 |

### 3.3 数据科学栈
| 技术 | 用途 |
|------|------|
| Pandas | 数据处理 |
| NumPy | 数值计算 |
| Scikit-learn | 机器学习 |
| LightGBM | 梯度提升 |
| XGBoost | 梯度提升 |

---

## 核心功能模块

### 4.1 AI 因子助手模块

#### 功能概述
通过 AI 对话方式帮助用户生成量化因子表达式，并提供因子解读和验证功能。

#### 核心特性
- **自然语言交互**：用户用自然语言描述投资想法
- **智能因子生成**：AI 自动转换为 Qlib 因子表达式
- **因子解读**：提供因子的技术解释和投资逻辑说明
- **语法验证**：实时检查因子表达式的语法正确性
- **因子库管理**：统一管理用户创建的因子表达式

#### 技术实现
```python
# AI 因子生成服务
class AIFactorService:
    def __init__(self):
        self.ai_client = OpenAIClient()  # 或其他 AI 服务
        
    async def generate_factor(self, user_prompt: str) -> FactorExpression:
        """根据用户描述生成因子表达式"""
        system_prompt = """
        你是一个量化投资专家，帮助用户将投资想法转换为 Qlib 因子表达式。
        请根据用户的描述生成对应的因子表达式。
        """
        
        response = await self.ai_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return self.parse_ai_response(response)
```

### 4.2 模型训练模块

#### 功能概述
提供可视化的模型训练配置界面，支持多种机器学习模型，实时监控训练进度。

#### 支持的模型
- **树模型**：LightGBM、XGBoost、CatBoost
- **深度学习**：LSTM、GRU、Transformer
- **线性模型**：LinearRegression、Ridge、Lasso

#### 训练流程
1. **数据配置**：选择股票池、时间范围、特征字段
2. **模型选择**：选择算法类型和参数配置
3. **训练执行**：异步执行训练任务，实时显示进度
4. **结果评估**：展示训练指标和特征重要性

#### 技术实现
```python
# 模型训练服务
class ModelTrainingService:
    def __init__(self):
        self.qlib_manager = QlibManager()
        
    async def train_model(self, config: TrainingConfig) -> TrainingResult:
        """执行模型训练"""
        # 准备数据集
        dataset = self.prepare_dataset(config.data_config)
        
        # 创建模型实例
        model = self.create_model(config.model_config)
        
        # 执行训练
        with MLflowTracker() as tracker:
            trained_model = model.fit(dataset)
            metrics = self.evaluate_model(trained_model, dataset)
            
            # 保存模型和元数据
            model_path = self.save_model(trained_model, config)
            tracker.log_metrics(metrics)
            
        return TrainingResult(
            model_path=model_path,
            metrics=metrics,
            config=config
        )
```

### 4.3 策略回测模块

#### 功能概述
基于训练好的模型执行投资策略回测，支持多种策略类型和风险控制机制。

#### 支持的策略
- **TopK 策略**：选择预测收益最高的 K 只股票
- **多空策略**：同时做多和做空
- **风险平价**：基于风险预算的资产配置

#### 回测功能
- **交易成本**：支持复杂的交易成本模型
- **风险控制**：止损、止盈、仓位控制
- **基准对比**：与市场指数的对比分析
- **归因分析**：收益来源分析

#### 技术实现
```python
# 策略回测服务
class BacktestService:
    def __init__(self):
        self.qlib_manager = QlibManager()
        
    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """执行策略回测"""
        # 加载模型
        model = self.load_model(config.model_id)
        
        # 配置策略
        strategy = TopkDropoutStrategy(
            model=model,
            topk=config.strategy_params.topk,
            n_drop=config.strategy_params.n_drop
        )
        
        # 执行回测
        portfolio_metric, indicator = backtest_daily(
            executor=config.executor_config,
            strategy=strategy,
            **config.backtest_params
        )
        
        return self.process_backtest_result(portfolio_metric, indicator)
```

### 4.4 结果分析模块

#### 功能概述
对回测结果进行深度分析，提供多维度的性能评估和可视化展示。

#### 分析维度
- **收益分析**：累计收益、年化收益、月度收益分布
- **风险分析**：最大回撤、波动率、VaR/CVaR
- **归因分析**：行业归因、因子归因、时间归因
- **交易分析**：换手率、交易成本、胜率分析

#### 可视化图表
- 净值曲线图
- 收益分布直方图
- 回撤分析图
- 行业配置饼图
- 因子贡献雷达图

### 4.5 策略部署模块

#### 功能概述
将回测验证的策略部署到实盘交易环境，支持模拟交易和真实交易。

#### 部署模式
- **模拟交易**：纸面交易，无实际资金风险
- **实盘交易**：连接券商接口进行真实交易
- **信号推送**：仅推送交易信号，不直接执行

#### 风险管理
- **仓位控制**：总仓位和单股仓位限制
- **止损机制**：自动止损和手动干预
- **实时监控**：7x24小时策略运行监控
- **异常告警**：系统异常和风险预警

---

## API 设计

### 5.1 API 架构设计

采用 RESTful API 设计风格，所有接口均以 `/api/v1` 为前缀，支持 JSON 格式数据交换。

#### 5.1.1 统一响应格式
```json
{
  "success": true,
  "data": {
    // 具体数据内容
  },
  "message": "操作成功",
  "error_code": null,
  "request_id": "uuid-string"
}
```

#### 5.1.2 错误处理
```json
{
  "success": false,
  "data": null,
  "message": "具体错误信息",
  "error_code": "VALIDATION_ERROR",
  "request_id": "uuid-string",
  "details": {
    "field": "参数名",
    "reason": "错误原因"
  }
}
```

### 5.2 核心 API 接口

#### 5.2.1 因子管理 API
```python
# 生成因子表达式
POST /api/v1/factors/generate
{
  "prompt": "用户的自然语言描述",
  "context": "额外上下文信息"
}

# 验证因子表达式
POST /api/v1/factors/validate
{
  "expression": "($close / Ref($close, 20)) - 1",
  "test_data": {
    "instruments": ["000001.XSHE"],
    "start_time": "2023-01-01",
    "end_time": "2023-12-31"
  }
}

# 保存因子到库
POST /api/v1/factors/save
{
  "name": "20日动量因子",
  "expression": "($close / Ref($close, 20)) - 1",
  "description": "计算过去20个交易日的累计收益率",
  "category": "momentum"
}

# 获取因子库列表
GET /api/v1/factors/library?category=momentum&page=1&size=20
```

#### 5.2.2 模型训练 API
```python
# 启动模型训练
POST /api/v1/models/train
{
  "name": "LightGBM动量策略",
  "model_type": "lightgbm",
  "model_params": {
    "n_estimators": 100,
    "learning_rate": 0.1,
    "max_depth": 6
  },
  "data_config": {
    "stock_pool": "csi300",
    "start_time": "2020-01-01",
    "end_time": "2023-12-31",
    "features": ["factor1", "factor2", "factor3"]
  },
  "segments": {
    "train": ["2020-01-01", "2021-12-31"],
    "valid": ["2022-01-01", "2022-12-31"],
    "test": ["2023-01-01", "2023-12-31"]
  }
}

# 获取训练状态
GET /api/v1/models/train/{task_id}/status

# 获取模型列表
GET /api/v1/models?status=completed&model_type=lightgbm

# 模型性能对比
POST /api/v1/models/compare
{
  "model_ids": ["model_1", "model_2"],
  "metrics": ["accuracy", "ic", "rank_ic"]
}
```

#### 5.2.3 策略回测 API
```python
# 启动回测
POST /api/v1/backtest/start
{
  "name": "TopK策略回测",
  "model_id": "model_123",
  "strategy_config": {
    "type": "TopkDropoutStrategy",
    "params": {
      "topk": 20,
      "n_drop": 5
    }
  },
  "backtest_config": {
    "start_time": "2023-01-01",
    "end_time": "2023-12-31",
    "initial_capital": 1000000,
    "benchmark": "SH000300",
    "trade_cost": 0.0015
  }
}

# 获取回测进度
GET /api/v1/backtest/{task_id}/progress

# 获取回测结果
GET /api/v1/backtest/{task_id}/result

# 回测结果分析
GET /api/v1/backtest/{task_id}/analysis?type=performance
```

#### 5.2.4 策略部署 API
```python
# 创建策略部署
POST /api/v1/deployment/create
{
  "strategy_id": "strategy_123",
  "deployment_config": {
    "mode": "paper_trading",  // paper_trading | live_trading
    "initial_capital": 100000,
    "risk_limits": {
      "max_position_ratio": 0.1,
      "daily_loss_limit": 0.05
    }
  }
}

# 启动策略
POST /api/v1/deployment/{deploy_id}/start

# 停止策略
POST /api/v1/deployment/{deploy_id}/stop

# 获取策略状态
GET /api/v1/deployment/{deploy_id}/status

# 获取实时持仓
GET /api/v1/deployment/{deploy_id}/positions

# 获取交易记录
GET /api/v1/deployment/{deploy_id}/trades?start_date=2024-01-01
```

---

## 数据管理

### 6.1 数据架构

#### 6.1.1 业务数据库 (PostgreSQL)
存储应用业务数据，包括用户信息、实验配置、模型元数据等。

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实验表
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型表
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    experiment_id UUID REFERENCES experiments(id),
    name VARCHAR(200) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_path VARCHAR(500),
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 因子表
CREATE TABLE factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    expression TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50),
    validation_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 6.1.2 Qlib 数据存储
使用 Qlib 标准数据格式存储金融市场数据。

```
~/.qlib/qlib_data/cn_data/
├── calendars/           # 交易日历
├── instruments/         # 股票列表
├── features/            # 特征数据
│   ├── sh000001/       # 股票代码目录
│   │   ├── open.day    # 开盘价
│   │   ├── close.day   # 收盘价
│   │   ├── high.day    # 最高价
│   │   ├── low.day     # 最低价
│   │   └── volume.day  # 成交量
│   └── ...
└── factors/            # 因子数据
```

#### 6.1.3 缓存系统 (Redis)
用于缓存频繁访问的数据和会话管理。

```python
# 缓存策略
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
    def cache_market_data(self, key: str, data: pd.DataFrame, ttl: int = 3600):
        """缓存市场数据"""
        serialized_data = pickle.dumps(data)
        self.redis_client.setex(key, ttl, serialized_data)
        
    def get_cached_data(self, key: str) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        cached_data = self.redis_client.get(key)
        if cached_data:
            return pickle.loads(cached_data)
        return None
```

### 6.2 数据更新机制

#### 6.2.1 增量数据更新
```python
class DataUpdateService:
    def __init__(self):
        self.data_provider = DataProvider()
        
    async def update_daily_data(self):
        """每日数据更新"""
        # 获取最新交易日
        latest_date = self.get_latest_trading_date()
        
        # 更新股票基础数据
        await self.update_stock_data(latest_date)
        
        # 更新指数数据
        await self.update_index_data(latest_date)
        
        # 更新基本面数据
        await self.update_fundamental_data(latest_date)
        
        # 清理缓存
        self.clear_related_cache()
```

---

## 部署和运维

### 7.1 Docker 容器化部署

#### 7.1.1 多容器架构
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/qlib_web
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - qlib_data:/root/.qlib

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=qlib_web
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/qlib_web
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - qlib_data:/root/.qlib

volumes:
  postgres_data:
  redis_data:
  qlib_data:
```

#### 7.1.2 Kubernetes 部署
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qlib-web-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: qlib-web-backend
  template:
    metadata:
      labels:
        app: qlib-web-backend
    spec:
      containers:
      - name: backend
        image: qlib-web-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: qlib-web-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### 7.2 监控和日志

#### 7.2.1 性能监控
```python
# APM 监控服务
class APMService:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        
    async def collect_metrics(self):
        """收集系统指标"""
        metrics = {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'active_connections': self.get_active_connections(),
            'request_rate': self.get_request_rate(),
            'error_rate': self.get_error_rate()
        }
        
        await self.metrics_collector.send_metrics(metrics)
```

#### 7.2.2 日志管理
```python
# 日志配置
import logging
from loguru import logger

class LogConfig:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """配置日志"""
        logger.add(
            "logs/qlib_web_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
        
        # 错误日志单独记录
        logger.add(
            "logs/error_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="60 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
```

---

## 安全设计

### 8.1 认证和授权

#### 8.1.1 JWT Token 认证
```python
# JWT 认证服务
class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        
    def create_access_token(self, user_id: str, expires_delta: timedelta = None):
        """创建访问令牌"""
        to_encode = {"sub": user_id}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
        
    def verify_token(self, token: str):
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            return user_id
        except JWTError:
            raise credentials_exception
```

#### 8.1.2 权限控制
```python
# 权限装饰器
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = get_current_user()
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=403,
                    detail="权限不足"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.delete("/experiments/{experiment_id}")
@require_permission("experiment:delete")
async def delete_experiment(experiment_id: str):
    # 删除实验逻辑
    pass
```

### 8.2 数据安全

#### 8.2.1 数据加密
```python
# 敏感数据加密
class DataEncryption:
    def __init__(self):
        self.cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        
    def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感数据"""
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()
        
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """解密敏感数据"""
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
```

#### 8.2.2 API 安全防护
```python
# 安全中间件
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # 添加安全头
            headers = dict(scope.get("headers", []))
            
            # CORS 检查
            origin = headers.get(b"origin")
            if origin and not self.is_allowed_origin(origin.decode()):
                await self.send_cors_error(send)
                return
                
            # 请求频率限制
            client_ip = self.get_client_ip(scope)
            if await self.is_rate_limited(client_ip):
                await self.send_rate_limit_error(send)
                return
                
        await self.app(scope, receive, send)
```

---

## 开发指南

### 9.1 环境搭建

#### 9.1.1 开发环境要求
- Python 3.8+
- Node.js 18+
- PostgreSQL 13+
- Redis 7+
- Docker (可选)

#### 9.1.2 快速启动
```bash
# 1. 克隆项目
git clone https://github.com/your-org/qlib-web.git
cd qlib-web

# 2. 后端环境搭建
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 前端环境搭建
cd ../frontend
npm install

# 4. 数据库初始化
cd ../backend
alembic upgrade head

# 5. 启动服务
# 后端
uvicorn app.main:app --reload

# 前端 (新终端)
cd frontend
npm run dev
```

### 9.2 开发规范

#### 9.2.1 代码风格
```python
# Python 代码风格 (遵循 PEP 8)
# 使用 black 格式化代码
black --line-length 88 app/

# 使用 isort 排序导入
isort app/

# 使用 flake8 检查代码质量
flake8 app/
```

```typescript
// TypeScript 代码风格
// 使用 Prettier 格式化
prettier --write src/

// 使用 ESLint 检查代码质量
eslint src/ --ext .vue,.js,.ts
```

#### 9.2.2 Git 提交规范
```bash
# 提交信息格式
<type>(<scope>): <subject>

# 类型说明
feat: 新功能
fix: 修复
docs: 文档
style: 格式
refactor: 重构
test: 测试
chore: 构建过程或辅助工具的变动

# 示例
feat(factor): 添加 AI 因子生成功能
fix(backtest): 修复回测结果计算错误
docs(api): 更新 API 文档
```

### 9.3 测试指南

#### 9.3.1 后端测试
```python
# 使用 pytest 进行单元测试
# tests/test_factor_service.py
import pytest
from app.services.factor_service import FactorService

class TestFactorService:
    @pytest.fixture
    def factor_service(self):
        return FactorService()
        
    async def test_generate_factor_expression(self, factor_service):
        """测试因子表达式生成"""
        prompt = "20日动量因子"
        result = await factor_service.generate_expression(prompt)
        
        assert result.expression is not None
        assert "Ref($close, 20)" in result.expression
        assert result.validity.is_valid == True

# 运行测试
pytest tests/ -v --cov=app
```

#### 9.3.2 前端测试
```typescript
// 使用 Vitest 进行单元测试
// tests/components/FactorEditor.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import FactorEditor from '@/components/FactorEditor.vue'

describe('FactorEditor', () => {
  it('应该正确渲染因子编辑器', () => {
    const wrapper = mount(FactorEditor)
    expect(wrapper.find('.factor-editor').exists()).toBe(true)
  })
  
  it('应该验证因子表达式', async () => {
    const wrapper = mount(FactorEditor)
    const input = wrapper.find('input[type="text"]')
    
    await input.setValue('($close / Ref($close, 20)) - 1')
    await input.trigger('blur')
    
    expect(wrapper.vm.isValid).toBe(true)
  })
})

// 运行测试
npm run test
```

---

## 扩展性设计

### 10.1 插件架构

#### 10.1.1 模型插件接口
```python
from abc import ABC, abstractmethod

class ModelPlugin(ABC):
    """模型插件基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取模型名称"""
        pass
        
    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        pass
        
    @abstractmethod
    def create_model(self, params: Dict[str, Any]):
        """创建模型实例"""
        pass
        
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数有效性"""
        pass

# 自定义模型插件示例
class CustomLSTMPlugin(ModelPlugin):
    def get_name(self) -> str:
        return "CustomLSTM"
        
    def get_default_params(self) -> Dict[str, Any]:
        return {
            "hidden_size": 128,
            "num_layers": 3,
            "dropout": 0.2
        }
        
    def create_model(self, params: Dict[str, Any]):
        return CustomLSTMModel(**params)
```

#### 10.1.2 策略插件接口
```python
class StrategyPlugin(ABC):
    """策略插件基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取策略名称"""
        pass
        
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        pass
        
    @abstractmethod
    def create_strategy(self, config: Dict[str, Any]):
        """创建策略实例"""
        pass
```

### 10.2 微服务化扩展

#### 10.2.1 服务拆分设计
```
Qlib-Web Platform
├── User Service          # 用户管理服务
├── Factor Service        # 因子服务
├── Model Service         # 模型服务
├── Backtest Service      # 回测服务
├── Deployment Service    # 部署服务
├── Data Service          # 数据服务
└── Notification Service  # 通知服务
```

#### 10.2.2 服务间通信
```python
# 使用 gRPC 进行服务间通信
# factor_service.proto
syntax = "proto3";

service FactorService {
    rpc GenerateFactor(GenerateFactorRequest) returns (GenerateFactorResponse);
    rpc ValidateFactor(ValidateFactorRequest) returns (ValidateFactorResponse);
}

message GenerateFactorRequest {
    string prompt = 1;
    string user_id = 2;
}

message GenerateFactorResponse {
    string expression = 1;
    string description = 2;
    bool is_valid = 3;
}
```

---

## 性能优化

### 10.1 数据库优化

#### 10.1.1 索引策略
```sql
-- 为常用查询创建索引
CREATE INDEX idx_experiments_user_id_status ON experiments(user_id, status);
CREATE INDEX idx_experiments_created_at ON experiments(created_at DESC);
CREATE INDEX idx_models_experiment_id ON models(experiment_id);
CREATE INDEX idx_factors_user_id_category ON factors(user_id, category);

-- 部分索引优化
CREATE INDEX idx_active_experiments ON experiments(user_id, updated_at) 
WHERE status IN ('running', 'pending');
```

#### 10.1.2 查询优化
```python
# 使用数据库连接池
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 批量查询优化
class ExperimentRepository:
    async def get_experiments_with_models(self, user_id: str):
        """一次查询获取实验和关联模型"""
        query = (
            select(Experiment, Model)
            .join(Model, Experiment.id == Model.experiment_id, isouter=True)
            .filter(Experiment.user_id == user_id)
            .options(selectinload(Experiment.models))
        )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()
```

### 10.2 前端性能优化

#### 10.2.1 代码分割和懒加载
```typescript
// 路由懒加载
const routes = [
  {
    path: '/dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/factors',
    component: () => import('@/views/FactorDevelopment.vue')
  },
  {
    path: '/training',
    component: () => import('@/views/ModelTraining.vue')
  }
]

// 组件懒加载
const AsyncChart = defineAsyncComponent(() => import('@/components/Chart.vue'))
```

#### 10.2.2 虚拟滚动优化
```vue
<!-- 大数据量表格优化 -->
<template>
  <VirtualScrollTable
    :items="experiments"
    :item-height="60"
    :visible-range="10"
    @scroll-bottom="loadMore"
  >
    <template #item="{ item }">
      <ExperimentRow :experiment="item" />
    </template>
  </VirtualScrollTable>
</template>
```

---

## 项目治理

### 11.1 版本发布策略

#### 11.1.1 语义化版本控制
```
版本格式：主版本号.次版本号.修订号

主版本号：不兼容的 API 修改
次版本号：向下兼容的功能性新增
修订号：向下兼容的问题修正

示例：
v1.0.0 - 首个稳定版本
v1.1.0 - 新增 AI 因子助手功能
v1.1.1 - 修复回测计算bug
v2.0.0 - 重构 API，不向下兼容
```

#### 11.1.2 发布流程
```bash
# 1. 创建发布分支
git checkout -b release/v1.2.0

# 2. 更新版本号
# package.json, __init__.py 等

# 3. 运行测试
npm run test
pytest

# 4. 构建文档
npm run build:docs

# 5. 创建发布 PR
# 经过 Code Review 后合并

# 6. 创建 Git Tag
git tag v1.2.0
git push origin v1.2.0

# 7. 自动部署到生产环境
```

### 11.2 文档维护

#### 11.2.1 文档结构
```
docs/
├── README.md                    # 项目概述
├── ARCHITECTURE.md              # 架构设计文档
├── API.md                       # API 文档
├── DEPLOYMENT.md                # 部署文档
├── DEVELOPMENT.md               # 开发文档
├── CHANGELOG.md                 # 变更日志
├── user-guide/                  # 用户指南
│   ├── getting-started.md
│   ├── factor-development.md
│   └── strategy-backtest.md
└── developer-guide/             # 开发者指南
    ├── setup.md
    ├── testing.md
    └── contribution.md
```

#### 11.2.2 API 文档自动生成
```python
# 使用 FastAPI 自动生成 OpenAPI 文档
app = FastAPI(
    title="Qlib-Web API",
    description="量化投资 Web 平台 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加详细的 API 文档
@app.post("/api/v1/factors/generate", 
    summary="生成因子表达式",
    description="使用 AI 根据自然语言描述生成量化因子表达式",
    response_model=FactorGenerationResponse,
    tags=["因子管理"])
async def generate_factor(request: FactorGenerationRequest):
    """
    生成因子表达式
    
    Args:
        request: 包含用户描述的请求对象
        
    Returns:
        生成的因子表达式和相关信息
        
    Raises:
        HTTPException: 当 AI 服务不可用时
    """
    pass
```

---

## 总结

Qlib-Web 项目通过现代化的 Web 技术栈和模块化的架构设计，为量化投资研究提供了一个功能完善、易于使用的平台。项目的核心优势包括：

1. **完整的工作流程覆盖**：从因子开发到策略部署的全链路支持
2. **先进的技术架构**：基于 Vue 3 + FastAPI 的现代化架构
3. **深度的 Qlib 集成**：充分利用 Qlib 的量化投资能力
4. **丰富的可视化**：直观的图表和分析展示
5. **扩展性设计**：支持插件化和微服务化扩展
6. **完善的安全机制**：多层次的安全防护措施

通过持续的迭代开发和社区贡献，Qlib-Web 将成为量化投资领域的重要工具平台，帮助更多的投资者和研究者享受到量化投资的便利和价值。

---

*文档版本：v1.0*  
*最后更新：2025-08-14*  
*编写目的：为 Qlib-Web 项目的设计和开发提供全面的技术指导*
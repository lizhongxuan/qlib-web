# Qlib Web Console 后端

基于 FastAPI + Qlib 构建的量化投资策略研究平台后端API。

## 功能特性

- 🚀 **高性能API** - 基于FastAPI异步框架
- 📊 **Qlib集成** - 完整的量化投资工具链
- 🔄 **异步任务** - Celery后台任务处理
- 📈 **实验管理** - 完整的实验生命周期管理
- 📊 **数据可视化** - 丰富的分析结果接口
- 🛡️ **类型安全** - 完整的Pydantic数据验证

## 技术栈

- **框架**: FastAPI + SQLAlchemy + Alembic
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **任务队列**: Celery
- **量化框架**: Qlib
- **数据处理**: Pandas + NumPy
- **日志**: Loguru

## 项目结构

```
backend/
├── app/
│   ├── api/v1/         # API路由
│   │   └── endpoints/  # 具体端点
│   ├── core/           # 核心配置
│   ├── models/         # 数据库模型
│   ├── schemas/        # Pydantic模式
│   ├── services/       # 业务逻辑层
│   ├── utils/          # 工具函数
│   └── main.py         # 应用入口
├── tests/              # 测试文件
├── requirements.txt    # 依赖列表
└── run.py             # 启动脚本
```

## 快速开始

### 环境要求

- Python 3.8+
- Redis (可选，开发环境)
- PostgreSQL (生产环境)

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 环境配置

复制环境配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的环境变量。

### 初始化数据库

```bash
# 初始化数据库（首次运行）
python -c "from app.core.database import init_db; init_db()"
```

### 启动服务

```bash
# 开发模式
python run.py

# 或者使用uvicorn直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 http://localhost:8000 启动。

### 访问文档

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## API 接口

### 实验管理

- `POST /api/v1/experiments` - 创建实验
- `GET /api/v1/experiments` - 获取实验列表
- `GET /api/v1/experiments/{id}` - 获取实验详情
- `PUT /api/v1/experiments/{id}` - 更新实验
- `DELETE /api/v1/experiments/{id}` - 删除实验

### 实验结果

- `GET /api/v1/experiments/{id}/performance` - 获取性能数据
- `GET /api/v1/experiments/{id}/positions` - 获取持仓数据
- `GET /api/v1/experiments/{id}/logs` - 获取执行日志

### 仪表盘

- `GET /api/v1/dashboard/summary` - 获取统计摘要
- `GET /api/v1/dashboard/recent` - 获取最近实验
- `GET /api/v1/dashboard/stats` - 获取详细统计

### 配置管理

- `GET /api/v1/config/stock-pools` - 获取股票池列表
- `GET /api/v1/config/models` - 获取模型列表
- `GET /api/v1/config/strategies` - 获取策略列表
- `GET /api/v1/config/model-params/{model}` - 获取模型参数
- `POST /api/v1/config/validate` - 验证配置

## 开发指南

### 代码规范

项目使用以下工具进行代码质量控制：

- **Black**: 代码格式化
- **isort**: 导入排序
- **Flake8**: 代码检查

```bash
# 格式化代码
black app/
isort app/

# 检查代码
flake8 app/
```

### 测试

```bash
# 运行测试
pytest

# 测试覆盖率
pytest --cov=app --cov-report=html
```

### 添加新的API端点

1. 在 `app/schemas/` 中定义请求/响应模式
2. 在 `app/services/` 中实现业务逻辑
3. 在 `app/api/v1/endpoints/` 中创建路由
4. 在 `app/api/v1/api.py` 中注册路由

### 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 创建迁移
alembic revision --autogenerate -m "描述信息"

# 应用迁移
alembic upgrade head
```

## 生产部署

### Docker部署

```bash
# 构建镜像
docker build -t qlib-web-backend .

# 运行容器
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@localhost/qlib_web \
  -e REDIS_URL=redis://localhost:6379/0 \
  qlib-web-backend
```

### 环境变量配置

生产环境需要配置以下环境变量：

- `DATABASE_URL`: 数据库连接URL
- `REDIS_URL`: Redis连接URL
- `SECRET_KEY`: JWT密钥
- `QLIB_DATA_PATH`: Qlib数据路径

### 性能优化

- 使用Gunicorn作为WSGI服务器
- 配置反向代理(Nginx)
- 启用数据库连接池
- 配置Redis缓存策略

## 监控和日志

### 日志配置

日志使用Loguru库，支持：

- 文件轮转
- 结构化日志
- 异步写入
- 自定义格式

### 监控指标

- API响应时间
- 错误率统计
- 实验成功率
- 系统资源使用

## 故障排除

### 常见问题

1. **Qlib初始化失败**
   - 检查数据路径配置
   - 确认Qlib数据已下载

2. **数据库连接错误**
   - 检查连接字符串
   - 确认数据库服务运行

3. **Redis连接失败**
   - 检查Redis服务状态
   - 验证连接配置

### 调试模式

启用调试模式以获取详细日志：

```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
python run.py
```

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License
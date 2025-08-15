# Qlib Web Console 后端本地部署文档

## 概述

本文档详细说明了如何在本地环境部署 Qlib Web Console 后端服务，使用 MySQL 作为数据库。

## 系统要求

### 基础环境
- **操作系统**: macOS / Linux / Windows
- **Python**: 3.8 及以上版本
- **MySQL**: 5.7 及以上版本
- **内存**: 建议 4GB 以上
- **磁盘空间**: 建议 2GB 以上

### 依赖服务
- **MySQL 服务器**: 端口 3306，密码 `lzx234258`
- **Redis 服务器**: 可选，端口 6379（缓存和任务队列）

## 快速部署

### 方法一：使用自动部署脚本（推荐）

1. **进入后端目录**
   ```bash
   cd /Users/zhongxuan/Desktop/demo3/qlib-web/backend
   ```

2. **运行部署脚本**
   ```bash
   ./deploy.sh
   ```

3. **启动服务**
   ```bash
   source venv/bin/activate
   python -m app.main
   ```

### 方法二：手动部署

#### 1. 环境准备

**检查Python版本**
```bash
python3 --version  # 确保是 3.8+
```

**检查MySQL服务**
```bash
mysql -u root -plzx234258 -e "SELECT 1;"
```

#### 2. 创建虚拟环境

```bash
cd /Users/zhongxuan/Desktop/demo3/qlib-web/backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 数据库配置

**创建MySQL数据库**
```bash
mysql -u root -plzx234258 < scripts/setup_mysql.sql
```

**初始化数据库表**
```bash
python -c "from app.core.database import init_db; init_db()"
```

#### 5. 创建必要目录

```bash
mkdir -p logs uploads results experiments backups
```

#### 6. 测试连接

```bash
python test_connection.py
```

#### 7. 启动服务

```bash
python -m app.main
```

## 应用入口

**主要入口文件**: `app/main.py`

该文件包含了完整的FastAPI应用程序配置、中间件设置、生命周期管理等。可以直接通过以下命令启动：

```bash
python -m app.main
```

**注意**: 已删除多余的 `run.py` 入口文件，统一使用 `app/main.py` 作为唯一启动入口。

## 配置说明

### 数据库配置

**连接字符串**
```
mysql+pymysql://root:lzx234258@localhost:3306/qlib_web?charset=utf8mb4
```

**配置参数**
- **主机**: localhost
- **端口**: 3306
- **用户**: root
- **密码**: lzx234258
- **数据库**: qlib_web
- **字符集**: utf8mb4

### 环境变量配置

主要配置文件：`.env`

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:lzx234258@localhost:3306/qlib_web?charset=utf8mb4

# API配置
SECRET_KEY=qlib-web-console-super-secret-key-for-jwt-tokens-2024-change-in-production
DEBUG=true

# 其他配置
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 服务访问

### API服务
- **主服务**: http://localhost:8000
- **API文档**: http://localhost:8000/api/v1/docs
- **ReDoc文档**: http://localhost:8000/api/v1/redoc
- **健康检查**: http://localhost:8000/health

### 监控面板
- **性能监控**: http://localhost:8000/apm/dashboard
- **错误监控**: http://localhost:8000/errors/dashboard
- **用户分析**: http://localhost:8000/analytics/dashboard

## 验证部署

### 1. 健康检查
```bash
curl http://localhost:8000/health
```

### 2. API文档访问
在浏览器中打开：http://localhost:8000/api/v1/docs

### 3. 数据库连接测试
```bash
python test_connection.py
```

## 目录结构

```
backend/
├── app/                    # 应用主目录
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据库模型
│   ├── schemas/           # Pydantic模式
│   ├── services/          # 业务逻辑
│   └── utils/             # 工具函数
├── logs/                  # 日志文件
├── uploads/               # 上传文件
├── results/               # 实验结果
├── experiments/           # 实验数据
├── backups/               # 备份文件
├── scripts/               # 部署脚本
│   └── setup_mysql.sql    # MySQL初始化脚本
├── venv/                  # 虚拟环境
├── .env                   # 环境变量
├── requirements.txt       # Python依赖
├── deploy.sh             # 部署脚本
└── test_connection.py    # 连接测试
```

## 常见问题

### 1. MySQL连接失败

**错误信息**: `Can't connect to MySQL server`

**解决方案**:
- 检查MySQL服务是否启动：`brew services start mysql` (macOS)
- 验证密码：`mysql -u root -plzx234258`
- 检查端口：确保3306端口未被占用

### 2. 依赖安装失败

**错误信息**: `ERROR: Failed building wheel for xxx`

**解决方案**:
```bash
# 更新构建工具
pip install --upgrade setuptools wheel

# 安装特定依赖
pip install PyMySQL==1.1.0
pip install aiomysql==0.2.0
```

### 3. 数据库编码问题

**错误信息**: `Incorrect string value`

**解决方案**:
- 确保数据库使用 utf8mb4 字符集
- 检查连接字符串包含 `charset=utf8mb4`

### 4. 端口占用

**错误信息**: `Address already in use`

**解决方案**:
```bash
# 查看占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
uvicorn app.main:app --port 8001
```

### 5. Qlib数据路径问题

**错误信息**: `Qlib data not found`

**解决方案**:
```bash
# 检查Qlib数据路径
ls ~/.qlib/qlib_data/cn_data

# 如果不存在，下载Qlib数据
python -c "import qlib; qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')"
```

## 开发调试

### 1. 调试模式
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python -m app.main
```

### 2. 热重载
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 数据库调试
```python
from app.core.database import engine
engine.echo = True  # 打印SQL语句
```

## 支持与反馈

如果遇到问题，请检查：
1. **日志文件**: `logs/app.log`
2. **错误监控**: http://localhost:8000/errors/dashboard
3. **系统状态**: http://localhost:8000/health

技术支持：请通过项目issues报告问题。

---

**部署完成！** 🎉

现在你可以访问 http://localhost:8000/api/v1/docs 查看API文档并开始使用 Qlib Web Console。
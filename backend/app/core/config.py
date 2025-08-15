from typing import Any, Dict, List, Optional, Union
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings, validator
    PYDANTIC_V2 = False
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "Qlib Web Console API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-very-secure-secret-key-here-this-is-a-very-long-secret-key-for-jwt"  # 应该通过环境变量设置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 前端URL配置
    FRONTEND_URL: str = "http://localhost:3000"
    
    # 邮件配置
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@qlib-web.com"
    SMTP_FROM_NAME: str = "Qlib Web Platform"
    
    if PYDANTIC_V2:
        @field_validator("SECRET_KEY")
        @classmethod
        def validate_secret_key(cls, v: str) -> str:
            if not v or len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters long")
            if v == "your-very-secure-secret-key-here":
                raise ValueError("Please change the default SECRET_KEY in production")
            return v
    else:
        @validator("SECRET_KEY", pre=True)
        def validate_secret_key(cls, v: str) -> str:
            if not v or len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters long")
            if v == "your-very-secure-secret-key-here":
                raise ValueError("Please change the default SECRET_KEY in production")
            return v
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:lzx234258@localhost:3306/qlib_web?charset=utf8mb4"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Qlib配置
    QLIB_DATA_PATH: str = "/Users/zhongxuan/.qlib/qlib_data/cn_data"
    QLIB_REGION: str = "cn"
    QLIB_PROVIDER_URI: str = "~/.qlib/qlib_data/cn_data"
    
    # 文件存储配置
    UPLOAD_PATH: str = "./uploads"
    RESULTS_PATH: str = "./results"
    EXPERIMENTS_PATH: str = "./experiments"
    BACKUP_PATH: str = "./backups"
    MAX_FILE_SIZE: str = "100MB"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:4173", 
        "http://127.0.0.1:4173",
        "http://localhost:9988",
        "http://127.0.0.1:9988"
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    if PYDANTIC_V2:
        @field_validator("ALLOWED_ORIGINS", mode="before")
        @classmethod
        def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            elif isinstance(v, (list, str)):
                return v
            raise ValueError(v)
    else:
        @validator("ALLOWED_ORIGINS", pre=True)
        def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            elif isinstance(v, (list, str)):
                return v
            raise ValueError(v)
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001
    
    if PYDANTIC_V2:
        model_config = {"env_file": ".env", "case_sensitive": True}
    else:
        class Config:
            env_file = ".env"
            case_sensitive = True


# 创建全局设置实例
settings = Settings()


# Qlib 相关配置
QLIB_CONFIG = {
    "stock_pools": [
        "CSI300", "CSI500", "CSI800", "CSI1000",
        "SSE50", "SZSE100", "ChiNext"
    ],
    "models": [
        "LightGBM", "XGBoost", "CatBoost", 
        "LSTM", "GRU", "Transformer",
        "Linear", "Ridge", "Lasso"
    ],
    "strategies": [
        "TopkDropoutStrategy", "SignalStrategy", 
        "WeightStrategyBase", "RollingStrategy"
    ],
    "model_params": {
        "LightGBM": {
            "n_estimators": {"type": "int", "min": 10, "max": 1000, "default": 100},
            "learning_rate": {"type": "float", "min": 0.01, "max": 1.0, "default": 0.1},
            "max_depth": {"type": "int", "min": 3, "max": 15, "default": 6},
            "num_leaves": {"type": "int", "min": 10, "max": 300, "default": 31}
        },
        "LSTM": {
            "hidden_size": {"type": "int", "min": 16, "max": 512, "default": 64},
            "num_layers": {"type": "int", "min": 1, "max": 10, "default": 2},
            "dropout": {"type": "float", "min": 0.0, "max": 0.5, "default": 0.1},
            "d_feat": {"type": "int", "min": 50, "max": 500, "default": 158}
        },
        "Linear": {
            "alpha": {"type": "float", "min": 0.0001, "max": 10.0, "default": 1.0},
            "fit_intercept": {"type": "bool", "default": True}
        }
    },
    "strategy_params": {
        "TopkDropoutStrategy": {
            "topk": {"type": "int", "min": 5, "max": 200, "default": 50},
            "n_drop": {"type": "int", "min": 1, "max": 50, "default": 5},
            "signal_config": {"type": "dict", "default": {}}
        },
        "SignalStrategy": {
            "signal": {"type": "str", "required": True}
        }
    }
}


# 数据库表前缀
TABLE_PREFIX = "qlib_"

# 任务状态枚举
class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


# API响应状态码
class ResponseStatus:
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
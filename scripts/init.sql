-- Qlib Web 数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 设置时区
SET timezone = 'UTC';

-- 创建序列（如果需要）
-- CREATE SEQUENCE IF NOT EXISTS experiment_seq START 1;
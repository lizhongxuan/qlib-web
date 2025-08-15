-- Qlib Web Console MySQL数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS qlib_web 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 切换到qlib_web数据库
USE qlib_web;

-- 显示成功信息
SELECT 'MySQL数据库创建成功!' as message;
SELECT 'Database qlib_web is ready for use' as status;

-- 显示数据库信息
SHOW DATABASES LIKE 'qlib_web';
SELECT DATABASE() as current_database;
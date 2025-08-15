#!/bin/bash
# Qlib Web Console 后端本地部署脚本

set -e  # 遇到错误立即退出

echo "🚀 开始部署 Qlib Web Console 后端..."

# 检查Python版本
echo "📋 检查Python版本..."
python3 --version || {
    echo "❌ 错误：需要Python 3.8及以上版本"
    exit 1
}

# 检查MySQL连接
echo "📋 检查MySQL连接..."
mysql -u root -plzx234258 -e "SELECT 1;" || {
    echo "❌ 错误：无法连接到MySQL，请检查MySQL服务是否启动以及密码是否正确"
    exit 1
}

# 创建虚拟环境
echo "🔧 创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "🔧 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装Python依赖包..."
pip install -r requirements.txt

# 创建数据库
echo "🗄️ 初始化MySQL数据库..."
mysql -u root -plzx234258 < scripts/setup_mysql.sql
echo "✅ 数据库初始化完成"

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs uploads results experiments backups
echo "✅ 目录创建完成"

# 初始化数据库表
echo "🗄️ 初始化数据库表..."
python -c "from app.core.database import init_db; init_db()" || {
    echo "❌ 数据库表初始化失败"
    exit 1
}
echo "✅ 数据库表初始化完成"

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 启动命令："
echo "   cd $(pwd)"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "🌐 访问地址："
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/api/v1/docs"
echo "   健康检查: http://localhost:8000/health"
echo ""
echo "📁 重要目录："
echo "   日志目录: $(pwd)/logs"
echo "   上传目录: $(pwd)/uploads"
echo "   结果目录: $(pwd)/results"
echo ""
#!/bin/bash

# Qlib Web 测试运行脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# 检查依赖
check_dependencies() {
    log_section "检查依赖"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    log_info "Python: $(python3 --version)"
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    log_info "Node.js: $(node --version)"
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    log_info "npm: $(npm --version)"
    
    # 检查Docker (可选)
    if command -v docker &> /dev/null; then
        log_info "Docker: $(docker --version)"
    else
        log_warn "Docker 未安装，跳过Docker相关测试"
    fi
}

# 设置测试环境
setup_test_env() {
    log_section "设置测试环境"
    
    # 创建测试环境变量文件
    if [ ! -f ".env.test" ]; then
        log_info "创建测试环境变量文件"
        cat > .env.test << EOF
SECRET_KEY=test-secret-key-for-testing-very-long-key-123456789
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/1
DEBUG=true
LOG_LEVEL=DEBUG
EOF
    fi
    
    # 设置环境变量
    export $(cat .env.test | grep -v '^#' | xargs)
}

# 运行后端测试
run_backend_tests() {
    log_section "运行后端测试"
    
    cd backend
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境"
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装后端依赖"
    pip install -r requirements.txt
    
    # 运行代码质量检查
    log_info "运行代码格式检查"
    black --check app/ || {
        log_warn "代码格式不符合规范，尝试自动修复..."
        black app/
    }
    
    log_info "运行导入排序检查"
    isort --check-only app/ || {
        log_warn "导入排序不符合规范，尝试自动修复..."
        isort app/
    }
    
    log_info "运行代码质量检查"
    flake8 app/ || {
        log_error "代码质量检查失败"
        cd ..
        return 1
    }
    
    # 运行类型检查
    if command -v mypy &> /dev/null; then
        log_info "运行类型检查"
        mypy app/ --ignore-missing-imports || {
            log_warn "类型检查发现问题"
        }
    fi
    
    # 运行测试
    log_info "运行单元测试"
    python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing || {
        log_error "单元测试失败"
        cd ..
        return 1
    }
    
    log_info "运行集成测试"
    python -m pytest tests/integration/ -v || {
        log_error "集成测试失败"
        cd ..
        return 1
    }
    
    # 生成覆盖率报告
    log_info "生成覆盖率报告"
    python -m pytest --cov=app --cov-report=html --cov-report=term-missing
    log_info "覆盖率报告已生成：htmlcov/index.html"
    
    cd ..
    log_info "后端测试完成"
}

# 运行前端测试
run_frontend_tests() {
    log_section "运行前端测试"
    
    cd frontend
    
    # 安装依赖
    log_info "安装前端依赖"
    npm ci
    
    # 运行代码质量检查
    log_info "运行ESLint检查"
    npm run lint || {
        log_error "ESLint检查失败"
        cd ..
        return 1
    }
    
    # 运行TypeScript类型检查
    log_info "运行TypeScript类型检查"
    npx vue-tsc --noEmit || {
        log_error "TypeScript类型检查失败"
        cd ..
        return 1
    }
    
    # 运行测试
    log_info "运行前端单元测试"
    npm run test:run || {
        log_error "前端测试失败"
        cd ..
        return 1
    }
    
    # 生成覆盖率报告
    log_info "生成前端覆盖率报告"
    npm run test:coverage
    log_info "覆盖率报告已生成：coverage/index.html"
    
    # 构建测试
    log_info "测试前端构建"
    npm run build || {
        log_error "前端构建失败"
        cd ..
        return 1
    }
    
    cd ..
    log_info "前端测试完成"
}

# 运行Docker测试
run_docker_tests() {
    if ! command -v docker &> /dev/null; then
        log_warn "跳过Docker测试 - Docker未安装"
        return 0
    fi
    
    log_section "运行Docker测试"
    
    # 构建镜像
    log_info "构建后端Docker镜像"
    docker build -t qlib-web-backend:test ./backend || {
        log_error "后端Docker镜像构建失败"
        return 1
    }
    
    log_info "构建前端Docker镜像"
    docker build -t qlib-web-frontend:test ./frontend || {
        log_error "前端Docker镜像构建失败"
        return 1
    }
    
    # 测试Docker Compose配置
    log_info "测试Docker Compose配置"
    docker-compose -f docker-compose.yml config || {
        log_error "Docker Compose配置验证失败"
        return 1
    }
    
    log_info "Docker测试完成"
}

# 清理测试环境
cleanup() {
    log_section "清理测试环境"
    
    # 删除临时文件
    rm -f test.db
    rm -f .env.test
    
    # 停止可能运行的Docker容器
    if command -v docker &> /dev/null; then
        docker-compose down --remove-orphans 2>/dev/null || true
    fi
    
    log_info "清理完成"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --backend-only    只运行后端测试"
    echo "  --frontend-only   只运行前端测试"
    echo "  --docker-only     只运行Docker测试"
    echo "  --no-docker       跳过Docker测试"
    echo "  --cleanup         清理测试环境后退出"
    echo "  -h, --help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                运行所有测试"
    echo "  $0 --backend-only 只运行后端测试"
    echo "  $0 --no-docker    运行除Docker外的所有测试"
}

# 主函数
main() {
    local run_backend=true
    local run_frontend=true
    local run_docker=true
    local cleanup_only=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                run_backend=true
                run_frontend=false
                run_docker=false
                shift
                ;;
            --frontend-only)
                run_backend=false
                run_frontend=true
                run_docker=false
                shift
                ;;
            --docker-only)
                run_backend=false
                run_frontend=false
                run_docker=true
                shift
                ;;
            --no-docker)
                run_docker=false
                shift
                ;;
            --cleanup)
                cleanup_only=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果只是清理，直接执行清理并退出
    if [ "$cleanup_only" = true ]; then
        cleanup
        exit 0
    fi
    
    # 设置错误处理
    trap cleanup EXIT
    
    log_info "开始运行Qlib Web测试套件"
    
    # 检查依赖
    check_dependencies
    
    # 设置测试环境
    setup_test_env
    
    # 记录开始时间
    start_time=$(date +%s)
    
    # 运行测试
    if [ "$run_backend" = true ]; then
        run_backend_tests
    fi
    
    if [ "$run_frontend" = true ]; then
        run_frontend_tests
    fi
    
    if [ "$run_docker" = true ]; then
        run_docker_tests
    fi
    
    # 计算总耗时
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    log_section "测试完成"
    log_info "总耗时: ${duration}秒"
    log_info "所有测试通过! ✅"
}

# 运行主函数
main "$@"
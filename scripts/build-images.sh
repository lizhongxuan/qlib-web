#!/bin/bash

# Docker镜像构建脚本
# 用于构建优化的生产环境镜像

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="qlib-web"
VERSION=${VERSION:-$(date +%Y%m%d-%H%M%S)}
REGISTRY=${REGISTRY:-""}
BUILD_ARGS=""
PLATFORM=${PLATFORM:-"linux/amd64,linux/arm64"}

# 打印帮助信息
show_help() {
    cat << EOF
Docker镜像构建脚本

用法: $0 [选项]

选项:
    -h, --help              显示帮助信息
    -v, --version VERSION   指定镜像版本 (默认: 时间戳)
    -r, --registry REGISTRY 指定镜像仓库地址
    -p, --platform PLATFORM 指定构建平台 (默认: linux/amd64,linux/arm64)
    -d, --dev               构建开发版本
    -c, --clean             清理构建缓存
    --no-cache              不使用构建缓存
    --push                  构建后推送到仓库

示例:
    $0 --version v1.0.0 --registry registry.example.com --push
    $0 --dev --no-cache
EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -d|--dev)
            DEV_MODE=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        --no-cache)
            BUILD_ARGS="--no-cache"
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 设置镜像名称
if [[ -n "$REGISTRY" ]]; then
    BACKEND_IMAGE="$REGISTRY/$PROJECT_NAME-backend:$VERSION"
    FRONTEND_IMAGE="$REGISTRY/$PROJECT_NAME-frontend:$VERSION"
    BACKEND_IMAGE_LATEST="$REGISTRY/$PROJECT_NAME-backend:latest"
    FRONTEND_IMAGE_LATEST="$REGISTRY/$PROJECT_NAME-frontend:latest"
else
    BACKEND_IMAGE="$PROJECT_NAME-backend:$VERSION"
    FRONTEND_IMAGE="$PROJECT_NAME-frontend:$VERSION"
    BACKEND_IMAGE_LATEST="$PROJECT_NAME-backend:latest"
    FRONTEND_IMAGE_LATEST="$PROJECT_NAME-frontend:latest"
fi

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}=== Docker镜像构建开始 ===${NC}"
echo "项目: $PROJECT_NAME"
echo "版本: $VERSION"
echo "平台: $PLATFORM"

# 清理构建缓存
if [[ "${CLEAN:-false}" == "true" ]]; then
    echo -e "${YELLOW}清理Docker构建缓存...${NC}"
    docker builder prune -f
    docker system prune -f
fi

# 确保buildx可用
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker Buildx不可用${NC}"
    exit 1
fi

# 创建并使用多平台构建器
if ! docker buildx inspect multiarch > /dev/null 2>&1; then
    echo -e "${YELLOW}创建多平台构建器...${NC}"
    docker buildx create --name multiarch --use
else
    docker buildx use multiarch
fi

# 构建后端镜像
echo -e "${GREEN}构建后端镜像...${NC}"
cd "$PROJECT_ROOT/backend"

DOCKERFILE="Dockerfile.optimized"
if [[ "${DEV_MODE:-false}" == "true" ]]; then
    DOCKERFILE="Dockerfile"
fi

docker buildx build \
    --platform "$PLATFORM" \
    --file "$DOCKERFILE" \
    --tag "$BACKEND_IMAGE" \
    --tag "$BACKEND_IMAGE_LATEST" \
    --build-arg VERSION="$VERSION" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --metadata-file /tmp/backend-metadata.json \
    $BUILD_ARGS \
    ${PUSH:+--push} \
    ${PUSH:+--provenance=true --sbom=true} \
    . || {
        echo -e "${RED}后端镜像构建失败${NC}"
        exit 1
    }

echo -e "${GREEN}后端镜像构建完成: $BACKEND_IMAGE${NC}"

# 构建前端镜像
echo -e "${GREEN}构建前端镜像...${NC}"
cd "$PROJECT_ROOT/frontend"

DOCKERFILE="Dockerfile.optimized"
if [[ "${DEV_MODE:-false}" == "true" ]]; then
    DOCKERFILE="Dockerfile"
fi

docker buildx build \
    --platform "$PLATFORM" \
    --file "$DOCKERFILE" \
    --tag "$FRONTEND_IMAGE" \
    --tag "$FRONTEND_IMAGE_LATEST" \
    --build-arg VERSION="$VERSION" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --metadata-file /tmp/frontend-metadata.json \
    $BUILD_ARGS \
    ${PUSH:+--push} \
    ${PUSH:+--provenance=true --sbom=true} \
    . || {
        echo -e "${RED}前端镜像构建失败${NC}"
        exit 1
    }

echo -e "${GREEN}前端镜像构建完成: $FRONTEND_IMAGE${NC}"

# 显示镜像信息
if [[ "${PUSH:-false}" != "true" ]]; then
    echo -e "${GREEN}=== 构建完成的镜像 ===${NC}"
    docker images | grep "$PROJECT_NAME"
    
    echo -e "${YELLOW}镜像大小对比:${NC}"
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$PROJECT_NAME"
fi

# 生成镜像安全扫描报告
if command -v trivy > /dev/null 2>&1; then
    echo -e "${GREEN}生成安全扫描报告...${NC}"
    mkdir -p "$PROJECT_ROOT/reports"
    
    trivy image --format json --output "$PROJECT_ROOT/reports/backend-security-scan.json" "$BACKEND_IMAGE" || true
    trivy image --format json --output "$PROJECT_ROOT/reports/frontend-security-scan.json" "$FRONTEND_IMAGE" || true
    
    echo -e "${GREEN}安全扫描报告已生成到 reports/ 目录${NC}"
fi

# 生成镜像清单
echo -e "${GREEN}生成镜像清单...${NC}"
cat > "$PROJECT_ROOT/image-manifest.json" << EOF
{
    "project": "$PROJECT_NAME",
    "version": "$VERSION",
    "build_date": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "platform": "$PLATFORM",
    "images": {
        "backend": "$BACKEND_IMAGE",
        "frontend": "$FRONTEND_IMAGE"
    },
    "registry": "${REGISTRY:-"local"}",
    "metadata": {
        "backend_size": "$(docker image inspect "$BACKEND_IMAGE" --format '{{.Size}}' 2>/dev/null || echo 'unknown')",
        "frontend_size": "$(docker image inspect "$FRONTEND_IMAGE" --format '{{.Size}}' 2>/dev/null || echo 'unknown')"
    }
}
EOF

echo -e "${GREEN}=== 构建完成 ===${NC}"
echo "镜像清单: $PROJECT_ROOT/image-manifest.json"

if [[ "${PUSH:-false}" == "true" ]]; then
    echo -e "${GREEN}镜像已推送到仓库: $REGISTRY${NC}"
else
    echo -e "${YELLOW}提示: 使用 --push 参数可将镜像推送到仓库${NC}"
fi
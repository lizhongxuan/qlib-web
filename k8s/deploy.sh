#!/bin/bash

# Kubernetes 部署脚本
# 用于部署 Qlib Web 应用到 Kubernetes 集群

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
NAMESPACE="qlib-web"
KUBECTL_TIMEOUT="300s"
DRY_RUN=false
SKIP_SECRETS=false

# 打印帮助信息
show_help() {
    cat << EOF
Kubernetes 部署脚本

用法: $0 [选项]

选项:
    -h, --help              显示帮助信息
    -n, --namespace NAME    指定命名空间 (默认: qlib-web)
    -d, --dry-run           执行模拟部署
    -s, --skip-secrets      跳过 Secrets 部署 (用于CI/CD)
    --timeout DURATION      设置kubectl超时时间 (默认: 300s)

示例:
    $0                      # 标准部署
    $0 --dry-run            # 模拟部署
    $0 --skip-secrets       # 跳过敏感信息部署
EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -s|--skip-secrets)
            SKIP_SECRETS=true
            shift
            ;;
        --timeout)
            KUBECTL_TIMEOUT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}=== Kubernetes 部署开始 ===${NC}"
echo "命名空间: $NAMESPACE"
echo "模拟运行: $DRY_RUN"
echo "跳过机密: $SKIP_SECRETS"

# 设置 kubectl 参数
KUBECTL_ARGS="--timeout=$KUBECTL_TIMEOUT"
if [[ "$DRY_RUN" == "true" ]]; then
    KUBECTL_ARGS="$KUBECTL_ARGS --dry-run=client -o yaml"
fi

# 检查 kubectl 可用性
if ! command -v kubectl > /dev/null 2>&1; then
    echo -e "${RED}错误: kubectl 未安装或不可用${NC}"
    exit 1
fi

# 检查集群连接
if ! kubectl cluster-info > /dev/null 2>&1; then
    echo -e "${RED}错误: 无法连接到 Kubernetes 集群${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Kubernetes 集群连接正常${NC}"

# 部署顺序定义
DEPLOY_ORDER=(
    "namespace.yaml"
    "persistent-volumes.yaml"
    "configmap.yaml"
)

# 如果不跳过secrets，添加到部署列表
if [[ "$SKIP_SECRETS" != "true" ]]; then
    DEPLOY_ORDER+=("secrets.yaml")
fi

# 继续添加其他资源
DEPLOY_ORDER+=(
    "postgres.yaml"
    "redis.yaml"
    "backend.yaml"
    "frontend.yaml"
    "nginx.yaml"
    "ingress.yaml"
    "monitoring.yaml"
)

# 部署函数
deploy_resource() {
    local resource_file="$1"
    local resource_path="$SCRIPT_DIR/$resource_file"
    
    if [[ ! -f "$resource_path" ]]; then
        echo -e "${YELLOW}警告: 文件 $resource_file 不存在，跳过${NC}"
        return 0
    fi
    
    echo -e "${GREEN}部署: $resource_file${NC}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        kubectl apply -f "$resource_path" $KUBECTL_ARGS
    else
        kubectl apply -f "$resource_path" $KUBECTL_ARGS
        
        # 等待部署完成（仅对特定资源）
        case "$resource_file" in
            "postgres.yaml")
                echo "等待 PostgreSQL 就绪..."
                kubectl wait --for=condition=ready pod -l component=postgres-primary -n "$NAMESPACE" --timeout=300s || true
                ;;
            "redis.yaml")
                echo "等待 Redis 就绪..."
                kubectl wait --for=condition=ready pod -l component=redis-primary -n "$NAMESPACE" --timeout=300s || true
                ;;
            "backend.yaml")
                echo "等待后端服务就绪..."
                kubectl wait --for=condition=available deployment/qlib-web-backend -n "$NAMESPACE" --timeout=300s || true
                ;;
            "frontend.yaml")
                echo "等待前端服务就绪..."
                kubectl wait --for=condition=available deployment/qlib-web-frontend -n "$NAMESPACE" --timeout=300s || true
                ;;
        esac
    fi
    
    echo -e "${GREEN}✓ $resource_file 部署完成${NC}"
}

# 执行部署
for resource in "${DEPLOY_ORDER[@]}"; do
    deploy_resource "$resource"
    sleep 2  # 短暂等待避免资源冲突
done

# 验证部署状态
if [[ "$DRY_RUN" != "true" ]]; then
    echo -e "${GREEN}=== 验证部署状态 ===${NC}"
    
    echo "检查命名空间资源:"
    kubectl get all -n "$NAMESPACE" -o wide
    
    echo -e "\n检查Pod状态:"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    echo -e "\n检查服务状态:"
    kubectl get services -n "$NAMESPACE" -o wide
    
    echo -e "\n检查存储卷状态:"
    kubectl get pvc -n "$NAMESPACE"
    
    echo -e "\n检查Ingress状态:"
    kubectl get ingress -n "$NAMESPACE" || echo "无Ingress资源"
    
    # 检查问题Pod
    PROBLEM_PODS=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    if [[ $PROBLEM_PODS -gt 0 ]]; then
        echo -e "${YELLOW}发现 $PROBLEM_PODS 个问题Pod:${NC}"
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running
        
        echo -e "${YELLOW}问题Pod详细信息:${NC}"
        kubectl describe pods -n "$NAMESPACE" --field-selector=status.phase!=Running
    fi
    
    # 显示访问信息
    echo -e "${GREEN}=== 应用访问信息 ===${NC}"
    
    # 获取外部访问地址
    EXTERNAL_IP=$(kubectl get service nginx-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [[ -n "$EXTERNAL_IP" ]]; then
        echo "外部访问地址: http://$EXTERNAL_IP"
    else
        echo "使用端口转发访问应用:"
        echo "  kubectl port-forward -n $NAMESPACE service/nginx-lb 8080:80"
        echo "  然后访问: http://localhost:8080"
    fi
    
    # 监控访问信息
    echo -e "\n监控系统访问:"
    echo "  Prometheus: kubectl port-forward -n $NAMESPACE service/prometheus 9090:9090"
    echo "  Grafana: kubectl port-forward -n $NAMESPACE service/grafana 3000:3000"
fi

echo -e "${GREEN}=== 部署完成 ===${NC}"

# 提供后续操作建议
cat << EOF

${YELLOW}后续操作建议:${NC}
1. 检查应用日志:
   kubectl logs -n $NAMESPACE -l app=qlib-web -f

2. 进入容器调试:
   kubectl exec -n $NAMESPACE -it deployment/qlib-web-backend -- /bin/bash

3. 查看配置:
   kubectl get configmap -n $NAMESPACE -o yaml

4. 更新应用:
   kubectl set image -n $NAMESPACE deployment/qlib-web-backend backend=qlib-web-backend:v1.1.0

5. 扩缩容:
   kubectl scale -n $NAMESPACE deployment/qlib-web-backend --replicas=5

6. 删除部署:
   kubectl delete namespace $NAMESPACE

${GREEN}祝您使用愉快！${NC}
EOF
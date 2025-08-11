#!/bin/bash

# Qlib Web 数据备份脚本

set -e

# 配置
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/tmp/qlib_backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api/v1}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 显示使用帮助
show_help() {
    cat << EOF
Qlib Web 备份工具

用法:
  $0 [选项] 命令

命令:
  create-full         创建完整备份
  create-experiment   创建实验备份 (需要指定 --experiment-id)
  list               列出所有备份
  restore            恢复备份 (需要指定 --backup-name)
  delete             删除备份 (需要指定 --backup-name)
  cleanup            清理过期备份

选项:
  --experiment-id ID  实验ID (用于 create-experiment)
  --backup-name NAME  备份名称 (用于 restore/delete)
  --description DESC  备份描述 (用于 create-*)
  --retention-days N  备份保留天数，默认30天 (用于 cleanup)
  -h, --help         显示此帮助信息

示例:
  $0 create-full --description "定期完整备份"
  $0 create-experiment --experiment-id exp-123 --description "重要实验备份"
  $0 list
  $0 restore --backup-name full_backup_20240101_120000
  $0 cleanup --retention-days 7
EOF
}

# 解析命令行参数
COMMAND=""
EXPERIMENT_ID=""
BACKUP_NAME=""
DESCRIPTION=""

while [[ \$# -gt 0 ]]; do
    case \$1 in
        create-full|create-experiment|list|restore|delete|cleanup)
            COMMAND=\$1
            shift
            ;;
        --experiment-id)
            EXPERIMENT_ID="\$2"
            shift 2
            ;;
        --backup-name)
            BACKUP_NAME="\$2"
            shift 2
            ;;
        --description)
            DESCRIPTION="\$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="\$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知选项: \$1"
            show_help
            exit 1
            ;;
    esac
done

# 检查必要参数
if [[ -z "\$COMMAND" ]]; then
    log_error "请指定命令"
    show_help
    exit 1
fi

# 创建备份目录
mkdir -p "\$BACKUP_BASE_DIR"

# 执行命令
case "\$COMMAND" in
    create-full)
        log_info "开始创建完整备份..."
        
        # 调用API创建备份
        response=\$(curl -s -X POST "\$API_BASE_URL/backup/full" \\
            -H "Content-Type: application/json" \\
            -d "{\"description\": \"\$DESCRIPTION\"}")
        
        if echo "\$response" | jq -e '.backup_name' > /dev/null 2>&1; then
            backup_name=\$(echo "\$response" | jq -r '.backup_name')
            backup_size=\$(echo "\$response" | jq -r '.backup_size')
            log_info "完整备份创建成功: \$backup_name"
            log_info "备份大小: \$(numfmt --to=iec \$backup_size)"
        else
            log_error "创建完整备份失败"
            echo "\$response"
            exit 1
        fi
        ;;
        
    create-experiment)
        if [[ -z "\$EXPERIMENT_ID" ]]; then
            log_error "创建实验备份需要指定 --experiment-id"
            exit 1
        fi
        
        log_info "开始创建实验 \$EXPERIMENT_ID 的备份..."
        
        response=\$(curl -s -X POST "\$API_BASE_URL/backup/experiment/\$EXPERIMENT_ID")
        
        if echo "\$response" | jq -e '.backup_name' > /dev/null 2>&1; then
            backup_name=\$(echo "\$response" | jq -r '.backup_name')
            backup_size=\$(echo "\$response" | jq -r '.backup_size')
            log_info "实验备份创建成功: \$backup_name"
            log_info "备份大小: \$(numfmt --to=iec \$backup_size)"
        else
            log_error "创建实验备份失败"
            echo "\$response"
            exit 1
        fi
        ;;
        
    list)
        log_info "获取备份列表..."
        
        response=\$(curl -s "\$API_BASE_URL/backup")
        
        if echo "\$response" | jq -e '.backups' > /dev/null 2>&1; then
            echo "备份列表:"
            echo "======================================"
            echo "\$response" | jq -r '.backups[] | "\(.backup_name) | \(.backup_type) | \((.file_size | tonumber) / 1024 / 1024 | floor)MB | \(.created_at)"'
        else
            log_error "获取备份列表失败"
            echo "\$response"
            exit 1
        fi
        ;;
        
    restore)
        if [[ -z "\$BACKUP_NAME" ]]; then
            log_error "恢复备份需要指定 --backup-name"
            exit 1
        fi
        
        log_warn "即将恢复备份: \$BACKUP_NAME"
        log_warn "这可能会覆盖现有数据，确定要继续吗？ (y/N)"
        read -r confirm
        if [[ \$confirm != "y" && \$confirm != "Y" ]]; then
            log_info "操作已取消"
            exit 0
        fi
        
        log_info "开始恢复备份 \$BACKUP_NAME..."
        
        response=\$(curl -s -X POST "\$API_BASE_URL/backup/\$BACKUP_NAME/restore")
        
        if echo "\$response" | jq -e '.restored_at' > /dev/null 2>&1; then
            log_info "备份恢复成功"
            echo "\$response" | jq '.'
        else
            log_error "恢复备份失败"
            echo "\$response"
            exit 1
        fi
        ;;
        
    delete)
        if [[ -z "\$BACKUP_NAME" ]]; then
            log_error "删除备份需要指定 --backup-name"
            exit 1
        fi
        
        log_warn "即将删除备份: \$BACKUP_NAME"
        log_warn "确定要删除吗？此操作不可恢复！ (y/N)"
        read -r confirm
        if [[ \$confirm != "y" && \$confirm != "Y" ]]; then
            log_info "操作已取消"
            exit 0
        fi
        
        log_info "开始删除备份 \$BACKUP_NAME..."
        
        response=\$(curl -s -X DELETE "\$API_BASE_URL/backup/\$BACKUP_NAME")
        
        if echo "\$response" | jq -e '.message' > /dev/null 2>&1; then
            log_info "备份删除成功"
        else
            log_error "删除备份失败"
            echo "\$response"
            exit 1
        fi
        ;;
        
    cleanup)
        log_info "清理 \$RETENTION_DAYS 天前的备份..."
        
        # 获取备份列表
        response=\$(curl -s "\$API_BASE_URL/backup")
        
        if ! echo "\$response" | jq -e '.backups' > /dev/null 2>&1; then
            log_error "获取备份列表失败"
            exit 1
        fi
        
        # 计算截止日期
        cutoff_date=\$(date -d "\$RETENTION_DAYS days ago" +%Y%m%d)
        
        # 查找过期备份
        expired_backups=\$(echo "\$response" | jq -r --arg cutoff "\$cutoff_date" '.backups[] | select((.created_at | gsub("[_:]"; "") | split("T")[0]) < \$cutoff) | .backup_name')
        
        if [[ -z "\$expired_backups" ]]; then
            log_info "没有找到过期备份"
            exit 0
        fi
        
        log_info "找到以下过期备份:"
        echo "\$expired_backups"
        
        log_warn "确定要删除这些过期备份吗？ (y/N)"
        read -r confirm
        if [[ \$confirm != "y" && \$confirm != "Y" ]]; then
            log_info "操作已取消"
            exit 0
        fi
        
        # 删除过期备份
        deleted_count=0
        for backup_name in \$expired_backups; do
            log_info "删除备份: \$backup_name"
            delete_response=\$(curl -s -X DELETE "\$API_BASE_URL/backup/\$backup_name")
            
            if echo "\$delete_response" | jq -e '.message' > /dev/null 2>&1; then
                ((deleted_count++))
            else
                log_warn "删除备份 \$backup_name 失败"
            fi
        done
        
        log_info "清理完成，删除了 \$deleted_count 个过期备份"
        ;;
        
    *)
        log_error "未知命令: \$COMMAND"
        show_help
        exit 1
        ;;
esac
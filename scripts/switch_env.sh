#!/bin/bash
# 环境切换脚本 - 在开发和生产环境之间切换

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_PROD_FILE="$PROJECT_ROOT/.env_prod"
BACKUP_DIR="$PROJECT_ROOT/.env_backups"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "环境切换脚本 - 在开发和生产环境之间切换"
    echo ""
    echo "用法: $0 [dev|prod|status]"
    echo ""
    echo "命令:"
    echo "  dev     切换到开发环境"
    echo "  prod    切换到生产环境"
    echo "  status  显示当前环境状态"
    echo ""
    echo "示例:"
    echo "  $0 dev    # 切换到开发环境"
    echo "  $0 prod   # 切换到生产环境"
    echo "  $0 status # 显示当前环境"
}

# 创建备份目录
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
    fi
}

# 备份当前环境配置
backup_current_env() {
    if [ -f "$ENV_FILE" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="$BACKUP_DIR/.env.backup_$timestamp"
        cp "$ENV_FILE" "$backup_file"
        echo -e "${GREEN}✓${NC} 已备份当前配置到: $backup_file"
    fi
}

# 显示当前环境状态
show_status() {
    echo "当前环境配置状态:"
    echo "===================="
    
    if [ -f "$ENV_FILE" ]; then
        local current_env=$(grep "^DJANGO_ENV=" "$ENV_FILE" | cut -d'=' -f2 | tr -d "'\"")
        local current_db=$(grep "^MARIADB_DATABASE=" "$ENV_FILE" | cut -d'=' -f2 | tr -d "'\"")
        local debug_mode=$(grep "^DJANGO_DEBUG=" "$ENV_FILE" | cut -d'=' -f2 | tr -d "'\"")
        
        echo -e "环境类型: ${GREEN}${current_env:-未设置}${NC}"
        echo -e "数据库名称: ${GREEN}${current_db:-未设置}${NC}"
        echo -e "调试模式: ${GREEN}${debug_mode:-未设置}${NC}"
        echo -e "配置文件: ${GREEN}$ENV_FILE${NC}"
    else
        echo -e "${RED}✗${NC} 未找到配置文件: $ENV_FILE"
    fi
    
    echo ""
    echo "可用环境:"
    echo "  - 开发环境 (dev): 数据库名称 = tiktok_products_dev"
    echo "  - 生产环境 (prod): 数据库名称 = tiktok_products"
}

# 切换到开发环境
switch_to_dev() {
    echo -e "${YELLOW}切换到开发环境...${NC}"
    
    if [ ! -f "$ENV_PROD_FILE" ]; then
        echo -e "${RED}✗${NC} 生产环境配置文件不存在: $ENV_PROD_FILE"
        exit 1
    fi
    
    create_backup_dir
    backup_current_env
    
    # 复制生产环境配置到 .env
    cp "$ENV_PROD_FILE" "$ENV_FILE"
    
    # 修改开发环境特定的配置
    # 如果 DJANGO_ENV 被注释，则取消注释并设置值
    if grep -q "^# DJANGO_ENV=" "$ENV_FILE"; then
        sed -i "s/^# DJANGO_ENV=.*/DJANGO_ENV=development/" "$ENV_FILE"
    elif grep -q "^DJANGO_ENV=" "$ENV_FILE"; then
        sed -i "s/^DJANGO_ENV=.*/DJANGO_ENV=development/" "$ENV_FILE"
    else
        echo "DJANGO_ENV=development" >> "$ENV_FILE"
    fi
    
    sed -i "s/^DJANGO_DEBUG=.*/DJANGO_DEBUG=True/" "$ENV_FILE"
    sed -i "s/^MARIADB_DATABASE=.*/MARIADB_DATABASE=tiktok_products_dev/" "$ENV_FILE"
    sed -i "s/^MYSQL_DB_NAME=.*/MYSQL_DB_NAME=tiktok_products_dev/" "$ENV_FILE"
    sed -i "s/^DB_LOCAL_NAME=.*/DB_LOCAL_NAME=tiktok_products_dev/" "$ENV_FILE"
    sed -i "s/^DB_REMOTE_NAME=.*/DB_REMOTE_NAME=tiktok_products_dev/" "$ENV_FILE"
    sed -i "s/^DB_SYNC_ENABLED=.*/DB_SYNC_ENABLED=True/" "$ENV_FILE"
    
    echo -e "${GREEN}✓${NC} 已切换到开发环境"
    echo ""
    echo "主要配置变更:"
    echo "  - DJANGO_ENV: development"
    echo "  - DJANGO_DEBUG: True"
    echo "  - 数据库名称: tiktok_products_dev"
    echo "  - 数据同步: 已启用"
    echo ""
    echo "请运行以下命令重启容器:"
    echo "  docker compose down"
    echo "  docker compose up -d"
}

# 切换到生产环境
switch_to_prod() {
    echo -e "${YELLOW}切换到生产环境...${NC}"
    
    if [ ! -f "$ENV_PROD_FILE" ]; then
        echo -e "${RED}✗${NC} 生产环境配置文件不存在: $ENV_PROD_FILE"
        exit 1
    fi
    
    create_backup_dir
    backup_current_env
    
    # 复制生产环境配置到 .env
    cp "$ENV_PROD_FILE" "$ENV_FILE"
    
    # 修改生产环境特定的配置
    # 如果 DJANGO_ENV 被注释，则取消注释并设置值
    if grep -q "^# DJANGO_ENV=" "$ENV_FILE"; then
        sed -i "s/^# DJANGO_ENV=.*/DJANGO_ENV=production/" "$ENV_FILE"
    elif grep -q "^DJANGO_ENV=" "$ENV_FILE"; then
        sed -i "s/^DJANGO_ENV=.*/DJANGO_ENV=production/" "$ENV_FILE"
    else
        echo "DJANGO_ENV=production" >> "$ENV_FILE"
    fi
    
    sed -i "s/^DJANGO_DEBUG=.*/DJANGO_DEBUG=False/" "$ENV_FILE"
    sed -i "s/^MARIADB_DATABASE=.*/MARIADB_DATABASE=tiktok_products/" "$ENV_FILE"
    sed -i "s/^MYSQL_DB_NAME=.*/MYSQL_DB_NAME=tiktok_products/" "$ENV_FILE"
    sed -i "s/^DB_LOCAL_NAME=.*/DB_LOCAL_NAME=tiktok_products/" "$ENV_FILE"
    sed -i "s/^DB_REMOTE_NAME=.*/DB_REMOTE_NAME=tiktok_products/" "$ENV_FILE"
    sed -i "s/^DB_SYNC_ENABLED=.*/DB_SYNC_ENABLED=False/" "$ENV_FILE"
    
    echo -e "${GREEN}✓${NC} 已切换到生产环境"
    echo ""
    echo "主要配置变更:"
    echo "  - DJANGO_ENV: production"
    echo "  - DJANGO_DEBUG: False"
    echo "  - 数据库名称: tiktok_products"
    echo "  - 数据同步: 已禁用"
    echo ""
    echo "请运行以下命令重启容器:"
    echo "  docker compose down"
    echo "  docker compose up -d"
}

# 主函数
main() {
    case "${1:-}" in
        dev)
            switch_to_dev
            ;;
        prod)
            switch_to_prod
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知命令 '${1:-}'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

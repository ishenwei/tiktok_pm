#!/bin/bash
# 数据库迁移脚本 - 在开发和生产数据库之间迁移数据

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "数据库迁移脚本 - 在开发和生产数据库之间迁移数据"
    echo ""
    echo "用法: $0 [dev_to_prod|prod_to_dev|backup|status]"
    echo ""
    echo "命令:"
    echo "  dev_to_prod   将开发数据库迁移到生产数据库"
    echo "  prod_to_dev   将生产数据库迁移到开发数据库"
    echo "  backup        备份当前数据库"
    echo "  status        显示数据库状态"
    echo ""
    echo "示例:"
    echo "  $0 dev_to_prod  # 将开发数据迁移到生产"
    echo "  $0 prod_to_dev  # 将生产数据迁移到开发"
    echo "  $0 backup       # 备份数据库"
}

# 获取数据库配置
get_db_config() {
    local env_file="$PROJECT_ROOT/.env"
    
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}✗${NC} 配置文件不存在: $env_file"
        exit 1
    fi
    
    source "$env_file"
    
    if [ "$DB_ENV" = "local" ]; then
        echo "DB_HOST=$DB_LOCAL_HOST"
        echo "DB_PORT=$DB_LOCAL_PORT"
        echo "DB_NAME=$DB_LOCAL_NAME"
        echo "DB_USER=$DB_LOCAL_USER"
        echo "DB_PASSWORD=$DB_LOCAL_PASSWORD"
    else
        echo "DB_HOST=$DB_REMOTE_HOST"
        echo "DB_PORT=$DB_REMOTE_PORT"
        echo "DB_NAME=$DB_REMOTE_NAME"
        echo "DB_USER=$DB_REMOTE_USER"
        echo "DB_PASSWORD=$DB_REMOTE_PASSWORD"
    fi
}

# 显示数据库状态
show_status() {
    echo "数据库状态:"
    echo "============"
    
    if [ -f "$PROJECT_ROOT/.env" ]; then
        source "$PROJECT_ROOT/.env"
        
        echo "当前环境: ${GREEN}${DJANGO_ENV:-未设置}${NC}"
        echo "数据库环境: ${GREEN}${DB_ENV}${NC}"
        echo "本地数据库:"
        echo "  - 主机: ${GREEN}${DB_LOCAL_HOST}${NC}"
        echo "  - 端口: ${GREEN}${DB_LOCAL_PORT}${NC}"
        echo "  - 名称: ${GREEN}${DB_LOCAL_NAME}${NC}"
        echo "  - 用户: ${GREEN}${DB_LOCAL_USER}${NC}"
        echo "远程数据库:"
        echo "  - 主机: ${GREEN}${DB_REMOTE_HOST}${NC}"
        echo "  - 端口: ${GREEN}${DB_REMOTE_PORT}${NC}"
        echo "  - 名称: ${GREEN}${DB_REMOTE_NAME}${NC}"
        echo "  - 用户: ${GREEN}${DB_REMOTE_USER}${NC}"
        
        # 检查数据库连接
        echo ""
        echo "数据库连接测试:"
        
        # 测试本地数据库
        if docker exec tiktok_pm_mariadb mysqladmin ping -h localhost -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" &>/dev/null; then
            echo -e "  - 本地数据库: ${GREEN}✓ 连接正常${NC}"
        else
            echo -e "  - 本地数据库: ${RED}✗ 连接失败${NC}"
        fi
        
        # 测试远程数据库
        if mysqladmin ping -h"$DB_REMOTE_HOST" -P"$DB_REMOTE_PORT" -u"$DB_REMOTE_USER" -p"$DB_REMOTE_PASSWORD" &>/dev/null; then
            echo -e "  - 远程数据库: ${GREEN}✓ 连接正常${NC}"
        else
            echo -e "  - 远程数据库: ${RED}✗ 连接失败${NC}"
        fi
    else
        echo -e "${RED}✗${NC} 配置文件不存在"
    fi
}

# 备份数据库
backup_database() {
    local backup_dir="$PROJECT_ROOT/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    if [ ! -d "$backup_dir" ]; then
        mkdir -p "$backup_dir"
    fi
    
    source "$PROJECT_ROOT/.env"
    
    echo -e "${YELLOW}备份数据库...${NC}"
    
    # 备份本地数据库
    local local_backup="$backup_dir/tiktok_products_dev_${timestamp}.sql"
    docker exec tiktok_pm_mariadb mysqldump -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE" > "$local_backup"
    echo -e "${GREEN}✓${NC} 本地数据库已备份到: $local_backup"
    
    # 备份远程数据库
    local remote_backup="$backup_dir/tiktok_products_${timestamp}.sql"
    mysqldump -h"$DB_REMOTE_HOST" -P"$DB_REMOTE_PORT" -u"$DB_REMOTE_USER" -p"$DB_REMOTE_PASSWORD" "$DB_REMOTE_NAME" > "$remote_backup"
    echo -e "${GREEN}✓${NC} 远程数据库已备份到: $remote_backup"
}

# 迁移开发数据库到生产数据库
migrate_dev_to_prod() {
    echo -e "${YELLOW}警告: 此操作将覆盖生产数据库！${NC}"
    echo -e "${YELLOW}生产数据库中的所有数据将被替换为开发数据库的数据。${NC}"
    echo ""
    read -p "确认继续？(输入 'yes' 继续): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "操作已取消"
        exit 0
    fi
    
    echo -e "${YELLOW}迁移开发数据库到生产数据库...${NC}"
    
    # 先备份
    backup_database
    
    source "$PROJECT_ROOT/.env"
    
    # 导出开发数据库
    local temp_file="/tmp/dev_to_prod_${timestamp}.sql"
    docker exec tiktok_pm_mariadb mysqldump -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE" > "$temp_file"
    
    # 导入到生产数据库
    mysql -h"$DB_REMOTE_HOST" -P"$DB_REMOTE_PORT" -u"$DB_REMOTE_USER" -p"$DB_REMOTE_PASSWORD" "$DB_REMOTE_NAME" < "$temp_file"
    
    rm -f "$temp_file"
    
    echo -e "${GREEN}✓${NC} 数据迁移完成"
}

# 迁移生产数据库到开发数据库
migrate_prod_to_dev() {
    echo -e "${YELLOW}警告: 此操作将覆盖开发数据库！${NC}"
    echo -e "${YELLOW}开发数据库中的所有数据将被替换为生产数据库的数据。${NC}"
    echo ""
    read -p "确认继续？(输入 'yes' 继续): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "操作已取消"
        exit 0
    fi
    
    echo -e "${YELLOW}迁移生产数据库到开发数据库...${NC}"
    
    # 先备份
    backup_database
    
    source "$PROJECT_ROOT/.env"
    
    # 导出生产数据库
    local temp_file="/tmp/prod_to_dev_${timestamp}.sql"
    mysqldump -h"$DB_REMOTE_HOST" -P"$DB_REMOTE_PORT" -u"$DB_REMOTE_USER" -p"$DB_REMOTE_PASSWORD" "$DB_REMOTE_NAME" > "$temp_file"
    
    # 导入到开发数据库
    docker exec -i tiktok_pm_mariadb mysql -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE" < "$temp_file"
    
    rm -f "$temp_file"
    
    echo -e "${GREEN}✓${NC} 数据迁移完成"
}

# 主函数
main() {
    case "${1:-}" in
        dev_to_prod)
            migrate_dev_to_prod
            ;;
        prod_to_dev)
            migrate_prod_to_dev
            ;;
        backup)
            backup_database
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

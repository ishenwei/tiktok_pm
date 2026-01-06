#!/bin/bash

# ==========================================================
# 生产环境日志查看脚本
# ==========================================================

LOG_DIR="/home/shenwei/docker/tiktok_pm/logs"
PROJECT_DIR="/path/to/your/project"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Django 生产环境日志查看工具"
echo "============================================================"
echo ""

# 函数：显示菜单
show_menu() {
    echo "请选择要查看的日志："
    echo "1) Django 主日志 (django.log)"
    echo "2) Django 错误日志 (django_error.log)"
    echo "3) API 请求日志 (api.log)"
    echo "4) n8n Webhook 日志 (n8n_webhook.log)"
    echo "5) Gunicorn 访问日志"
    echo "6) Gunicorn 错误日志"
    echo "7) Nginx 访问日志"
    echo "8) Nginx 错误日志"
    echo "9) 实时监控所有日志"
    echo "10) 搜索特定关键词"
    echo "0) 退出"
    echo ""
}

# 函数：实时查看日志
tail_log() {
    local log_file=$1
    local log_name=$2
    
    if [ -f "$log_file" ]; then
        echo -e "${GREEN}正在查看: $log_name${NC}"
        echo "按 Ctrl+C 退出"
        echo "============================================================"
        tail -f "$log_file"
    else
        echo -e "${RED}错误: 日志文件不存在: $log_file${NC}"
    fi
}

# 函数：搜索日志
search_logs() {
    echo "请输入要搜索的关键词:"
    read keyword
    
    echo ""
    echo "============================================================"
    echo -e "${GREEN}搜索结果: '$keyword'${NC}"
    echo "============================================================"
    
    # 搜索所有日志文件
    find "$LOG_DIR" -name "*.log" -type f -exec grep -n --color=always "$keyword" {} + 2>/dev/null
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 (0-10): " choice
    
    case $choice in
        1)
            tail_log "$LOG_DIR/django.log" "Django 主日志"
            ;;
        2)
            tail_log "$LOG_DIR/django_error.log" "Django 错误日志"
            ;;
        3)
            tail_log "$LOG_DIR/api.log" "API 请求日志"
            ;;
        4)
            tail_log "$LOG_DIR/n8n_webhook.log" "n8n Webhook 日志"
            ;;
        5)
            tail_log "/var/log/gunicorn/access.log" "Gunicorn 访问日志"
            ;;
        6)
            tail_log "/var/log/gunicorn/error.log" "Gunicorn 错误日志"
            ;;
        7)
            tail_log "/var/log/nginx/access.log" "Nginx 访问日志"
            ;;
        8)
            tail_log "/var/log/nginx/error.log" "Nginx 错误日志"
            ;;
        9)
            echo -e "${GREEN}实时监控所有日志...${NC}"
            echo "按 Ctrl+C 退出"
            echo "============================================================"
            tail -f $LOG_DIR/*.log /var/log/gunicorn/*.log /var/log/nginx/*.log 2>/dev/null
            ;;
        10)
            search_logs
            ;;
        0)
            echo "退出日志查看工具"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项，请重新选择${NC}"
            ;;
    esac
    
    echo ""
    read -p "按 Enter 继续..."
    clear
done

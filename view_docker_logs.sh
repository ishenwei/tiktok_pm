#!/bin/bash

# ==========================================================
# Docker Compose 环境日志查看工具
# ==========================================================
#
# 功能说明：
#     本脚本提供 Docker Compose 环境下应用程序日志的查看和管理功能
#     支持实时日志监控、历史日志查看、日志搜索、容器状态检查等功能
#
# 适用环境：
#     - Docker Compose 部署的 Django 应用
#     - 包含 web (Django + Gunicorn)、worker (Django Q)、nginx 三个服务
#
# 使用方法：
#     1. 确保 docker-compose.yml 文件在当前目录
#     2. 运行脚本: bash view_docker_logs.sh
#     3. 按照菜单提示选择要执行的操作
#
# 依赖要求：
#     - Docker (版本 20.10+)
#     - Docker Compose (作为 Docker CLI 插件，使用 'docker compose' 命令)
#
# 注意事项：
#     - 需要在 docker-compose.yml 所在目录执行
#     - 确保容器正在运行
#     - 某些操作需要容器内存在相应的日志目录
#     - 本脚本使用 'docker compose' 命令（新版 Docker Compose V2）
#     - 如果使用旧版 docker-compose 命令，请将所有 'docker compose' 替换为 'docker-compose'
#
# ==========================================================

echo "============================================================"
echo "Docker Compose 环境日志查看工具"
echo "============================================================"
echo ""

# 函数：显示菜单
#
# 功能说明：
#     显示主菜单，列出所有可用的日志查看和管理选项
#
# 参数说明：
#     无
#
# 返回值：
#     无（直接输出菜单到控制台）
#
# 使用示例：
#     show_menu
#
# 菜单选项：
#     1) Web 服务实时日志 (Django + Gunicorn)
#     2) Worker 服务实时日志 (Django Q)
#     3) Nginx 服务实时日志
#     4) 所有服务实时日志
#     5) Web 服务最近 100 行
#     6) Worker 服务最近 100 行
#     7) Nginx 服务最近 100 行
#     8) 搜索所有服务日志
#     9) 查看容器状态
#     10) 进入容器内部查看日志
#     11) 从容器复制日志文件到本地
#     0) 退出
#
show_menu() {
    echo "请选择要查看的日志："
    echo "1) Web 服务实时日志 (Django + Gunicorn)"
    echo "2) Worker 服务实时日志 (Django Q)"
    echo "3) Nginx 服务实时日志"
    echo "4) 所有服务实时日志"
    echo "5) Web 服务最近 100 行"
    echo "6) Worker 服务最近 100 行"
    echo "7) Nginx 服务最近 100 行"
    echo "8) 搜索所有服务日志"
    echo "9) 查看容器状态"
    echo "10) 进入容器内部查看日志"
    echo "11) 从容器复制日志文件到本地"
    echo "0) 退出"
    echo ""
}

# 函数：实时查看日志
#
# 功能说明：
#     实时监控指定服务的日志输出，类似于 Linux 的 tail -f 命令
#     显示最新的 50 行日志，并持续跟踪新的日志输出
#
# 参数说明：
#     $1 (service): Docker Compose 服务名称（web/worker/nginx）
#     $2 (service_name): 服务的显示名称（用于输出提示信息）
#
# 返回值：
#     无（直接输出日志到控制台）
#
# 使用示例：
#     tail_logs "web" "Web 服务 (Django + Gunicorn)"
#     tail_logs "worker" "Worker 服务 (Django Q)"
#     tail_logs "nginx" "Nginx 服务"
#
# 注意事项：
#     - 使用 Ctrl+C 可以退出实时日志查看
#     - 默认显示最近 50 行日志
#     - 需要服务正在运行才能查看日志
#
tail_logs() {
    local service=$1
    local service_name=$2
    
    echo "============================================================"
    echo "正在查看: $service_name 实时日志"
    echo "按 Ctrl+C 退出"
    echo "============================================================"
    docker compose logs -f --tail=50 $service
}

# 函数：查看最近日志
#
# 功能说明：
#     查看指定服务的最近 N 行日志，不进行实时跟踪
#     适用于快速查看最近的日志记录，用于问题排查和调试
#
# 参数说明：
#     $1 (service): Docker Compose 服务名称（web/worker/nginx）
#     $2 (service_name): 服务的显示名称（用于输出提示信息）
#     $3 (lines): 要显示的日志行数（默认为 100）
#
# 返回值：
#     无（直接输出日志到控制台）
#
# 使用示例：
#     show_recent_logs "web" "Web 服务" 100
#     show_recent_logs "worker" "Worker 服务" 200
#     show_recent_logs "nginx" "Nginx 服务" 50
#
# 注意事项：
#     - 仅显示指定行数的日志，不进行实时跟踪
#     - 适合快速查看最近的错误或警告信息
#     - 可以根据需要调整显示的行数
#
show_recent_logs() {
    local service=$1
    local service_name=$2
    local lines=$3
    
    echo "============================================================"
    echo "正在查看: $service_name 最近 $lines 行日志"
    echo "============================================================"
    docker compose logs --tail=$lines $service
}

# 函数：搜索日志
#
# 功能说明：
#     在所有服务的日志中搜索包含指定关键词的日志行
#     支持不区分大小写的搜索，并高亮显示匹配的关键词
#
# 参数说明：
#     无（通过用户交互输入搜索关键词）
#
# 返回值：
#     无（直接输出搜索结果到控制台）
#
# 使用示例：
#     search_logs
#     # 然后输入要搜索的关键词，如 "ERROR"、"n8n"、"product" 等
#
# 注意事项：
#     - 搜索不区分大小写
#     - 匹配的关键词会以彩色高亮显示
#     - 如果关键词为空，会提示重新输入
#     - 搜索范围包括所有服务的日志
#
search_logs() {
    echo "请输入要搜索的关键词:"
    read keyword
    
    if [ -z "$keyword" ]; then
        echo "关键词不能为空"
        return
    fi
    
    echo ""
    echo "============================================================"
    echo "搜索结果: '$keyword'"
    echo "============================================================"
    docker compose logs | grep --color=always -i "$keyword"
}

# 函数：查看容器状态
#
# 功能说明：
#     显示所有 Docker Compose 服务的运行状态和详细信息
#     包括容器名称、状态、端口映射、命令等信息
#
# 参数说明：
#     无
#
# 返回值：
#     无（直接输出容器状态到控制台）
#
# 使用示例：
#     show_container_status
#
# 输出信息：
#     - 容器名称
#     - 运行状态（Up/Exited 等）
#     - 端口映射
#     - 运行的命令
#     - 容器 ID
#
# 注意事项：
#     - 显示所有容器（包括已停止的容器）
#     - 适用于检查服务是否正常运行
#     - 可以用于排查容器启动失败的问题
#
show_container_status() {
    echo "============================================================"
    echo "容器状态"
    echo "============================================================"
    docker compose ps
    echo ""
    
    echo "============================================================"
    echo "容器详细信息"
    echo "============================================================"
    docker compose ps -a
}

# 函数：进入容器
#
# 功能说明：
#     进入指定的 Docker 容器内部，提供交互式 shell 访问
#     可以在容器内部执行命令、查看文件、调试问题等
#
# 参数说明：
#     无（通过用户交互选择要进入的容器）
#
# 返回值：
#     无（进入容器的交互式 shell）
#
# 使用示例：
#     enter_container
#     # 然后选择要进入的容器（1-web, 2-worker, 3-nginx）
#
# 支持的容器：
#     1) web (Django + Gunicorn) - 使用 /bin/bash
#     2) worker (Django Q) - 使用 /bin/bash
#     3) nginx - 使用 /bin/sh
#
# 注意事项：
#     - web 和 worker 容器使用 bash shell
#     - nginx 容器使用 sh shell（轻量级）
#     - 使用 exit 命令可以退出容器
#     - 在容器内的修改在容器重启后会丢失（除非挂载了卷）
#     - 适合用于临时调试和问题排查
#
enter_container() {
    echo "请选择要进入的容器:"
    echo "1) web (Django + Gunicorn)"
    echo "2) worker (Django Q)"
    echo "3) nginx"
    read -p "请输入选项 (1-3): " choice
    
    case $choice in
        1)
            echo "进入 web 容器..."
            docker compose exec web /bin/bash
            ;;
        2)
            echo "进入 worker 容器..."
            docker compose exec worker /bin/bash
            ;;
        3)
            echo "进入 nginx 容器..."
            docker compose exec nginx /bin/sh
            ;;
        *)
            echo "无效选项"
            ;;
    esac
}

# 函数：从容器复制日志文件
copy_logs_from_container() {
    echo "请选择要复制日志的容器:"
    echo "1) web (Django + Gunicorn)"
    echo "2) worker (Django Q)"
    echo "3) nginx"
    read -p "请输入选项 (1-3): " choice
    
    local container_name=""
    local service_name=""
    
    case $choice in
        1)
            container_name="tiktok_pm_web"
            service_name="web"
            ;;
        2)
            container_name="tiktok_pm_worker"
            service_name="worker"
            ;;
        3)
            container_name="tiktok_pm_nginx"
            service_name="nginx"
            ;;
        *)
            echo "无效选项"
            return
            ;;
    esac
    
    echo "============================================================"
    echo "从容器 $container_name 复制日志文件"
    echo "============================================================"
    
    # 创建本地日志目录
    mkdir -p docker_logs
    
    # 复制容器内的日志文件
    if [ "$service_name" == "web" ] || [ "$service_name" == "worker" ]; then
        # Django 应用日志
        docker cp $container_name:/app/logs/ ./docker_logs/ 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ 成功复制 /app/logs/ 到 ./docker_logs/"
            echo ""
            echo "复制的文件:"
            ls -lh ./docker_logs/logs/
        else
            echo "⚠️  容器内没有 /app/logs/ 目录"
            echo "日志可能通过 Docker 日志驱动输出，请使用 docker compose logs 命令查看"
        fi
    elif [ "$service_name" == "nginx" ]; then
        # Nginx 日志
        docker cp $container_name:/var/log/nginx/ ./docker_logs/nginx/ 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ 成功复制 /var/log/nginx/ 到 ./docker_logs/nginx/"
            echo ""
            echo "复制的文件:"
            ls -lh ./docker_logs/nginx/
        else
            echo "⚠️  容器内没有 /var/log/nginx/ 目录"
        fi
    fi
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 (0-11): " choice
    
    case $choice in
        1)
            tail_logs "web" "Web 服务 (Django + Gunicorn)"
            ;;
        2)
            tail_logs "worker" "Worker 服务 (Django Q)"
            ;;
        3)
            tail_logs "nginx" "Nginx 服务"
            ;;
        4)
            echo "============================================================"
            echo "正在查看所有服务实时日志"
            echo "按 Ctrl+C 退出"
            echo "============================================================"
            docker compose logs -f --tail=50
            ;;
        5)
            show_recent_logs "web" "Web 服务" 100
            ;;
        6)
            show_recent_logs "worker" "Worker 服务" 100
            ;;
        7)
            show_recent_logs "nginx" "Nginx 服务" 100
            ;;
        8)
            search_logs
            ;;
        9)
            show_container_status
            ;;
        10)
            enter_container
            ;;
        11)
            copy_logs_from_container
            ;;
        0)
            echo "退出日志查看工具"
            exit 0
            ;;
        *)
            echo "无效选项，请重新选择"
            ;;
    esac
    
    echo ""
    read -p "按 Enter 继续..."
    clear
done

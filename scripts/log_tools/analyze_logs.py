#!/usr/bin/env python3
# ==========================================================
# Django 生产环境日志分析工具
# ==========================================================
#
# 功能说明：
#   - 快速查看和分析 Django 应用的日志文件
#   - 支持关键词搜索、错误分析、统计等功能
#   - 提供 n8n webhook 日志的专项分析
#   - 支持多种日志格式解析（Django、Gunicorn、Nginx）
#
# 使用方式：
#   1. 直接运行脚本：python analyze_logs.py
#   2. 选择相应的功能菜单进行操作
#   3. 按照提示输入参数（如关键词、日志文件名等）
#
# 使用示例：
#   # 查看最近的 Django 日志
#   python analyze_logs.py
#   # 选择菜单 1
#
#   # 搜索关键词
#   python analyze_logs.py
#   # 选择菜单 7，输入关键词 "ERROR"
#
#   # 分析 n8n webhook 日志
#   python analyze_logs.py
#   # 选择菜单 6
#
# 日志文件位置：
#   - 项目日志：logs/ 目录下
#   - 系统日志：/var/log/ 目录下
#
# 注意事项：
#   - 需要确保日志文件存在且有读取权限
#   - 大文件搜索可能需要较长时间
#   - 建议定期清理旧日志文件
# ==========================================================

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

# ==========================================================
# 配置区域
# ==========================================================

# 日志目录配置
# LOG_DIR: 系统日志目录（生产环境）
# PROJECT_LOG_DIR: 项目日志目录（相对路径）
LOG_DIR = Path("/var/log/tiktok_pm")
PROJECT_LOG_DIR = Path(__file__).parent / "logs"

# 日志文件映射配置
# 键：日志名称（用于菜单选择和命令行参数）
# 值：日志文件的完整路径
LOG_FILES = {
    "django": PROJECT_LOG_DIR / "django.log",
    "error": PROJECT_LOG_DIR / "django_error.log",
    "api": PROJECT_LOG_DIR / "api.log",
    "n8n": PROJECT_LOG_DIR / "n8n_webhook.log",
    "gunicorn_access": Path("/var/log/gunicorn/access.log"),
    "gunicorn_error": Path("/var/log/gunicorn/error.log"),
    "nginx_access": Path("/var/log/nginx/access.log"),
    "nginx_error": Path("/var/log/nginx/error.log"),
}


# ==========================================================
# 辅助函数
# ==========================================================

def print_header(text):
    """
    打印格式化的标题
    
    功能说明：
        在控制台打印带分隔线的标题，用于区分不同的输出区域
    
    参数说明：
        text (str): 标题文本
    
    返回值：
        None
    
    使用示例：
        print_header("日志分析结果")
        # 输出：
        # ================================================================================
        #  日志分析结果
        # ================================================================================
    """
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80 + "\n")


def print_error(text):
    """
    打印错误信息
    
    功能说明：
        在控制台打印带错误图标的错误信息，用于提示用户操作失败
    
    参数说明：
        text (str): 错误信息文本
    
    返回值：
        None
    
    使用示例：
        print_error("日志文件不存在")
        # 输出：
        # ❌ 日志文件不存在
    """
    print(f"\n❌ {text}\n")


def print_success(text):
    """
    打印成功信息
    
    功能说明：
        在控制台打印带成功图标的成功信息，用于提示用户操作成功
    
    参数说明：
        text (str): 成功信息文本
    
    返回值：
        None
    
    使用示例：
        print_success("日志分析完成")
        # 输出：
        # ✅ 日志分析完成
    """
    print(f"\n✅ {text}\n")


def print_warning(text):
    """
    打印警告信息
    
    功能说明：
        在控制台打印带警告图标的警告信息，用于提示用户需要注意的事项
    
    参数说明：
        text (str): 警告信息文本
    
    返回值：
        None
    
    使用示例：
        print_warning("日志文件过大，搜索可能需要较长时间")
        # 输出：
        # ⚠️  日志文件过大，搜索可能需要较长时间
    """
    print(f"\n⚠️  {text}\n")


# ==========================================================
# 日志读取函数
# ==========================================================

def read_log_file(log_path, lines=None):
    """
    读取日志文件
    
    功能说明：
        从指定路径读取日志文件内容，支持读取全部内容或最后 N 行
    
    参数说明：
        log_path (Path): 日志文件路径
        lines (int, optional): 要读取的行数，None 表示读取全部
    
    返回值：
        list: 日志行列表，如果文件不存在或读取失败则返回 None
    
    使用示例：
        # 读取全部日志
        logs = read_log_file(Path("logs/django.log"))
        
        # 读取最后 100 行
        logs = read_log_file(Path("logs/django.log"), lines=100)
    """
    if not log_path.exists():
        return None
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            if lines:
                # 读取最后 N 行
                all_lines = f.readlines()
                return all_lines[-lines:]
            else:
                return f.readlines()
    except Exception as e:
        print_error(f"读取日志文件失败: {e}")
        return None


# ==========================================================
# 日志解析函数
# ==========================================================

def parse_log_line(line):
    """
    解析日志行
    
    功能说明：
        解析单行日志，提取时间戳、日志级别、模块、文件路径等信息
        支持多种日志格式（Django、Gunicorn、Nginx）
    
    参数说明：
        line (str): 日志行文本
    
    返回值：
        dict: 解析后的日志信息字典，包含以下字段：
            - timestamp: 时间戳
            - level: 日志级别
            - module: 模块名
            - path: 文件路径
            - line: 行号
            - message: 日志消息
            - raw: 原始日志行
          如果解析失败则返回 None
    
    使用示例：
        line = "[2025-01-05 10:30:45] INFO [products] views.py:123 - 处理请求"
        parsed = parse_log_line(line)
        print(parsed['timestamp'])  # 2025-01-05 10:30:45
        print(parsed['level'])      # INFO
        print(parsed['module'])     # products
    """
    # Django 日志格式: [2025-01-05 10:30:45] INFO [module] path:line - message
    django_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+) \[(.*?)\] (.*?):(\d+) - (.*)'
    
    # Gunicorn/Nginx 日志格式（通用）
    common_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    
    # 尝试匹配 Django 日志格式
    match = re.match(django_pattern, line)
    if match:
        return {
            'timestamp': match.group(1),
            'level': match.group(2),
            'module': match.group(3),
            'path': match.group(4),
            'line': match.group(5),
            'message': match.group(6),
            'raw': line
        }
    
    # 尝试匹配通用日志格式
    match = re.match(common_pattern, line)
    if match:
        return {
            'timestamp': match.group(1),
            'level': 'INFO',
            'module': 'system',
            'message': line,
            'raw': line
        }
    
    # 无法解析的格式
    return None


# ==========================================================
# 日志查看函数
# ==========================================================

def show_recent_logs(log_name, lines=100):
    """
    显示最近的日志
    
    功能说明：
        读取并显示指定日志文件的最后 N 行，每行前面显示行号
    
    参数说明：
        log_name (str): 日志名称（LOG_FILES 字典的键）
        lines (int): 要显示的行数，默认 100
    
    返回值：
        None
    
    使用示例：
        # 显示 Django 日志的最后 50 行
        show_recent_logs('django', 50)
        
        # 显示错误日志的最后 100 行
        show_recent_logs('error', 100)
    """
    print_header(f"显示 {log_name} 最近 {lines} 行日志")
    
    log_path = LOG_FILES.get(log_name)
    if not log_path:
        print_error(f"未找到日志配置: {log_name}")
        return
    
    log_lines = read_log_file(log_path, lines)
    if log_lines is None:
        print_error(f"日志文件不存在或无法读取: {log_path}")
        return
    
    for i, line in enumerate(log_lines, 1):
        print(f"{i:4d} | {line.rstrip()}")
    
    print_success(f"共显示 {len(log_lines)} 行日志")


# ==========================================================
# 日志搜索函数
# ==========================================================

def search_logs(keyword, log_name=None, lines=1000):
    """
    搜索日志中的关键词
    
    功能说明：
        在指定日志文件中搜索包含关键词的日志行，支持不区分大小写搜索
    
    参数说明：
        keyword (str): 要搜索的关键词
        log_name (str, optional): 日志名称，None 表示搜索所有日志
        lines (int): 每个日志文件读取的行数，默认 1000
    
    返回值：
        None
    
    使用示例：
        # 在所有日志中搜索 "ERROR"
        search_logs("ERROR")
        
        # 在 API 日志中搜索 "webhook"
        search_logs("webhook", log_name="api")
        
        # 在最近 500 行中搜索 "product_id"
        search_logs("product_id", lines=500)
    """
    print_header(f"搜索关键词: '{keyword}'")
    
    if log_name:
        log_paths = [LOG_FILES.get(log_name)]
        print(f"搜索范围: {log_name}")
    else:
        log_paths = [path for path in LOG_FILES.values() if path.exists()]
        print(f"搜索范围: 所有日志文件")
    
    results = []
    for log_path in log_paths:
        if not log_path or not log_path.exists():
            continue
        
        log_lines = read_log_file(log_path, lines)
        if not log_lines:
            continue
        
        for i, line in enumerate(log_lines):
            if keyword.lower() in line.lower():
                results.append({
                    'file': log_path.name,
                    'line': line.rstrip(),
                    'index': i + 1
                })
    
    if results:
        print_success(f"找到 {len(results)} 条匹配结果\n")
        for result in results:
            print(f"[{result['file']}] {result['line']}")
    else:
        print_warning("未找到匹配结果")


# ==========================================================
# 错误分析函数
# ==========================================================

def analyze_errors(log_name=None, hours=24):
    """
    分析错误日志
    
    功能说明：
        分析日志文件中的错误信息，统计错误类型和数量，显示最近的错误
    
    参数说明：
        log_name (str, optional): 日志名称，None 表示分析错误日志和 Django 日志
        hours (int): 分析最近几小时的日志，默认 24 小时
    
    返回值：
        None
    
    使用示例：
        # 分析最近 24 小时的错误
        analyze_errors()
        
        # 分析最近 48 小时的错误
        analyze_errors(hours=48)
        
        # 分析 API 日志中的错误
        analyze_errors(log_name="api")
    """
    print_header(f"分析最近 {hours} 小时的错误")
    
    if log_name:
        log_paths = [LOG_FILES.get(log_name)]
    else:
        log_paths = [LOG_FILES.get('error'), LOG_FILES.get('django')]
    
    error_count = 0
    error_types = Counter()
    error_messages = []
    
    for log_path in log_paths:
        if not log_path or not log_path.exists():
            continue
        
        log_lines = read_log_file(log_path)
        if not log_lines:
            continue
        
        for line in log_lines:
            parsed = parse_log_line(line)
            if parsed and parsed['level'] in ['ERROR', 'CRITICAL']:
                error_count += 1
                
                # 提取错误类型
                error_match = re.search(r'(\w+Error|Exception)', parsed['message'])
                if error_match:
                    error_types[error_match.group(1)] += 1
                
                error_messages.append({
                    'timestamp': parsed['timestamp'],
                    'module': parsed['module'],
                    'message': parsed['message'][:200]  # 只显示前200字符
                })
    
    print(f"总错误数: {error_count}")
    print("\n错误类型统计:")
    for error_type, count in error_types.most_common(10):
        print(f"  {error_type}: {count} 次")
    
    if error_messages:
        print("\n最近的错误:")
        for msg in error_messages[-5:]:
            print(f"  [{msg['timestamp']}] {msg['module']}: {msg['message']}")


# ==========================================================
# n8n Webhook 分析函数
# ==========================================================

def analyze_n8n_webhook():
    """
    分析 n8n webhook 日志
    
    功能说明：
        专门分析 n8n webhook 相关的日志，统计请求次数、成功/失败次数、涉及的产品 ID
    
    参数说明：
        None
    
    返回值：
        None
    
    使用示例：
        analyze_n8n_webhook()
        # 输出示例：
        # Webhook 请求总数: 150
        # 成功: 145
        # 失败: 5
        # 
        # 涉及的产品 ID (最近10个):
        #   - 123
        #   - 124
        #   - ...
    """
    print_header("分析 n8n Webhook 日志")
    
    log_path = LOG_FILES.get('n8n')
    if not log_path or not log_path.exists():
        print_error("n8n webhook 日志文件不存在")
        return
    
    log_lines = read_log_file(log_path, 500)
    if not log_lines:
        return
    
    # 统计变量
    webhook_count = 0
    success_count = 0
    error_count = 0
    product_ids = []
    
    for line in log_lines:
        if 'update_product_api' in line:
            webhook_count += 1
            
            if 'status": "success"' in line:
                success_count += 1
            elif 'error' in line.lower() or 'exception' in line.lower():
                error_count += 1
            
            # 提取 product_id
            product_match = re.search(r'product_id["\s:]+([0-9]+)', line)
            if product_match:
                product_ids.append(product_match.group(1))
    
    print(f"Webhook 请求总数: {webhook_count}")
    print(f"成功: {success_count}")
    print(f"失败: {error_count}")
    
    if product_ids:
        print(f"\n涉及的产品 ID (最近10个):")
        for pid in product_ids[-10:]:
            print(f"  - {pid}")


# ==========================================================
# 菜单和界面函数
# ==========================================================

def show_menu():
    """
    显示主菜单
    
    功能说明：
        在控制台显示功能菜单，列出所有可用的日志分析功能
    
    参数说明：
        None
    
    返回值：
        None
    
    使用示例：
        show_menu()
        # 输出：
        # ================================================================================
        #  Django 日志分析工具
        # ================================================================================
        # 
        # 1) 查看最近的 Django 主日志
        # 2) 查看最近的错误日志
        # ...
    """
    print_header("Django 日志分析工具")
    
    print("1) 查看最近的 Django 主日志")
    print("2) 查看最近的错误日志")
    print("3) 查看最近的 API 请求日志")
    print("4) 查看最近的 n8n Webhook 日志")
    print("5) 分析错误日志")
    print("6) 分析 n8n Webhook 日志")
    print("7) 搜索关键词")
    print("8) 查看所有日志文件状态")
    print("0) 退出")
    print()


def show_log_files_status():
    """
    显示所有日志文件状态
    
    功能说明：
        显示所有配置的日志文件的存在状态、文件大小和最后修改时间
    
    参数说明：
        None
    
    返回值：
        None
    
    使用示例：
        show_log_files_status()
        # 输出示例：
        # ================================================================================
        #  日志文件状态
        # ================================================================================
        # ✅ django              | 大小:    1024000 bytes | 修改时间: 2025-01-05 10:30:45
        # ❌ gunicorn_access     | 文件不存在
    """
    print_header("日志文件状态")
    
    for name, path in LOG_FILES.items():
        if path.exists():
            size = path.stat().st_size
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            print(f"✅ {name:20s} | 大小: {size:10d} bytes | 修改时间: {mtime}")
        else:
            print(f"❌ {name:20s} | 文件不存在")


# ==========================================================
# 主函数
# ==========================================================

def main():
    """
    主函数
    
    功能说明：
        程序入口，显示菜单并处理用户输入，调用相应的功能函数
    
    参数说明：
        None
    
    返回值：
        None
    
    使用示例：
        # 直接运行脚本
        python analyze_logs.py
    """
    while True:
        show_menu()
        choice = input("请输入选项 (0-8): ").strip()
        
        if choice == '0':
            print("退出日志分析工具")
            break
        
        elif choice == '1':
            show_recent_logs('django', 50)
        
        elif choice == '2':
            show_recent_logs('error', 50)
        
        elif choice == '3':
            show_recent_logs('api', 50)
        
        elif choice == '4':
            show_recent_logs('n8n', 50)
        
        elif choice == '5':
            analyze_errors()
        
        elif choice == '6':
            analyze_n8n_webhook()
        
        elif choice == '7':
            keyword = input("请输入要搜索的关键词: ").strip()
            if keyword:
                log_name = input("指定日志文件 (留空搜索所有日志): ").strip() or None
                search_logs(keyword, log_name)
        
        elif choice == '8':
            show_log_files_status()
        
        else:
            print_error("无效选项")
        
        input("\n按 Enter 继续...")


if __name__ == "__main__":
    main()

# ==========================================================
# Django 日志配置 (生产环境)
# ==========================================================
# 
# 功能说明：
#   - 配置 Django 应用的日志系统，支持多级别、多目标的日志记录
#   - 提供控制台输出、文件轮转、日志格式化等功能
#   - 支持按模块和应用分别配置日志级别和处理器
#
# 使用方式：
#   1. 在 Django settings.py 中导入此配置：
#      from logging_config import LOGGING
#   2. 在视图中使用日志记录器：
#      import logging
#      logger = logging.getLogger('products')
#      logger.info('这是一条信息日志')
#      logger.error('这是一条错误日志')
#
# 日志文件位置：
#   - django.log: 所有应用日志
#   - django_error.log: 错误级别日志
#   - api.log: API 请求相关日志
#   - n8n_webhook.log: n8n webhook 相关日志
#
# 注意事项：
#   - 日志文件会自动轮转，避免单个文件过大
#   - 生产环境建议定期备份和清理旧日志文件
#   - 敏感信息（如密码、密钥）不应记录到日志中
# ==========================================================

import os
from pathlib import Path

# ==========================================================
# 项目路径配置
# ==========================================================
# 
# 功能说明：
#   - 定义项目根目录路径，用于定位日志文件等资源
#   - 使用 pathlib.Path 提供跨平台的路径操作
#
# 使用方式：
#   - BASE_DIR: 项目根目录
#   - 日志文件路径: BASE_DIR / 'logs' / 'django.log'
# ==========================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# ==========================================================
# 日志格式化器配置
# ==========================================================
# 
# 功能说明：
#   - 定义不同场景下的日志输出格式
#   - 支持详细、简洁、调试等多种格式
#
# 参数说明：
#   - format: 日志格式字符串，支持以下占位符：
#     * {levelname}: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
#     * {asctime}: 时间戳
#     * {module}: 模块名
#     * {process}: 进程ID
#     * {thread}: 线程ID
#     * {message}: 日志消息
#     * {name}: 日志记录器名称
#     * {pathname}: 文件路径
#     * {lineno}: 行号
#   - style: 格式风格，可选 '{' (str.format) 或 '%' (printf-style)
#
# 使用示例：
#   logger = logging.getLogger('products')
#   logger.info('用户登录', extra={'user_id': 123})
#   # 输出: [2025-01-05 10:30:45] INFO [products] views.py:123 - 用户登录
# ==========================================================

LOGGING = {
    # 日志配置版本，必须设置为 1
    "version": 1,
    
    # 是否禁用已存在的日志记录器
    # False: 保留已存在的日志记录器，只添加新配置
    # True: 禁用所有已存在的日志记录器，只使用此配置
    "disable_existing_loggers": False,
    
    # 日志格式化器配置
    "formatters": {
        # 详细格式 - 包含进程和线程信息，用于调试
        # 使用场景：开发环境、性能分析、并发问题排查
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        
        # 简洁格式 - 只包含基本信息，用于日常监控
        # 使用场景：生产环境、实时监控、日志聚合
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
        
        # 详细格式 - 包含文件路径和行号，用于问题定位
        # 使用场景：错误排查、代码调试、问题追踪
        "detailed": {
            "format": "[{asctime}] {levelname} [{name}] {pathname}:{lineno:d} - {message}",
            "style": "{",
        },
    },
    
    # ==========================================================
    # 日志过滤器配置
    # ==========================================================
    # 
    # 功能说明：
    #   - 对日志记录进行过滤，决定是否处理某条日志
    #   - 支持基于日志级别、调试模式等条件的过滤
    #
    # 使用示例：
    #   logger = logging.getLogger('django')
    #   logger.debug('调试信息')  # 在生产环境不会输出
    # ==========================================================
    
    "filters": {
        # 只在 DEBUG=True 时输出日志
        # 使用场景：开发环境调试信息，生产环境自动禁用
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    
    # ==========================================================
    # 日志处理器配置
    # ==========================================================
    # 
    # 功能说明：
    #   - 定义日志的输出目标（控制台、文件、网络等）
    #   - 支持日志轮转、级别过滤、格式化等功能
    #
    # 参数说明：
    #   - level: 处理器处理的最低日志级别
    #   - class: 处理器类，常用的有：
    #     * logging.StreamHandler: 输出到控制台
    #     * logging.FileHandler: 输出到文件
    #     * logging.handlers.RotatingFileHandler: 文件轮转
    #     * logging.handlers.TimedRotatingFileHandler: 按时间轮转
    #   - formatter: 使用的格式化器名称
    #   - filename: 日志文件路径（文件处理器专用）
    #   - maxBytes: 单个日志文件最大字节数（轮转处理器专用）
    #   - backupCount: 保留的备份文件数量（轮转处理器专用）
    #
    # 使用示例：
    #   # 记录到文件
    #   logger.info('操作完成')
    #   # 输出到 logs/django.log
    # ==========================================================
    
    "handlers": {
        # ----------------------------------------------------------
        # 控制台输出处理器（开发环境）
        # ----------------------------------------------------------
        # 功能说明：将日志输出到控制台，便于开发调试
        # 使用场景：开发环境、本地测试、实时调试
        # 注意事项：生产环境建议关闭或设置为 WARNING 级别
        # ----------------------------------------------------------
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        
        # ----------------------------------------------------------
        # 文件处理器 - 所有日志
        # ----------------------------------------------------------
        # 功能说明：记录所有 INFO 及以上级别的日志到文件
        # 使用场景：应用运行日志、日常监控、问题追踪
        # 日志轮转：达到 100MB 时自动轮转，保留 10 个备份
        # ----------------------------------------------------------
        "file_all": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "maxBytes": 1024 * 1024 * 100,  # 100 MB
            "backupCount": 10,
            "formatter": "detailed",
        },
        
        # ----------------------------------------------------------
        # 文件处理器 - 错误日志
        # ----------------------------------------------------------
        # 功能说明：只记录 ERROR 及以上级别的日志到单独文件
        # 使用场景：错误监控、问题排查、告警触发
        # 日志轮转：达到 50MB 时自动轮转，保留 10 个备份
        # ----------------------------------------------------------
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django_error.log"),
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 10,
            "formatter": "detailed",
        },
        
        # ----------------------------------------------------------
        # 文件处理器 - API 请求日志
        # ----------------------------------------------------------
        # 功能说明：记录 API 请求相关的详细日志，包括 DEBUG 级别
        # 使用场景：API 调试、请求追踪、性能分析
        # 日志轮转：达到 50MB 时自动轮转，保留 10 个备份
        # ----------------------------------------------------------
        "file_api": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "api.log"),
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 10,
            "formatter": "detailed",
        },
        
        # ----------------------------------------------------------
        # 文件处理器 - n8n webhook 日志
        # ----------------------------------------------------------
        # 功能说明：记录 n8n webhook 调用的详细日志，包括 DEBUG 级别
        # 使用场景：n8n 集成调试、webhook 问题排查、数据流追踪
        # 日志轮转：达到 50MB 时自动轮转，保留 10 个备份
        # ----------------------------------------------------------
        "file_n8n": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "n8n_webhook.log"),
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 10,
            "formatter": "detailed",
        },
    },
    
    # ==========================================================
    # 日志记录器配置
    # ==========================================================
    # 
    # 功能说明：
    #   - 为不同的模块和应用配置独立的日志记录器
    #   - 每个记录器可以有自己的日志级别和处理器
    #
    # 参数说明：
    #   - handlers: 使用的处理器列表
    #   - level: 记录器的最低日志级别
    #   - propagate: 是否向上传播日志到父记录器
    #
    # 使用示例：
    #   # 在 views.py 中
    #   import logging
    #   logger = logging.getLogger('products.views')
    #   logger.info('处理请求')
    #   # 日志会输出到 file_api 和 file_n8n 处理器
    # ==========================================================
    
    "loggers": {
        # ----------------------------------------------------------
        # Django 默认日志记录器
        # ----------------------------------------------------------
        # 功能说明：处理 Django 框架自身的日志
        # 使用场景：框架级别的日志、系统事件
        # 输出目标：django.log 和 django_error.log
        # ----------------------------------------------------------
        "django": {
            "handlers": ["file_all", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        
        # ----------------------------------------------------------
        # Django 数据库查询日志
        # ----------------------------------------------------------
        # 功能说明：记录数据库查询的日志
        # 使用场景：数据库性能分析、查询优化
        # 注意事项：生产环境建议设置为 WARNING 或 ERROR，避免记录过多查询
        # 输出目标：django.log
        # ----------------------------------------------------------
        "django.db.backends": {
            "handlers": ["file_all"],
            "level": "WARNING",
            "propagate": False,
        },
        
        # ----------------------------------------------------------
        # Django 请求日志
        # ----------------------------------------------------------
        # 功能说明：记录 HTTP 请求相关的日志
        # 使用场景：请求监控、错误追踪、访问统计
        # 输出目标：django.log 和 django_error.log
        # ----------------------------------------------------------
        "django.request": {
            "handlers": ["file_all", "file_error"],
            "level": "ERROR",
            "propagate": False,
        },
        
        # ----------------------------------------------------------
        # products 应用日志
        # ----------------------------------------------------------
        # 功能说明：处理 products 应用的所有日志
        # 使用场景：业务逻辑日志、功能调试、问题排查
        # 输出目标：django.log、api.log 和 n8n_webhook.log
        # 使用示例：
        #   import logging
        #   logger = logging.getLogger('products')
        #   logger.info('产品创建成功', extra={'product_id': 123})
        # ----------------------------------------------------------
        "products": {
            "handlers": ["file_all", "file_api", "file_n8n"],
            "level": "DEBUG",
            "propagate": False,
        },
        
        # ----------------------------------------------------------
        # products.views 日志记录器
        # ----------------------------------------------------------
        # 功能说明：专门处理 products 应用的视图层日志
        # 使用场景：API 请求日志、webhook 调用日志
        # 输出目标：api.log 和 n8n_webhook.log
        # 使用示例：
        #   import logging
        #   logger = logging.getLogger('products.views')
        #   logger.info('收到 n8n webhook 请求', extra={'product_id': 456})
        # ----------------------------------------------------------
        "products.views": {
            "handlers": ["file_n8n", "file_api"],
            "level": "DEBUG",
            "propagate": False,
        },
        
        # ----------------------------------------------------------
        # Django-Q 日志记录器
        # ----------------------------------------------------------
        # 功能说明：处理 Django-Q 异步任务队列的日志
        # 使用场景：任务执行监控、队列调试、错误追踪
        # 输出目标：django.log
        # 使用示例：
        #   import logging
        #   logger = logging.getLogger('django_q')
        #   logger.info('任务开始执行', extra={'task_id': 'abc123'})
        # ----------------------------------------------------------
        "django_q": {
            "handlers": ["file_all"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

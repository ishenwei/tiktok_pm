# Dockerfile

# 使用官方的 Python 3.11 镜像作为基础
FROM python:3.11-slim

# 设置环境变量，使用无缓冲的 Python 输出，便于查看日志
ENV PYTHONUNBUFFERED 1

# Django settings 模块路径
ENV DJANGO_SETTINGS_MODULE=tiktok_pm_project.settings

# 设置工作目录
WORKDIR /app

# 1. 复制依赖文件并安装依赖
# 使用了 mysqlclient，确保您已经安装了必要的系统依赖
COPY requirements.txt /app/
# 安装依赖时，需要先安装 mysqlclient 的依赖包
RUN apt-get update \
    && apt-get install -y default-libmysqlclient-dev gcc \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove --purge -y gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 2. 复制整个项目代码到容器中
COPY . /app/

# 3. 运行 Django 的收集静态文件命令
# STATIC_ROOT 路径将被收集到 /app/staticfiles/
RUN python manage.py collectstatic --noinput

# 暴露 Gunicorn 监听的端口
EXPOSE 8000

# 启动 Gunicorn 服务器来服务应用
# --workers: 根据 CPU 核数设置，这里使用 3 个工作进程
# --bind 0.0.0.0:8000: 绑定到所有接口
CMD ["gunicorn", "tiktok_pm_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
# 生产环境日志排查指南

## 目录
1. [日志文件位置](#日志文件位置)
2. [日志级别说明](#日志级别说明)
3. [常用日志查看命令](#常用日志查看命令)
4. [常见问题排查](#常见问题排查)
5. [日志配置](#日志配置)
6. [日志分析工具](#日志分析工具)

---

## 日志文件位置

### 1. Django 应用日志

#### 项目日志目录
```
/path/to/your/project/logs/
├── django.log              # Django 主日志（所有 INFO 及以上级别）
├── django_error.log        # Django 错误日志（ERROR 及以上级别）
├── api.log                 # API 请求日志（DEBUG 及以上级别）
└── n8n_webhook.log         # n8n Webhook 专用日志（DEBUG 及以上级别）
```

#### 系统日志目录
```
/var/log/
├── gunicorn/
│   ├── access.log          # Gunicorn 访问日志
│   └── error.log           # Gunicorn 错误日志
├── nginx/
│   ├── access.log          # Nginx 访问日志
│   └── error.log           # Nginx 错误日志
├── syslog                  # 系统日志
└── auth.log                # 认证日志
```

### 2. 云服务日志（如果使用）

- **AWS**: CloudWatch Logs
- **阿里云**: 日志服务 SLS
- **腾讯云**: 云日志服务 CLS

---

## 日志级别说明

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发环境，详细的调试信息 |
| INFO | 一般信息 | 正常运行信息，如请求处理 |
| WARNING | 警告信息 | 潜在问题，但不影响运行 |
| ERROR | 错误信息 | 错误发生，但程序继续运行 |
| CRITICAL | 严重错误 | 严重错误，可能导致程序崩溃 |

---

## 常用日志查看命令

### 1. 实时查看日志

```bash
# 查看所有日志
tail -f /path/to/your/project/logs/django.log

# 查看错误日志
tail -f /path/to/your/project/logs/django_error.log

# 查看多个日志文件
tail -f /path/to/your/project/logs/*.log
```

### 2. 查看最后 N 行

```bash
# 查看最后 100 行
tail -n 100 /path/to/your/project/logs/django.log

# 查看最后 500 行错误日志
tail -n 500 /path/to/your/project/logs/django_error.log
```

### 3. 搜索关键词

```bash
# 搜索特定关键词
grep "ERROR" /path/to/your/project/logs/django.log

# 搜索并显示行号
grep -n "update_product_api" /path/to/your/project/logs/api.log

# 搜索并显示上下文
grep -C 5 "Exception" /path/to/your/project/logs/django_error.log

# 忽略大小写搜索
grep -i "n8n" /path/to/your/project/logs/n8n_webhook.log
```

### 4. 按时间过滤

```bash
# 查看今天的日志
grep "$(date +%Y-%m-%d)" /path/to/your/project/logs/django.log

# 查看最近 1 小时的日志
find /path/to/your/project/logs -name "*.log" -mmin -60 -exec tail -f {} +

# 查看特定时间段的日志
awk '/2025-01-05 10:00/,/2025-01-05 11:00/' /path/to/your/project/logs/django.log
```

### 5. 统计分析

```bash
# 统计错误数量
grep -c "ERROR" /path/to/your/project/logs/django.log

# 统计各类型日志数量
grep -oE "DEBUG|INFO|WARNING|ERROR|CRITICAL" /path/to/your/project/logs/django.log | sort | uniq -c

# 查找最频繁的错误
grep "ERROR" /path/to/your/project/logs/django_error.log | awk '{print $NF}' | sort | uniq -c | sort -rn | head -10
```

### 6. systemd 服务日志

```bash
# 查看服务日志
journalctl -u your-service-name -f

# 查看今天的日志
journalctl -u your-service-name --since today

# 查看最近的日志
journalctl -u your-service-name -n 100

# 搜索特定关键词
journalctl -u your-service-name | grep "ERROR"
```

### 7. Docker 日志

```bash
# 查看容器日志
docker logs -f container_name

# 查看最近 100 行
docker logs --tail 100 container_name

# 查看特定时间段的日志
docker logs --since 2025-01-05T10:00:00 --until 2025-01-05T11:00:00 container_name

# 搜索关键词
docker logs container_name | grep "ERROR"
```

---

## 常见问题排查

### 1. n8n Webhook 回调问题

**检查日志文件：**
- `/path/to/your/project/logs/n8n_webhook.log`
- `/path/to/your/project/logs/api.log`

**关键搜索词：**
```bash
# 搜索 webhook 请求
grep "update_product_api" /path/to/your/project/logs/n8n_webhook.log

# 搜索成功响应
grep "status.*success" /path/to/your/project/logs/n8n_webhook.log

# 搜索错误
grep -i "error\|exception" /path/to/your/project/logs/n8n_webhook.log

# 搜索特定产品
grep "product_id.*1731500998159798308" /path/to/your/project/logs/n8n_webhook.log
```

**关键日志信息：**
- `output_data extracted` - 检查数据是否正确提取
- `create_items called` - 检查是否调用创建函数
- `Created AIContentItem` - 检查是否成功创建记录
- `output_data keys` - 检查可用的字段
- `desc_zh`, `desc_en`, `script_zh`, `script_en`, `voice_zh`, `voice_en`, `img_p_zh`, `img_p_en` - 检查各字段值

### 2. API 请求问题

**检查日志文件：**
- `/path/to/your/project/logs/api.log`
- `/path/to/your/project/logs/django_error.log`

**关键搜索词：**
```bash
# 搜索特定 API 端点
grep "/api/update_product/" /path/to/your/project/logs/api.log

# 搜索 HTTP 状态码
grep "200\|400\|404\|500" /path/to/your/project/logs/api.log

# 搜索请求时间
grep "2025-01-05" /path/to/your/project/logs/api.log
```

### 3. 数据库连接问题

**检查日志文件：**
- `/path/to/your/project/logs/django_error.log`
- `/var/log/gunicorn/error.log`

**关键搜索词：**
```bash
# 搜索数据库错误
grep -i "database\|mysql\|connection" /path/to/your/project/logs/django_error.log

# 搜索超时错误
grep -i "timeout" /path/to/your/project/logs/django_error.log
```

### 4. 性能问题

**检查日志文件：**
- `/path/to/your/project/logs/django.log`
- `/var/log/gunicorn/access.log`

**关键搜索词：**
```bash
# 搜索慢查询
grep -i "slow query\|duration" /path/to/your/project/logs/django.log

# 统计响应时间
awk '{print $NF}' /var/log/gunicorn/access.log | sort -n | tail -10
```

### 5. 内存/资源问题

**检查系统日志：**
```bash
# 查看系统日志
tail -f /var/log/syslog

# 查看 OOM (Out of Memory) 错误
grep -i "out of memory\|oom" /var/log/syslog

# 查看 Gunicorn 重启记录
grep -i "restarting\|killed" /var/log/gunicorn/error.log
```

---

## 日志配置

### 1. 启用日志配置

在 `settings.py` 中添加：

```python
# 导入日志配置
from .logging_config import LOGGING

# 应用日志配置
LOGGING = LOGGING
```

### 2. 创建日志目录

```bash
mkdir -p /path/to/your/project/logs
chmod 755 /path/to/your/project/logs
```

### 3. 配置日志轮转

日志配置中已包含 `RotatingFileHandler`，会自动轮转：
- 单个文件最大 100MB
- 保留最近 10 个备份文件

### 4. 日志级别调整

根据环境调整日志级别：

**开发环境：**
```python
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['products']['level'] = 'DEBUG'
```

**生产环境：**
```python
LOGGING['handlers']['console']['level'] = 'INFO'
LOGGING['loggers']['products']['level'] = 'INFO'
```

---

## 日志分析工具

### 1. Python 日志分析脚本

使用提供的 `analyze_logs.py` 脚本：

```bash
# 运行日志分析工具
python analyze_logs.py

# 功能菜单：
# 1) 查看最近的 Django 主日志
# 2) 查看最近的错误日志
# 3) 查看最近的 API 请求日志
# 4) 查看最近的 n8n Webhook 日志
# 5) 分析错误日志
# 6) 分析 n8n Webhook 日志
# 7) 搜索关键词
# 8) 查看所有日志文件状态
```

### 2. Bash 日志查看脚本

使用提供的 `view_logs.sh` 脚本：

```bash
# 添加执行权限
chmod +x view_logs.sh

# 运行日志查看工具
./view_logs.sh
```

### 3. 在线日志分析工具

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Graylog**
- **Loki + Grafana**

---

## 最佳实践

### 1. 日志管理

- ✅ 定期清理旧日志文件
- ✅ 使用日志轮转防止文件过大
- ✅ 设置合适的日志级别
- ✅ 敏感信息不要记录到日志中
- ✅ 使用结构化日志格式（JSON）

### 2. 日志监控

- ✅ 设置日志告警（错误日志、异常日志）
- ✅ 监控日志文件大小
- ✅ 定期检查日志文件权限
- ✅ 使用集中式日志管理系统

### 3. 问题排查流程

1. **确定问题范围** - 哪个功能出现问题
2. **定位相关日志** - 找到对应的日志文件
3. **搜索关键词** - 使用错误信息、时间戳等搜索
4. **分析日志内容** - 查看错误堆栈、请求参数等
5. **复现问题** - 在测试环境复现
6. **修复问题** - 根据日志信息修复
7. **验证修复** - 检查日志确认问题解决

### 4. 日志安全

- ✅ 不要记录密码、密钥等敏感信息
- ✅ 设置日志文件访问权限（600 或 640）
- ✅ 定期备份重要日志
- ✅ 使用加密传输日志（如果使用远程日志服务器）

---

## 快速参考

### 常用命令速查

```bash
# 实时查看日志
tail -f /path/to/log/file.log

# 查看最后 100 行
tail -n 100 /path/to/log/file.log

# 搜索关键词
grep "keyword" /path/to/log/file.log

# 搜索并显示上下文
grep -C 5 "keyword" /path/to/log/file.log

# 统计出现次数
grep -c "keyword" /path/to/log/file.log

# 查看特定时间段
awk '/start_time/,/end_time/' /path/to/log/file.log

# 查看系统服务日志
journalctl -u service-name -f

# 查看 Docker 日志
docker logs -f container_name
```

### 日志文件路径速查

| 日志类型 | 路径 |
|---------|------|
| Django 主日志 | `/path/to/your/project/logs/django.log` |
| Django 错误日志 | `/path/to/your/project/logs/django_error.log` |
| API 请求日志 | `/path/to/your/project/logs/api.log` |
| n8n Webhook 日志 | `/path/to/your/project/logs/n8n_webhook.log` |
| Gunicorn 访问日志 | `/var/log/gunicorn/access.log` |
| Gunicorn 错误日志 | `/var/log/gunicorn/error.log` |
| Nginx 访问日志 | `/var/log/nginx/access.log` |
| Nginx 错误日志 | `/var/log/nginx/error.log` |

---

## 联系支持

如果遇到无法解决的问题，请收集以下信息：

1. 相关日志文件（最近 100 行）
2. 错误信息截图
3. 复现步骤
4. 系统环境信息（操作系统、Python 版本、Django 版本等）

---

**最后更新：** 2025-01-05

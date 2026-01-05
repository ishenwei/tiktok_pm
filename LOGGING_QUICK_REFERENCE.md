# 生产环境日志快速参考

## 🚨 紧急问题排查 - 快速命令

### 1. n8n Webhook 问题
```bash
# 查看最新的 n8n webhook 日志
tail -100 /path/to/your/project/logs/n8n_webhook.log

# 搜索错误
grep -i "error\|exception" /path/to/your/project/logs/n8n_webhook.log

# 搜索特定产品
grep "product_id.*YOUR_PRODUCT_ID" /path/to/your/project/logs/n8n_webhook.log

# 搜索数据提取信息
grep "output_data" /path/to/your/project/logs/n8n_webhook.log
```

### 2. API 请求问题
```bash
# 查看 API 日志
tail -100 /path/to/your/project/logs/api.log

# 搜索特定端点
grep "/api/update_product/" /path/to/your/project/logs/api.log

# 搜索 HTTP 错误
grep "400\|404\|500" /path/to/your/project/logs/api.log
```

### 3. 应用错误
```bash
# 查看错误日志
tail -100 /path/to/your/project/logs/django_error.log

# 搜索所有错误
grep "ERROR" /path/to/your/project/logs/django.log

# 搜索异常
grep -i "exception\|traceback" /path/to/your/project/logs/django_error.log
```

### 4. 系统服务问题
```bash
# Gunicorn 错误
tail -100 /var/log/gunicorn/error.log

# Nginx 错误
tail -100 /var/log/nginx/error.log

# systemd 服务日志
journalctl -u your-service-name -n 100
```

---

## 📋 日志文件位置

### Django 应用日志
```
/path/to/your/project/logs/
├── django.log              # 主日志
├── django_error.log        # 错误日志
├── api.log                 # API 日志
└── n8n_webhook.log         # n8n Webhook 日志
```

### 系统日志
```
/var/log/
├── gunicorn/
│   ├── access.log
│   └── error.log
├── nginx/
│   ├── access.log
│   └── error.log
├── syslog
└── auth.log
```

---

## 🔍 关键日志信息

### n8n Webhook 日志关键点
- `output_data extracted` - 数据是否正确提取
- `create_items called` - 是否调用创建函数
- `Created AIContentItem` - 是否成功创建记录
- `output_data keys` - 可用的字段
- `desc_zh`, `desc_en`, `script_zh`, `script_en`, `voice_zh`, `voice_en`, `img_p_zh`, `img_p_en` - 各字段值

### API 日志关键点
- 请求时间戳
- HTTP 方法（GET/POST/PUT/DELETE）
- 请求路径
- HTTP 状态码
- 响应时间

### 错误日志关键点
- 错误类型（Exception Name）
- 错误消息
- 堆栈跟踪
- 发生时间
- 相关模块和行号

---

## 🛠️ 实用工具

### 1. Python 日志分析工具
```bash
python analyze_logs.py
```

### 2. Bash 日志查看工具
```bash
./view_logs.sh
```

### 3. 实时监控
```bash
# 监控所有 Django 日志
tail -f /path/to/your/project/logs/*.log

# 监控系统日志
tail -f /var/log/gunicorn/*.log /var/log/nginx/*.log
```

---

## 📊 日志统计命令

```bash
# 统计错误数量
grep -c "ERROR" /path/to/your/project/logs/django.log

# 统计各类型日志
grep -oE "DEBUG|INFO|WARNING|ERROR|CRITICAL" /path/to/your/project/logs/django.log | sort | uniq -c

# 查找最频繁的错误
grep "ERROR" /path/to/your/project/logs/django_error.log | awk '{print $NF}' | sort | uniq -c | sort -rn | head -10

# 统计 API 请求数
grep -c "POST\|GET\|PUT\|DELETE" /path/to/your/project/logs/api.log
```

---

## 🎯 常见问题快速定位

| 问题类型 | 检查日志 | 搜索关键词 |
|---------|---------|-----------|
| n8n webhook 失败 | n8n_webhook.log | error, exception, 500 |
| 数据未保存 | n8n_webhook.log, api.log | Created AIContentItem, create_items |
| API 404 错误 | api.log, nginx/error.log | 404, not found |
| 数据库连接失败 | django_error.log | database, connection, timeout |
| 内存溢出 | syslog, gunicorn/error.log | out of memory, OOM |
| 性能问题 | django.log, gunicorn/access.log | slow, duration, timeout |

---

## 📞 获取帮助

如果问题无法解决，请收集：

1. 相关日志文件（最近 100 行）
2. 错误信息截图
3. 复现步骤
4. 系统环境信息

---

## 📖 完整文档

详细文档请参考：[PRODUCTION_LOGGING_GUIDE.md](./PRODUCTION_LOGGING_GUIDE.md)

---

**最后更新：** 2025-01-05

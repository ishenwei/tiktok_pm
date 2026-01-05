# 日志查看工具使用指南

## 概述

本指南介绍如何使用项目中的日志查看工具来监控、分析和调试 Django 应用程序。项目提供了两个主要的日志查看工具：

1. **analyze_logs.py** - Python 日志分析工具，用于分析和解析应用程序日志
2. **view_docker_logs.sh** - Bash 脚本，用于管理 Docker Compose 环境下的容器日志

## 目录

- [环境要求](#环境要求)
- [analyze_logs.py 使用指南](#analyze_logs_py-使用指南)
- [view_docker_logs.sh 使用指南](#view_docker_logs_sh-使用指南)
- [常见使用场景](#常见使用场景)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

---

## 环境要求

### analyze_logs.py

- Python 3.7+
- Django 应用程序
- 日志文件位于项目目录

### view_docker_logs.sh

- Docker
- Docker Compose
- Linux/Unix 环境（或 WSL on Windows）
- docker-compose.yml 文件

---

## analyze_logs.py 使用指南

### 功能概述

`analyze_logs.py` 是一个功能强大的日志分析工具，提供以下功能：

- 读取和解析日志文件
- 实时监控日志输出
- 搜索特定关键词
- 分析错误和警告
- 统计日志信息
- 导出分析结果

### 基本用法

#### 1. 查看日志文件

```bash
# 查看所有日志
python analyze_logs.py --file logs/django.log

# 查看最近 N 行日志
python analyze_logs.py --file logs/django.log --tail 100

# 实时监控日志
python analyze_logs.py --file logs/django.log --follow
```

#### 2. 搜索日志

```bash
# 搜索包含特定关键词的日志
python analyze_logs.py --file logs/django.log --search "ERROR"

# 搜索多个关键词
python analyze_logs.py --file logs/django.log --search "ERROR,WARNING"

# 不区分大小写搜索
python analyze_logs.py --file logs/django.log --search "error" --ignore-case
```

#### 3. 分析错误

```bash
# 分析所有错误日志
python analyze_logs.py --file logs/django.log --analyze-errors

# 分析特定级别的日志
python analyze_logs.py --file logs/django.log --level ERROR

# 统计日志级别分布
python analyze_logs.py --file logs/django.log --stats
```

#### 4. n8n Webhook 日志分析

```bash
# 分析 n8n webhook 相关日志
python analyze_logs.py --file logs/django.log --n8n-analysis

# 查看最近的 n8n webhook 调用
python analyze_logs.py --file logs/django.log --n8n-recent

# 分析 n8n webhook 错误
python analyze_logs.py --file logs/django.log --n8n-errors
```

### 高级用法

#### 1. 过滤日志

```bash
# 按时间范围过滤
python analyze_logs.py --file logs/django.log --start "2025-01-05 10:00:00" --end "2025-01-05 11:00:00"

# 按模块过滤
python analyze_logs.py --file logs/django.log --module products

# 按日志级别过滤
python analyze_logs.py --file logs/django.log --min-level WARNING
```

#### 2. 导出结果

```bash
# 导出分析结果到文件
python analyze_logs.py --file logs/django.log --analyze-errors --output error_report.txt

# 导出为 JSON 格式
python analyze_logs.py --file logs/django.log --stats --output stats.json --format json
```

#### 3. 组合使用

```bash
# 搜索错误并导出结果
python analyze_logs.py --file logs/django.log --search "ERROR" --output errors.txt

# 实时监控并过滤特定模块
python analyze_logs.py --file logs/django.log --follow --module n8n
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--file` | 指定日志文件路径 | `--file logs/django.log` |
| `--tail` | 显示最后 N 行日志 | `--tail 100` |
| `--follow` | 实时监控日志 | `--follow` |
| `--search` | 搜索关键词 | `--search "ERROR"` |
| `--ignore-case` | 不区分大小写搜索 | `--ignore-case` |
| `--level` | 过滤特定日志级别 | `--level ERROR` |
| `--min-level` | 过滤最低日志级别 | `--min-level WARNING` |
| `--module` | 过滤特定模块 | `--module products` |
| `--start` | 开始时间 | `--start "2025-01-05 10:00:00"` |
| `--end` | 结束时间 | `--end "2025-01-05 11:00:00"` |
| `--analyze-errors` | 分析错误日志 | `--analyze-errors` |
| `--stats` | 显示统计信息 | `--stats` |
| `--n8n-analysis` | 分析 n8n webhook 日志 | `--n8n-analysis` |
| `--n8n-recent` | 查看最近的 n8n 调用 | `--n8n-recent` |
| `--n8n-errors` | 分析 n8n 错误 | `--n8n-errors` |
| `--output` | 输出文件路径 | `--output report.txt` |
| `--format` | 输出格式 (text/json) | `--format json` |

### 使用示例

#### 示例 1: 调试产品更新问题

```bash
# 查看产品相关的错误日志
python analyze_logs.py --file logs/django.log --search "product" --level ERROR

# 查看最近的 n8n webhook 调用
python analyze_logs.py --file logs/django.log --n8n-recent
```

#### 示例 2: 监控生产环境

```bash
# 实时监控错误日志
python analyze_logs.py --file logs/django.log --follow --level ERROR

# 统计日志级别分布
python analyze_logs.py --file logs/django.log --stats
```

#### 示例 3: 生成错误报告

```bash
# 分析所有错误并生成报告
python analyze_logs.py --file logs/django.log --analyze-errors --output daily_error_report.txt

# 导出为 JSON 格式供其他工具使用
python analyze_logs.py --file logs/django.log --stats --output stats.json --format json
```

---

## view_docker_logs.sh 使用指南

### 功能概述

`view_docker_logs.sh` 是一个交互式的 Docker 日志管理工具，提供以下功能：

- 实时查看容器日志
- 查看历史日志
- 搜索日志内容
- 查看容器状态
- 进入容器内部
- 复制日志文件到本地

### 基本用法

#### 1. 运行脚本

```bash
# 确保在 docker-compose.yml 所在目录
cd /path/to/project

# 运行脚本
bash view_docker_logs.sh
```

#### 2. 菜单选项

脚本启动后会显示以下菜单：

```
请选择要查看的日志：
1) Web 服务实时日志 (Django + Gunicorn)
2) Worker 服务实时日志 (Django Q)
3) Nginx 服务实时日志
4) 所有服务实时日志
5) Web 服务最近 100 行
6) Worker 服务最近 100 行
7) Nginx 服务最近 100 行
8) 搜索所有服务日志
9) 查看容器状态
10) 进入容器内部查看日志
11) 从容器复制日志文件到本地
0) 退出
```

### 详细功能说明

#### 1. 实时日志查看

**选项 1-4**: 实时查看日志输出

```bash
# 选择 1: 查看 Web 服务实时日志
# 选择 2: 查看 Worker 服务实时日志
# 选择 3: 查看 Nginx 服务实时日志
# 选择 4: 查看所有服务实时日志
```

**使用场景**:
- 监控应用程序运行状态
- 实时调试问题
- 观察用户请求处理过程

**注意事项**:
- 使用 `Ctrl+C` 退出实时日志查看
- 默认显示最近 50 行日志

#### 2. 历史日志查看

**选项 5-7**: 查看最近 100 行日志

```bash
# 选择 5: 查看 Web 服务最近 100 行
# 选择 6: 查看 Worker 服务最近 100 行
# 选择 7: 查看 Nginx 服务最近 100 行
```

**使用场景**:
- 快速查看最近的错误或警告
- 检查最近的请求处理情况
- 不需要实时监控时的快速查看

#### 3. 日志搜索

**选项 8**: 搜索所有服务日志

```bash
# 选择 8 后，输入要搜索的关键词
# 例如: ERROR, n8n, product, 500
```

**使用场景**:
- 查找特定的错误信息
- 搜索特定用户的操作记录
- 查找特定时间点的日志

**特点**:
- 不区分大小写
- 关键词高亮显示
- 搜索所有服务的日志

#### 4. 容器状态查看

**选项 9**: 查看容器状态

```bash
# 选择 9 查看容器运行状态
```

**输出信息**:
- 容器名称
- 运行状态 (Up/Exited)
- 端口映射
- 运行的命令
- 容器 ID

**使用场景**:
- 检查服务是否正常运行
- 排查容器启动失败问题
- 查看端口映射配置

#### 5. 进入容器

**选项 10**: 进入容器内部

```bash
# 选择 10 后，选择要进入的容器
# 1) web (Django + Gunicorn)
# 2) worker (Django Q)
# 3) nginx
```

**使用场景**:
- 在容器内执行命令
- 查看容器内的文件
- 调试容器内部问题
- 检查环境变量和配置

**注意事项**:
- 使用 `exit` 命令退出容器
- web 和 worker 容器使用 bash shell
- nginx 容器使用 sh shell
- 容器内的修改在重启后会丢失

#### 6. 复制日志文件

**选项 11**: 从容器复制日志文件到本地

```bash
# 选择 11 后，选择要复制日志的容器
# 1) web (Django + Gunicorn) - 复制 /app/logs/
# 2) worker (Django Q) - 复制 /app/logs/
# 3) nginx - 复制 /var/log/nginx/
```

**输出位置**:
- Django 日志: `./docker_logs/logs/`
- Nginx 日志: `./docker_logs/nginx/`

**使用场景**:
- 离线分析日志
- 长期存储日志
- 使用其他工具分析日志
- 分享日志文件

**注意事项**:
- 如果容器内没有相应的日志目录，会提示使用 `docker-compose logs` 命令
- 日志可能通过 Docker 日志驱动输出，而不是文件
- 会自动创建本地日志目录

### 使用示例

#### 示例 1: 调试 API 错误

```bash
# 1. 运行脚本
bash view_docker_logs.sh

# 2. 选择 8 搜索日志
# 3. 输入 "ERROR" 或 "500"
# 4. 查看错误信息

# 5. 如果需要更详细的信息，选择 1 查看 Web 服务实时日志
# 6. 重现问题，观察日志输出
```

#### 示例 2: 监控 n8n Webhook

```bash
# 1. 运行脚本
bash view_docker_logs.sh

# 2. 选择 8 搜索日志
# 3. 输入 "n8n" 或 "webhook"

# 4. 选择 1 查看 Web 服务实时日志
# 5. 触发 n8n webhook，观察日志输出
```

#### 示例 3: 导出日志进行分析

```bash
# 1. 运行脚本
bash view_docker_logs.sh

# 2. 选择 11 复制日志文件
# 3. 选择 1 (web 容器)

# 4. 日志文件复制到 ./docker_logs/logs/
# 5. 使用 analyze_logs.py 分析日志
python analyze_logs.py --file docker_logs/logs/django.log --analyze-errors
```

#### 示例 4: 排查容器启动问题

```bash
# 1. 运行脚本
bash view_docker_logs.sh

# 2. 选择 9 查看容器状态
# 3. 检查容器是否正常运行

# 4. 如果容器未运行，选择 10 进入容器
# 5. 检查配置文件和环境变量
# 6. 手动启动服务，查看错误信息
```

---

## 常见使用场景

### 场景 1: 调试产品更新失败

**问题**: 产品更新后 AI 内容没有保存到数据库

**解决步骤**:

1. 使用 `view_docker_logs.sh` 查看 Web 服务实时日志
2. 触发产品更新操作
3. 搜索日志中的 "ERROR" 或 "Exception"
4. 查看 n8n webhook 相关日志
5. 检查数据库操作日志

```bash
# 方法 1: 使用 view_docker_logs.sh
bash view_docker_logs.sh
# 选择 1 (Web 服务实时日志)
# 触发产品更新
# 观察日志输出

# 方法 2: 使用 analyze_logs.py
python analyze_logs.py --file logs/django.log --n8n-recent
python analyze_logs.py --file logs/django.log --search "update_product" --level ERROR
```

### 场景 2: 监控生产环境

**目标**: 实时监控生产环境的错误和警告

**解决步骤**:

1. 使用 `analyze_logs.py` 实时监控错误日志
2. 设置日志级别过滤
3. 定期生成错误报告

```bash
# 实时监控错误日志
python analyze_logs.py --file logs/django.log --follow --level ERROR

# 或者使用 Docker 日志脚本
bash view_docker_logs.sh
# 选择 1 (Web 服务实时日志)
# 在另一个终端搜索错误
```

### 场景 3: 分析性能问题

**目标**: 找出响应时间慢的请求

**解决步骤**:

1. 查看日志中的请求处理时间
2. 搜索慢查询日志
3. 分析数据库操作日志

```bash
# 搜索慢查询
python analyze_logs.py --file logs/django.log --search "slow" --level WARNING

# 查看数据库操作
python analyze_logs.py --file logs/django.log --module database --level WARNING
```

### 场景 4: 导出日志用于分析

**目标**: 将日志导出到本地进行离线分析

**解决步骤**:

1. 使用 `view_docker_logs.sh` 复制日志文件
2. 使用 `analyze_logs.py` 分析日志
3. 生成分析报告

```bash
# 1. 复制日志文件
bash view_docker_logs.sh
# 选择 11 (复制日志文件)
# 选择 1 (web 容器)

# 2. 分析日志
python analyze_logs.py --file docker_logs/logs/django.log --analyze-errors --output error_report.txt

# 3. 生成统计报告
python analyze_logs.py --file docker_logs/logs/django.log --stats --output stats.json --format json
```

---

## 故障排查

### 问题 1: 无法查看日志

**症状**: 运行 `view_docker_logs.sh` 时提示找不到容器

**可能原因**:
- 容器未启动
- docker-compose.yml 文件不在当前目录
- 容器名称不匹配

**解决方法**:

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 启动容器
docker-compose up -d

# 3. 确认在正确的目录
ls docker-compose.yml

# 4. 检查容器名称
docker ps --format "table {{.Names}}"
```

### 问题 2: 日志文件不存在

**症状**: 运行 `analyze_logs.py` 时提示找不到日志文件

**可能原因**:
- 日志文件路径不正确
- 日志目录不存在
- 日志文件权限问题

**解决方法**:

```bash
# 1. 检查日志文件是否存在
ls -la logs/

# 2. 创建日志目录
mkdir -p logs

# 3. 检查文件权限
chmod 644 logs/django.log

# 4. 使用正确的路径
python analyze_logs.py --file /path/to/logs/django.log
```

### 问题 3: 容器内没有日志文件

**症状**: 使用 `view_docker_logs.sh` 复制日志时提示目录不存在

**可能原因**:
- 日志通过 Docker 日志驱动输出
- 日志目录未挂载到容器
- 日志配置不正确

**解决方法**:

```bash
# 1. 使用 docker-compose logs 命令查看
docker-compose logs web

# 2. 检查 docker-compose.yml 配置
cat docker-compose.yml | grep -A 5 volumes

# 3. 进入容器检查
docker-compose exec web ls -la /app/logs

# 4. 检查日志配置
cat logging_config.py
```

### 问题 4: 搜索不到结果

**症状**: 使用搜索功能时找不到匹配的日志

**可能原因**:
- 关键词拼写错误
- 搜索区分大小写
- 日志格式不匹配

**解决方法**:

```bash
# 1. 使用不区分大小写搜索
python analyze_logs.py --file logs/django.log --search "error" --ignore-case

# 2. 使用部分匹配
python analyze_logs.py --file logs/django.log --search "err"

# 3. 查看原始日志
python analyze_logs.py --file logs/django.log --tail 50

# 4. 检查日志格式
head -20 logs/django.log
```

---

## 最佳实践

### 1. 日志管理

- **定期清理日志**: 设置日志轮转，避免日志文件过大
- **按级别分类**: 使用不同的日志级别记录不同重要性的信息
- **结构化日志**: 使用统一的日志格式，便于解析和分析
- **添加上下文**: 在日志中包含请求 ID、用户 ID 等上下文信息

### 2. 监控策略

- **实时监控关键服务**: 对关键服务设置实时日志监控
- **定期生成报告**: 每天生成错误报告和统计信息
- **设置告警**: 对错误和异常设置告警机制
- **保留历史日志**: 保留一定时间的历史日志用于问题追溯

### 3. 调试技巧

- **从错误开始**: 先查看错误日志，再查看上下文
- **使用时间过滤**: 按时间范围缩小搜索范围
- **结合多个工具**: 使用 `view_docker_logs.sh` 和 `analyze_logs.py` 配合使用
- **记录复现步骤**: 记录问题复现的步骤和时间点

### 4. 性能优化

- **避免过度日志**: 不要记录过多的 DEBUG 级别日志
- **异步日志**: 使用异步日志记录，避免阻塞主线程
- **日志聚合**: 使用日志聚合工具（如 ELK）集中管理日志
- **定期归档**: 定期归档和压缩旧的日志文件

### 5. 安全考虑

- **敏感信息**: 不要在日志中记录密码、密钥等敏感信息
- **访问控制**: 限制日志文件的访问权限
- **日志加密**: 对敏感日志进行加密存储
- **定期审计**: 定期审计日志访问记录

---

## 附录

### A. 日志级别说明

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发和调试阶段 |
| INFO | 一般信息 | 记录应用程序的正常运行状态 |
| WARNING | 警告信息 | 记录潜在的问题 |
| ERROR | 错误信息 | 记录错误，但不影响程序继续运行 |
| CRITICAL | 严重错误 | 记录严重错误，可能导致程序崩溃 |

### B. 常用命令速查

#### analyze_logs.py

```bash
# 查看最近 100 行日志
python analyze_logs.py --file logs/django.log --tail 100

# 实时监控日志
python analyze_logs.py --file logs/django.log --follow

# 搜索错误
python analyze_logs.py --file logs/django.log --search "ERROR"

# 分析错误
python analyze_logs.py --file logs/django.log --analyze-errors

# 统计信息
python analyze_logs.py --file logs/django.log --stats

# n8n webhook 分析
python analyze_logs.py --file logs/django.log --n8n-analysis
```

#### view_docker_logs.sh

```bash
# 运行脚本
bash view_docker_logs.sh

# 直接使用 docker-compose 命令
docker-compose logs -f --tail=50 web
docker-compose logs --tail=100 worker
docker-compose logs | grep "ERROR"
docker-compose ps
```

### C. 相关文档

- [Django 日志配置](logging_config.py)
- [生产环境日志指南](PRODUCTION_LOGGING_GUIDE.md)
- [日志快速参考](LOGGING_QUICK_REFERENCE.md)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Python logging 模块文档](https://docs.python.org/3/library/logging.html)

---

## 联系支持

如果您在使用日志查看工具时遇到问题，请：

1. 查看本文档的故障排查部分
2. 检查相关文档和示例
3. 查看日志文件中的错误信息
4. 联系技术支持团队

---

**文档版本**: 1.0  
**最后更新**: 2025-01-05  
**维护者**: 开发团队

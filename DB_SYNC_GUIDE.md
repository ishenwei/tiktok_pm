# 数据库同步系统完整指南

## 目录

1. [概述与目的](#1-概述与目的)
2. [部署指南](#2-部署指南)
3. [同步操作指南](#3-同步操作指南)
4. [测试指南](#4-测试指南)
5. [故障排除](#5-故障排除)
6. [附录](#6-附录)

---

## 1. 概述与目的

### 1.1 系统功能

数据库同步系统是一个功能强大的数据管理解决方案，支持在远程MySQL数据库和本地MariaDB数据库之间进行无缝切换和双向数据同步。该系统提供以下核心功能：

- **环境切换**: 支持在远程MySQL和本地MariaDB之间无缝切换
- **双向同步**: 支持远程到本地、本地到远程以及双向同步
- **同步模式**: 支持全量同步(FULL)和增量同步(INCREMENTAL)
- **定时任务**: 基于Django Q2的自动定时同步
- **手动触发**: 支持通过管理命令手动触发同步
- **冲突处理**: 提供多种冲突解决策略(REMOTE_WINS/LOCAL_WINS/SKIP/MANUAL)
- **日志记录**: 完整的同步日志和状态追踪
- **实时监控**: 监控数据库连接状态、同步任务进度及数据一致性
- **自动故障排除**: 针对异常情况进行自动troubleshooting

### 1.2 应用场景

#### 场景1: 开发环境使用本地数据库

**需求**: 开发时使用本地数据库，提高开发效率，定期同步远程数据

**配置**:
```bash
DB_ENV=local
DB_SYNC_ENABLED=True
DB_SYNC_INTERVAL=60
DB_SYNC_DIRECTION=REMOTE_TO_LOCAL
DB_SYNC_TYPE=INCREMENTAL
```

**优点**:
- 开发速度快，不受网络影响
- 可以随意修改数据，不影响远程
- 定期同步保持数据更新

#### 场景2: 生产环境使用远程数据库

**需求**: 生产环境使用远程数据库，禁用自动同步

**配置**:
```bash
DB_ENV=remote
DB_SYNC_ENABLED=False
```

**优点**:
- 数据安全，避免意外同步
- 集中管理，便于维护
- 减少网络传输

#### 场景3: 测试环境双向同步

**需求**: 测试环境需要在本地和远程之间双向同步数据

**配置**:
```bash
DB_ENV=local
DB_SYNC_ENABLED=True
DB_SYNC_INTERVAL=30
DB_SYNC_DIRECTION=BOTH
DB_SYNC_TYPE=INCREMENTAL
```

**优点**:
- 数据实时同步
- 两个环境保持一致
- 便于测试数据同步功能

#### 场景4: 数据备份

**需求**: 定期将远程数据库备份到本地

**配置**:
```bash
DB_ENV=local
DB_SYNC_ENABLED=True
DB_SYNC_INTERVAL=120
DB_SYNC_DIRECTION=REMOTE_TO_LOCAL
DB_SYNC_TYPE=FULL
```

**优点**:
- 自动备份，无需手动操作
- 数据完整，全量备份
- 可恢复性强

#### 场景5: 数据迁移

**需求**: 将数据从远程迁移到本地

**配置**:
```bash
DB_ENV=local
DB_SYNC_ENABLED=False
```

**优点**:
- 可控性强，分步操作
- 可以验证数据
- 避免意外覆盖

### 1.3 文档使用指南

本文档分为六个主要章节：

- **第1章**: 系统概述、功能介绍和应用场景
- **第2章**: 详细的部署指南，包括环境要求、安装步骤和配置说明
- **第3章**: 同步操作指南，涵盖同步流程、参数配置和常见操作
- **第4章**: 测试指南，包括测试环境搭建、测试用例设计和自动化测试
- **第5章**: 故障排除，提供常见问题解决方案和错误代码解释
- **第6章**: 附录，包含环境变量列表、管理命令速查和目录结构

建议首次部署时按顺序阅读第2章，日常使用时参考第3章，遇到问题时查阅第5章。

---

## 2. 部署指南

### 2.1 环境要求

#### 系统要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.8+
- **Django**: 5.2+
- **MariaDB**: 10.11+
- **内存**: 最少 2GB，推荐 4GB+
- **磁盘空间**: 最少 10GB 可用空间

#### 网络要求

- 远程数据库服务器可访问
- 网络带宽充足（建议 > 10Mbps）
- 防火墙配置正确（允许数据库端口访问）

#### 权限要求

- Docker执行权限
- 数据库读写权限
- 文件系统读写权限

### 2.2 安装步骤

#### 步骤1: 环境准备

确保已安装Docker和Docker Compose:

```bash
docker --version
docker-compose --version
```

如果未安装，请参考官方文档进行安装。

#### 步骤2: 配置环境变量

编辑项目根目录下的 `.env` 文件，配置以下参数:

##### 数据库环境切换配置

```bash
# 数据库环境选择: remote (远程MySQL) 或 local (本地MariaDB)
DB_ENV=remote

# 远程数据库配置(当DB_ENV=remote时使用)
DB_REMOTE_HOST=192.168.3.17
DB_REMOTE_PORT=3307
DB_REMOTE_NAME=tiktok_products_dev
DB_REMOTE_USER=shenwei
DB_REMOTE_PASSWORD=!Abcde12345

# 本地数据库配置(当DB_ENV=local时使用)
DB_LOCAL_HOST=mariadb
DB_LOCAL_PORT=3306
DB_LOCAL_NAME=tiktok_products_dev
DB_LOCAL_USER=shenwei
DB_LOCAL_PASSWORD=!Abcde12345
```

##### 数据同步配置

```bash
# 是否启用自动数据同步
DB_SYNC_ENABLED=False

# 同步间隔(分钟)
DB_SYNC_INTERVAL=60

# 同步方向: BOTH(双向), REMOTE_TO_LOCAL(远程到本地), LOCAL_TO_REMOTE(本地到远程)
DB_SYNC_DIRECTION=BOTH

# 默认同步类型: FULL(全量), INCREMENTAL(增量)
DB_SYNC_TYPE=INCREMENTAL
```

##### 本地MariaDB配置

```bash
MARIADB_ROOT_PASSWORD=rootpassword
MARIADB_DATABASE=tiktok_products_dev
MARIADB_USER=shenwei
MARIADB_PASSWORD=!Abcde12345
MARIADB_PORT=3306
```

#### 步骤3: 启动本地MariaDB服务

使用Docker Compose启动本地MariaDB服务:

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看MariaDB日志
docker-compose logs -f mariadb
```

#### 步骤4: 初始化数据库

MariaDB容器首次启动时会自动执行初始化脚本 `mariadb/init/01-init.sql`，该脚本会:

- 创建数据库 `tiktok_products`
- 创建同步日志表 `db_sync_log`
- 创建同步配置表 `db_sync_config`
- 插入默认同步配置

如果初始化失败，可以手动执行:

```bash
docker-compose exec -T mariadb mysql -u root -p$MARIADB_ROOT_PASSWORD < mariadb/init/01-init.sql
```

#### 步骤5: 切换数据库环境

##### 切换到本地MariaDB

修改 `.env` 文件:

```bash
DB_ENV=local
```

重启Django服务:

```bash
docker-compose restart web worker
```

##### 切换到远程MySQL

修改 `.env` 文件:

```bash
DB_ENV=remote
```

重启Django服务:

```bash
docker-compose restart web worker
```

#### 步骤6: 启用数据同步

##### 启用自动同步

修改 `.env` 文件:

```bash
DB_SYNC_ENABLED=True
DB_SYNC_INTERVAL=60
DB_SYNC_DIRECTION=BOTH
DB_SYNC_TYPE=INCREMENTAL
```

重启worker服务:

```bash
docker-compose restart worker
```

##### 启用定时任务

在Django容器中执行:

```bash
docker-compose exec web python manage.py sync_scheduler enable
```

查看定时任务状态:

```bash
docker-compose exec web python manage.py sync_scheduler status
```

### 2.3 配置说明

#### 配置层次

1. **全局配置** (环境变量): 控制同步功能的启用和默认行为
2. **表级配置** (数据库表): 为每个表配置独立的同步策略
3. **运行时配置** (命令行参数): 在执行同步时临时覆盖默认配置

#### 环境变量详解

##### DB_ENV

**作用**: 选择当前使用的数据库环境

**可选值**:
- `remote`: 使用远程MySQL数据库
- `local`: 使用本地MariaDB数据库

**使用场景**:
- 开发环境: 使用本地数据库，提高开发效率
- 生产环境: 使用远程数据库，保证数据安全
- 测试环境: 可根据需要切换

##### DB_SYNC_ENABLED

**作用**: 控制是否启用数据同步功能

**可选值**:
- `True`: 启用数据同步
- `False`: 禁用数据同步

**使用建议**:
- 开发阶段: 可根据需要启用或禁用
- 生产环境: 建议禁用，避免意外同步
- 测试环境: 根据测试需求配置

##### DB_SYNC_INTERVAL

**作用**: 设置自动同步的时间间隔

**单位**: 分钟

**默认值**: 60

**使用建议**:
- 数据变化频繁: 使用较短的间隔(5-15分钟)
- 数据变化较少: 使用较长的间隔(60-120分钟)
- 实时性要求高: 使用短间隔(1-5分钟)
- 资源受限: 使用长间隔(120分钟以上)

##### DB_SYNC_DIRECTION

**作用**: 设置默认的同步方向

**可选值**:
- `BOTH`: 双向同步(默认)
- `REMOTE_TO_LOCAL`: 仅从远程同步到本地
- `LOCAL_TO_REMOTE`: 仅从本地同步到远程

**使用场景**:
- `BOTH`: 两个环境都需要更新，保持数据一致
- `REMOTE_TO_LOCAL`: 本地作为远程的备份或只读副本
- `LOCAL_TO_REMOTE`: 本地作为主库，远程作为备份

##### DB_SYNC_TYPE

**作用**: 设置默认的同步类型

**可选值**:
- `FULL`: 全量同步
- `INCREMENTAL`: 增量同步(默认)

**使用建议**:
- 首次同步: 使用全量同步
- 日常同步: 使用增量同步，提高效率
- 数据修复: 使用全量同步确保一致性

#### 表级配置

##### db_sync_config 表结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | int | 主键 |
| table_name | varchar(100) | 表名(唯一) |
| sync_enabled | tinyint(1) | 是否启用同步(1:启用, 0:禁用) |
| sync_type | enum | 同步类型(FULL/INCREMENTAL) |
| sync_direction | enum | 同步方向(BOTH/REMOTE_TO_LOCAL/LOCAL_TO_REMOTE) |
| last_sync_time | datetime | 最后同步时间 |
| last_sync_position | varchar(255) | 最后同步位置(增量同步用) |
| priority | int | 同步优先级(数字越大优先级越高) |
| conflict_resolution | enum | 冲突解决策略(REMOTE_WINS/LOCAL_WINS/SKIP/MANUAL) |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

##### 配置示例

启用产品表的全量同步:

```sql
UPDATE db_sync_config 
SET 
    sync_enabled = 1,
    sync_type = 'FULL',
    sync_direction = 'BOTH',
    priority = 100,
    conflict_resolution = 'REMOTE_WINS'
WHERE table_name = 'products';
```

禁用某个表的同步:

```sql
UPDATE db_sync_config 
SET sync_enabled = 0 
WHERE table_name = 'temp_table';
```

配置只读同步:

```sql
UPDATE db_sync_config 
SET 
    sync_direction = 'REMOTE_TO_LOCAL',
    conflict_resolution = 'REMOTE_WINS'
WHERE table_name = 'reference_data';
```

设置同步优先级:

```sql
-- 优先同步重要表
UPDATE db_sync_config 
SET priority = 100 
WHERE table_name IN ('products', 'orders');

-- 最后同步辅助表
UPDATE db_sync_config 
SET priority = 10 
WHERE table_name IN ('logs', 'temp_data');
```

### 2.4 部署验证

#### 验证Docker服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 应该看到以下服务正在运行:
# - web (Django应用)
# - worker (Django Q worker)
# - mariadb (本地数据库)
# - redis (缓存和任务队列)
```

#### 验证数据库连接

```bash
# 连接到本地数据库
docker-compose exec web python manage.py dbshell

# 执行简单查询
SELECT 1;

# 退出
exit
```

#### 验证同步表

```bash
# 连接到数据库
docker-compose exec web python manage.py dbshell

# 查看同步配置表
SELECT * FROM db_sync_config;

# 查看同步日志表
SELECT * FROM db_sync_log;

# 退出
exit
```

#### 验证定时任务

```bash
# 查看定时任务状态
docker-compose exec web python manage.py sync_scheduler status

# 应该显示任务已启用
```

#### 执行测试同步

```bash
# 执行手动同步测试
docker-compose exec web python manage.py sync_db --verbose

# 检查同步日志
docker-compose exec web python manage.py dbshell
SELECT * FROM db_sync_log ORDER BY start_time DESC LIMIT 1;
```

---

## 3. 同步操作指南

### 3.1 同步流程

#### 全量同步流程

1. **准备阶段**
   - 检查数据库连接
   - 验证表结构兼容性
   - 锁定目标表（防止并发修改）

2. **数据传输**
   - 从源数据库读取所有数据
   - 批量传输到目标数据库
   - 记录同步进度

3. **数据验证**
   - 比较源和目标的数据量
   - 验证数据完整性
   - 记录同步结果

4. **清理阶段**
   - 解锁目标表
   - 更新同步配置
   - 记录同步日志

#### 增量同步流程

1. **准备阶段**
   - 检查数据库连接
   - 读取上次同步位置
   - 查询变更数据

2. **数据传输**
   - 从源数据库读取变更数据（新增、更新、删除）
   - 批量传输到目标数据库
   - 更新同步位置

3. **冲突处理**
   - 检测数据冲突
   - 应用冲突解决策略
   - 记录冲突信息

4. **清理阶段**
   - 更新同步配置
   - 记录同步日志
   - 清理临时数据

#### 双向同步流程

1. **第一轮同步（远程到本地）**
   - 执行远程到本地同步
   - 处理冲突
   - 记录同步结果

2. **第二轮同步（本地到远程）**
   - 执行本地到远程同步
   - 处理冲突
   - 记录同步结果

3. **最终验证**
   - 比较两端数据
   - 验证数据一致性
   - 生成同步报告

### 3.2 参数配置

#### 手动同步命令参数

```bash
python manage.py sync_db [options]
```

**可用参数**:

- `--type`: 同步类型 (FULL/INCREMENTAL)
- `--direction`: 同步方向 (BOTH/REMOTE_TO_LOCAL/LOCAL_TO_REMOTE)
- `--table`: 指定同步的表名
- `--verbose`: 显示详细输出
- `--dry-run`: 模拟执行，不实际修改数据

#### 定时任务管理命令

```bash
# 启用定时任务
python manage.py sync_scheduler enable

# 禁用定时任务
python manage.py sync_scheduler disable

# 查看任务状态
python manage.py sync_scheduler status

# 重启定时任务
python manage.py sync_scheduler restart
```

#### 冲突解决策略

##### REMOTE_WINS (远程优先)

**说明**: 当数据冲突时，保留远程数据库的数据

**适用场景**:
- 远程数据库为主库
- 本地数据库作为只读副本
- 需要确保远程数据的权威性

**配置**:
```sql
UPDATE db_sync_config 
SET conflict_resolution = 'REMOTE_WINS' 
WHERE table_name = 'products';
```

##### LOCAL_WINS (本地优先)

**说明**: 当数据冲突时，保留本地数据库的数据

**适用场景**:
- 本地数据库为主库
- 远程数据库作为备份
- 本地进行数据修改后需要同步到远程

**配置**:
```sql
UPDATE db_sync_config 
SET conflict_resolution = 'LOCAL_WINS' 
WHERE table_name = 'products';
```

##### SKIP (跳过冲突)

**说明**: 当数据冲突时，跳过该记录，不进行同步

**适用场景**:
- 需要手动处理冲突
- 避免数据覆盖
- 数据独立性要求高

**配置**:
```sql
UPDATE db_sync_config 
SET conflict_resolution = 'SKIP' 
WHERE table_name = 'user_settings';
```

##### MANUAL (手动处理)

**说明**: 当数据冲突时，记录冲突信息，需要手动处理

**适用场景**:
- 需要人工审核冲突
- 复杂的数据合并场景
- 需要保留双方数据

**配置**:
```sql
UPDATE db_sync_config 
SET conflict_resolution = 'MANUAL' 
WHERE table_name = 'orders';
```

### 3.3 常见操作

#### 手动触发同步

##### 同步所有表

```bash
# 使用默认配置同步
docker-compose exec web python manage.py sync_db

# 指定同步类型和方向
docker-compose exec web python manage.py sync_db --type INCREMENTAL --direction BOTH

# 显示详细输出
docker-compose exec web python manage.py sync_db --verbose
```

##### 同步指定表

```bash
docker-compose exec web python manage.py sync_db --table products
```

##### 全量同步

```bash
docker-compose exec web python manage.py sync_db --type FULL
```

##### 组合使用

```bash
# 全量同步products表，从远程到本地
docker-compose exec web python manage.py sync_db --table products --type FULL --direction REMOTE_TO_LOCAL --verbose

# 增量同步所有表，双向同步
docker-compose exec web python manage.py sync_db --type INCREMENTAL --direction BOTH --verbose
```

#### 定时任务管理

##### 启用定时任务

```bash
docker-compose exec web python manage.py sync_scheduler enable
```

**输出示例**:
```
配置信息:
  - 同步间隔: 60分钟
  - 同步方向: BOTH
  - 同步类型: INCREMENTAL
数据库同步定时任务已启用
任务将每60分钟自动执行一次
```

##### 禁用定时任务

```bash
docker-compose exec web python manage.py sync_scheduler disable
```

**输出示例**:
```
数据库同步定时任务已禁用
```

##### 查看任务状态

```bash
docker-compose exec web python manage.py sync_scheduler status
```

**输出示例**:
```
数据库同步定时任务状态:
==================================================
状态: 已启用
调度类型: MINUTES
执行间隔: 60 分钟
下次执行: 2026-01-06 15:30:00+00:00
上次执行: 2026-01-06 14:30:00+00:00
成功次数: 10
失败次数: 0
==================================================
```

##### 重启定时任务

```bash
docker-compose exec web python manage.py sync_scheduler restart
```

**输出示例**:
```
重启数据库同步定时任务...
数据库同步定时任务已重启
```

#### 数据库切换

##### 切换到本地数据库

1. 修改 `.env` 文件:
```bash
DB_ENV=local
```

2. 重启服务:
```bash
docker-compose restart web worker
```

3. 验证连接:
```bash
docker-compose exec web python manage.py dbshell
```

##### 切换到远程数据库

1. 修改 `.env` 文件:
```bash
DB_ENV=remote
```

2. 重启服务:
```bash
docker-compose restart web worker
```

3. 验证连接:
```bash
docker-compose exec web python manage.py dbshell
```

#### 查看同步日志

##### 通过数据库查询

```bash
docker-compose exec web python manage.py dbshell
```

```sql
-- 查看最近的同步记录
SELECT * FROM db_sync_log ORDER BY start_time DESC LIMIT 10;

-- 查看失败的同步记录
SELECT * FROM db_sync_log WHERE status = 'FAILED' ORDER BY start_time DESC;

-- 查看特定表的同步记录
SELECT * FROM db_sync_log WHERE table_name = 'products' ORDER BY start_time DESC;

-- 统计同步成功率
SELECT 
    status,
    COUNT(*) as count,
    AVG(duration) as avg_duration
FROM db_sync_log 
GROUP BY status;
```

##### 通过Django Admin

1. 登录Django Admin
2. 进入"Database Sync Logs"页面
3. 查看和管理同步日志

#### 配置同步表

编辑 `db_sync_config` 表来配置需要同步的表:

```sql
-- 启用某个表的同步
UPDATE db_sync_config SET sync_enabled = 1 WHERE table_name = 'products';

-- 禁用某个表的同步
UPDATE db_sync_config SET sync_enabled = 0 WHERE table_name = 'products';

-- 修改同步类型
UPDATE db_sync_config SET sync_type = 'FULL' WHERE table_name = 'categories';

-- 修改同步方向
UPDATE db_sync_config SET sync_direction = 'REMOTE_TO_LOCAL' WHERE table_name = 'products';

-- 修改冲突解决策略
UPDATE db_sync_config SET conflict_resolution = 'REMOTE_WINS' WHERE table_name = 'products';
```

### 3.4 注意事项

#### 数据安全

1. **备份重要数据**: 在执行全量同步前，建议先备份目标数据库
2. **测试环境验证**: 在生产环境执行同步前，先在测试环境验证
3. **监控同步过程**: 使用 `--verbose` 参数查看详细同步过程
4. **检查同步日志**: 同步完成后，检查日志确认同步成功

#### 性能优化

1. **使用增量同步**: 日常同步使用增量同步，减少数据传输量
2. **合理设置同步间隔**: 根据数据变化频率调整同步间隔
3. **配置表优先级**: 优先同步重要表，最后同步辅助表
4. **批量操作**: 使用批量操作减少网络往返

#### 冲突处理

1. **明确数据权威性**: 根据业务需求选择合适的冲突解决策略
2. **重要数据手动处理**: 对重要数据使用 MANUAL 策略，人工审核
3. **记录冲突信息**: 定期检查冲突记录，分析冲突原因
4. **优化同步策略**: 根据冲突情况调整同步策略

#### 监控和维护

1. **定期检查同步日志**: 每天检查同步日志，及时发现失败
2. **监控系统资源**: 监控CPU、内存、磁盘使用情况
3. **清理历史日志**: 定期清理旧的同步日志，避免占用过多空间
4. **更新配置**: 根据业务变化及时更新同步配置

---

## 4. 测试指南

### 4.1 测试环境搭建

#### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.8+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

#### 测试框架结构

```
db_sync_tests/
├── __init__.py
├── test_framework.py          # 测试框架基础类
├── monitor.py                 # 实时监控系统
├── troubleshooter.py          # 自动故障排除
├── report_generator.py        # 测试报告生成器
├── test_deployment.py         # 数据库部署测试
├── test_sync.py              # 数据同步测试
├── test_boundary.py          # 边界情况测试
└── management/
    └── commands/
        └── run_db_sync_tests.py  # Django管理命令
```

#### 启动测试环境

```bash
# 启动所有服务
docker-compose up -d

# 验证服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 配置测试数据库

编辑 `.env` 文件，配置测试数据库:

```bash
DB_ENV=local
DB_SYNC_ENABLED=True
DB_SYNC_INTERVAL=30
DB_SYNC_DIRECTION=BOTH
DB_SYNC_TYPE=INCREMENTAL
```

### 4.2 测试用例设计

#### 测试类型

##### 1. 数据库部署测试 (deployment)

测试数据库环境的正确部署和配置：

- **DatabaseDeploymentTest**: 测试Docker服务状态、MariaDB容器状态、数据库连接、初始化、同步表和配置
- **DatabaseEnvironmentSwitchTest**: 测试环境变量配置、远程和本地数据库配置、环境切换功能
- **DatabasePerformanceTest**: 测试连接速度、查询性能和并发连接

##### 2. 数据同步测试 (sync)

测试数据同步功能的正确性和性能：

- **FullSyncTest**: 测试全量同步功能
  - 远程到本地全量同步
  - 本地到远程全量同步
  - 全量同步数据完整性
  - 全量同步性能

- **IncrementalSyncTest**: 测试增量同步功能
  - 增量同步新增数据
  - 增量同步更新数据
  - 增量同步删除数据
  - 增量同步性能
  - 增量同步日志记录

- **BidirectionalSyncTest**: 测试双向同步功能
  - 双向同步数据一致性
  - 双向同步冲突解决
  - 双向同步顺序

- **SyncLogTest**: 测试同步日志功能
  - 同步日志创建
  - 同步日志更新
  - 同步日志查询
  - 同步日志错误处理

##### 3. 边界情况测试 (boundary)

测试各种异常和边界场景：

- **NetworkFluctuationTest**: 测试网络波动场景
  - 网络超时
  - 网络延迟
  - 网络断开
  - 网络恢复

- **DataConflictTest**: 测试数据冲突场景
  - 主键冲突
  - 更新冲突
  - 删除冲突
  - 冲突解决策略

- **AbnormalInterruptionTest**: 测试异常中断场景
  - 用户中断同步
  - 系统中断同步
  - 异常中断同步
  - 中断后恢复同步

- **ConcurrentSyncTest**: 测试并发同步场景
  - 并发全量同步
  - 并发增量同步
  - 并发双向同步
  - 并发同步锁定

- **LargeDataSyncTest**: 测试大数据量同步场景
  - 大数据量全量同步
  - 大数据量增量同步
  - 大数据量同步性能
  - 大数据量同步内存使用

### 4.3 自动化测试执行

#### 方法1: 使用Django管理命令

```bash
# 运行所有测试
python manage.py run_db_sync_tests

# 运行特定类型的测试
python manage.py run_db_sync_tests --test-type deployment
python manage.py run_db_sync_tests --test-type sync
python manage.py run_db_sync_tests --test-type boundary

# 运行特定的测试用例
python manage.py run_db_sync_tests --test-name FullSyncTest

# 启用实时监控
python manage.py run_db_sync_tests --monitor

# 启用自动修复
python manage.py run_db_sync_tests --auto-fix

# 详细输出
python manage.py run_db_sync_tests --verbose

# 指定输出目录
python manage.py run_db_sync_tests --output-dir custom_reports

# 指定报告格式
python manage.py run_db_sync_tests --report-format html
python manage.py run_db_sync_tests --report-format json
python manage.py run_db_sync_tests --report-format markdown

# 设置超时时间
python manage.py run_db_sync_tests --timeout 1200
```

#### 方法2: 使用运行脚本

```bash
# 运行所有测试
python run_tests.py

# 运行特定类型的测试
python run_tests.py --type deployment
python run_tests.py --type sync
python run_tests.py --type boundary

# 运行特定的测试用例
python run_tests.py --name FullSyncTest

# 启用实时监控
python run_tests.py --monitor

# 启用自动修复
python run_tests.py --auto-fix

# 详细输出
python run_tests.py --verbose
```

### 4.4 结果验证方法

#### 测试报告

测试框架会生成以下格式的报告：

1. **HTML报告**: 交互式HTML报告，包含详细的测试结果和图表
2. **JSON报告**: 机器可读的JSON格式报告
3. **Markdown报告**: Markdown格式的报告，适合文档集成

报告默认保存在 `test_reports/` 目录下，文件名格式为 `test_report_YYYYMMDD_HHMMSS.格式`。

#### 实时监控

启用实时监控后，测试框架会：

- 监控数据库连接池状态
- 监控同步任务进度
- 监控系统资源使用（CPU、内存、磁盘）
- 实时显示监控指标

#### 自动故障排除

启用自动修复后，测试框架会：

- 自动检测常见问题
- 尝试自动修复检测到的问题
- 记录修复历史
- 提供无法自动修复问题的解决方案建议

#### 测试结果

测试完成后，会显示以下信息：

- 总测试数量
- 通过的测试数量
- 失败的测试数量
- 跳过的测试数量
- 总耗时
- 成功率

如果测试失败，会显示详细的错误信息和堆栈跟踪。

#### 性能基准

以下是一些性能基准参考：

- 全量同步速度: > 10 行/秒
- 增量同步速度: > 50 行/秒
- 数据库连接时间: < 5 秒
- 查询响应时间: < 1 秒
- 内存使用增加: < 500 MB（大数据量测试）

### 4.5 扩展测试

如需添加新的测试用例：

1. 在相应的测试文件中创建新的测试类，继承自 `BaseTest`
2. 实现 `setup()`, `execute()`, 和 `teardown()` 方法
3. 在 `run_db_sync_tests.py` 中注册新的测试类
4. 运行测试验证

示例：

```python
from .test_framework import BaseTest

class MyCustomTest(BaseTest):
    def setup(self):
        self.logger.info("设置测试环境")
    
    def execute(self):
        self.logger.info("执行测试")
        # 添加测试逻辑
    
    def teardown(self):
        self.logger.info("清理测试环境")
```

---

## 5. 故障排除

### 5.1 常见问题及解决方案

#### 问题1: 同步失败，提示连接超时

**原因**: 网络连接问题或数据库不可达

**解决方案**:
1. 检查网络连接
2. 验证数据库地址和端口
3. 检查防火墙设置
4. 增加连接超时时间

**排查步骤**:
```bash
# 测试网络连接
ping $DB_REMOTE_HOST

# 测试数据库端口
telnet $DB_REMOTE_HOST $DB_REMOTE_PORT

# 查看数据库日志
docker-compose logs mariadb
```

#### 问题2: 同步后数据不一致

**原因**: 冲突解决策略不当或同步顺序问题

**解决方案**:
1. 检查冲突解决策略
2. 使用全量同步重新同步
3. 检查表配置的优先级
4. 验证数据完整性

**排查步骤**:
```sql
-- 查看同步日志
SELECT * FROM db_sync_log WHERE status = 'FAILED' ORDER BY start_time DESC;

-- 查看冲突记录
SELECT * FROM db_sync_log WHERE error_message LIKE '%conflict%';

-- 验证数据一致性
-- 比较本地和远程的数据量
```

#### 问题3: 定时任务未执行

**原因**: Worker服务未运行或定时任务未启用

**解决方案**:
1. 检查Worker服务状态: `docker-compose ps worker`
2. 查看Worker日志: `docker-compose logs worker`
3. 确认定时任务已启用: `python manage.py sync_scheduler status`
4. 重启Worker服务: `docker-compose restart worker`

**排查步骤**:
```bash
# 检查Worker状态
docker-compose ps worker

# 查看Worker日志
docker-compose logs worker

# 查看定时任务状态
docker-compose exec web python manage.py sync_scheduler status

# 重启Worker
docker-compose restart worker
```

#### 问题4: 同步速度慢

**原因**: 数据量大或网络带宽不足

**解决方案**:
1. 使用增量同步
2. 增加同步间隔
3. 优化数据库查询
4. 增加网络带宽
5. 分批同步数据

**优化建议**:
```bash
# 使用增量同步
python manage.py sync_db --type INCREMENTAL

# 优化数据库索引
CREATE INDEX idx_updated_at ON products(updated_at);

# 调整同步间隔
DB_SYNC_INTERVAL=120
```

#### 问题5: 内存占用过高

**原因**: 同步数据量大或并发同步过多

**解决方案**:
1. 减少同步间隔
2. 限制同步的表数量
3. 使用增量同步
4. 增加系统内存
5. 优化同步逻辑

**优化建议**:
```bash
# 查看内存使用
docker stats

# 增加Docker内存限制
# 在docker-compose.yml中添加:
services:
  web:
    deploy:
      resources:
        limits:
          memory: 2G
```

### 5.2 错误代码解释

#### 数据库连接错误

| 错误代码 | 说明 | 解决方案 |
|---------|------|---------|
| DB_CONN_001 | 无法连接到数据库 | 检查数据库地址、端口、用户名、密码 |
| DB_CONN_002 | 连接超时 | 检查网络连接，增加超时时间 |
| DB_CONN_003 | 认证失败 | 检查用户名和密码 |
| DB_CONN_004 | 数据库不存在 | 检查数据库名称，创建数据库 |

#### 同步错误

| 错误代码 | 说明 | 解决方案 |
|---------|------|---------|
| SYNC_001 | 表结构不匹配 | 检查表结构，确保字段类型一致 |
| SYNC_002 | 主键冲突 | 检查冲突解决策略，使用合适的策略 |
| SYNC_003 | 数据类型不匹配 | 检查数据类型，进行类型转换 |
| SYNC_004 | 外键约束失败 | 检查外键关系，确保引用完整性 |
| SYNC_005 | 同步中断 | 检查网络连接，重新执行同步 |

#### 配置错误

| 错误代码 | 说明 | 解决方案 |
|---------|------|---------|
| CFG_001 | 环境变量未设置 | 检查.env文件，设置所有必需的环境变量 |
| CFG_002 | 配置值无效 | 检查配置值，确保在有效范围内 |
| CFG_003 | 表配置不存在 | 检查db_sync_config表，添加表配置 |
| CFG_004 | 同步方向无效 | 检查sync_direction，使用有效的值 |

#### 系统错误

| 错误代码 | 说明 | 解决方案 |
|---------|------|---------|
| SYS_001 | 磁盘空间不足 | 清理磁盘空间，增加存储容量 |
| SYS_002 | 内存不足 | 增加系统内存，优化内存使用 |
| SYS_003 | CPU使用率过高 | 优化同步逻辑，减少CPU使用 |
| SYS_004 | 权限不足 | 检查文件和数据库权限 |

### 5.3 故障处理流程

#### MariaDB容器无法启动

**症状**: `docker-compose up -d mariadb` 失败

**排查步骤**:
1. 查看日志: `docker-compose logs mariadb`
2. 检查端口占用: `netstat -tuln | grep 3306`
3. 检查数据卷权限: `ls -la /var/lib/docker/volumes/`
4. 验证环境变量配置

**解决方案**:
```bash
# 停止并删除容器
docker-compose down

# 删除数据卷(谨慎操作)
docker volume rm tiktok_pm_mariadb_data

# 重新启动
docker-compose up -d mariadb
```

#### 同步日志表不存在

**症状**: 同步时提示表不存在

**排查步骤**:
1. 检查初始化脚本是否执行
2. 查看MariaDB日志
3. 手动执行初始化脚本

**解决方案**:
```bash
# 手动执行初始化脚本
docker-compose exec -T mariadb mysql -u root -p$MARIADB_ROOT_PASSWORD < mariadb/init/01-init.sql
```

#### Django Q任务堆积

**症状**: 同步任务执行延迟

**排查步骤**:
1. 查看任务队列: `docker-compose exec web python manage.py qinfo`
2. 检查Worker数量
3. 查看Worker日志

**解决方案**:
```bash
# 增加Worker数量
# 修改docker-compose.yml中的workers配置
# 或在settings.py中增加Q_CLUSTER的workers数量

# 清空任务队列
docker-compose exec web python manage.py qclear
```

#### 数据库连接池耗尽

**症状**: 提示连接数过多

**排查步骤**:
1. 查看当前连接数
2. 检查连接池配置
3. 查看是否有连接泄漏

**解决方案**:
```sql
-- 查看当前连接数
SHOW PROCESSLIST;

-- 增加最大连接数
SET GLOBAL max_connections = 500;

-- 优化连接池配置
# 在settings.py中调整CONN_MAX_AGE
```

#### 同步冲突无法解决

**症状**: 同步日志显示大量冲突

**排查步骤**:
1. 查看冲突详情
2. 分析冲突原因
3. 检查数据修改历史

**解决方案**:
```sql
-- 查看冲突记录
SELECT * FROM db_sync_log WHERE error_message LIKE '%conflict%';

-- 修改冲突解决策略
UPDATE db_sync_config 
SET conflict_resolution = 'MANUAL' 
WHERE table_name = 'problem_table';

-- 手动处理冲突数据
```

### 5.4 监控和日志

#### 关键监控指标

- 同步成功率
- 同步耗时
- 数据一致性
- 系统资源使用率

#### 监控方法

1. 定期检查同步日志
2. 监控Django Q任务队列
3. 查看数据库性能指标
4. 监控容器资源使用

#### 日志位置

- Docker日志: `docker-compose logs [service]`
- 同步日志: `db_sync_log` 表
- Django日志: 应用日志文件
- MariaDB日志: `/var/log/mysql/`

#### 日志查询示例

```sql
-- 查看最近的同步记录
SELECT * FROM db_sync_log ORDER BY start_time DESC LIMIT 10;

-- 查看失败的同步记录
SELECT * FROM db_sync_log WHERE status = 'FAILED' ORDER BY start_time DESC;

-- 查看特定表的同步记录
SELECT * FROM db_sync_log WHERE table_name = 'products' ORDER BY start_time DESC;

-- 统计同步成功率
SELECT 
    status,
    COUNT(*) as count,
    AVG(duration) as avg_duration
FROM db_sync_log 
GROUP BY status;

-- 查看错误信息
SELECT * FROM db_sync_log WHERE error_message IS NOT NULL;
```

---

## 6. 附录

### 6.1 环境变量完整列表

```bash
# 数据库环境
DB_ENV=remote

# 远程数据库配置
DB_REMOTE_HOST=192.168.3.17
DB_REMOTE_PORT=3307
DB_REMOTE_NAME=tiktok_products_dev
DB_REMOTE_USER=shenwei
DB_REMOTE_PASSWORD=!Abcde12345

# 本地数据库配置
DB_LOCAL_HOST=mariadb
DB_LOCAL_PORT=3306
DB_LOCAL_NAME=tiktok_products_dev
DB_LOCAL_USER=shenwei
DB_LOCAL_PASSWORD=!Abcde12345

# 数据同步配置
DB_SYNC_ENABLED=False
DB_SYNC_INTERVAL=60
DB_SYNC_DIRECTION=BOTH
DB_SYNC_TYPE=INCREMENTAL

# MariaDB配置
MARIADB_ROOT_PASSWORD=rootpassword
MARIADB_DATABASE=tiktok_products_dev
MARIADB_USER=shenwei
MARIADB_PASSWORD=!Abcde12345
MARIADB_PORT=3306
```

### 6.2 管理命令速查

```bash
# 手动同步
python manage.py sync_db [options]

# 定时任务管理
python manage.py sync_scheduler enable
python manage.py sync_scheduler disable
python manage.py sync_scheduler status
python manage.py sync_scheduler restart

# Django Q管理
python manage.py qinfo          # 查看队列信息
python manage.py qclear         # 清空队列
python manage.py qcluster       # 启动worker

# 数据库操作
python manage.py dbshell        # 进入数据库shell
python manage.py migrate        # 执行数据库迁移
python manage.py createsuperuser  # 创建超级用户
```

### 6.3 数据库操作速查

```sql
-- 查看同步配置
SELECT * FROM db_sync_config;

-- 查看同步日志
SELECT * FROM db_sync_log ORDER BY start_time DESC LIMIT 10;

-- 启用表同步
UPDATE db_sync_config SET sync_enabled = 1 WHERE table_name = 'table_name';

-- 禁用表同步
UPDATE db_sync_config SET sync_enabled = 0 WHERE table_name = 'table_name';

-- 修改同步类型
UPDATE db_sync_config SET sync_type = 'FULL' WHERE table_name = 'table_name';

-- 修改同步方向
UPDATE db_sync_config SET sync_direction = 'BOTH' WHERE table_name = 'table_name';

-- 修改冲突策略
UPDATE db_sync_config SET conflict_resolution = 'REMOTE_WINS' WHERE table_name = 'table_name';

-- 设置同步优先级
UPDATE db_sync_config SET priority = 100 WHERE table_name = 'table_name';

-- 查看数据库连接
SHOW PROCESSLIST;

-- 查看表结构
DESCRIBE table_name;

-- 查看表索引
SHOW INDEX FROM table_name;

-- 查看数据库大小
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'tiktok_products_dev'
GROUP BY table_schema;
```

### 6.4 目录结构

```
tiktok_pm/
├── .env                          # 环境变量配置
├── docker-compose.yml            # Docker Compose配置
├── mariadb/
│   └── init/
│       └── 01-init.sql          # MariaDB初始化脚本
├── scripts/
│   └── sync_tools/              # 同步工具脚本
│       ├── verify_ai_content_items.py
│       ├── verify_table_compatibility.py
│       └── verify_sync.py
└── tiktok_pm_project/
    ├── settings.py              # Django配置
    └── db_sync/                 # 数据同步模块
        ├── __init__.py
        ├── config.py           # 同步配置
        ├── connection.py       # 数据库连接
        ├── sync_manager.py     # 同步管理器
        ├── scheduler.py        # 定时任务调度
        └── management/
            └── commands/
                ├── sync_db.py   # 手动同步命令
                └── sync_scheduler.py  # 定时任务管理命令
```

### 6.5 相关文件

- [settings.py](file:///home/shenwei/docker/tiktok_pm/tiktok_pm_project/settings.py) - Django配置文件
- [docker-compose.yml](file:///home/shenwei/docker/tiktok_pm/docker-compose.yml) - Docker Compose配置
- [01-init.sql](file:///home/shenwei/docker/tiktok_pm/mariadb/init/01-init.sql) - 数据库初始化脚本
- [sync_manager.py](file:///home/shenwei/docker/tiktok_pm/tiktok_pm_project/db_sync/sync_manager.py) - 同步管理器
- [scheduler.py](file:///home/shenwei/docker/tiktok_pm/tiktok_pm_project/db_sync/scheduler.py) - 定时任务调度器

### 6.6 最佳实践

#### 配置管理

1. **使用环境变量管理配置**
   ```bash
   # 开发环境
   DB_ENV=local
   DB_SYNC_ENABLED=True
   DB_SYNC_INTERVAL=30

   # 生产环境
   DB_ENV=remote
   DB_SYNC_ENABLED=False
   ```

2. **为不同环境创建配置文件**
   ```
   .env.dev          # 开发环境配置
   .env.test         # 测试环境配置
   .env.prod         # 生产环境配置
   ```

3. **使用时加载对应配置**
   ```bash
   cp .env.dev .env
   ```

#### 同步策略

1. **首次同步使用全量同步**
   ```bash
   python manage.py sync_db --type FULL
   ```

2. **日常同步使用增量同步**
   ```bash
   python manage.py sync_db --type INCREMENTAL
   ```

3. **重要数据使用短间隔**
   ```sql
   UPDATE db_sync_config 
   SET priority = 100 
   WHERE table_name IN ('products', 'orders');
   ```

4. **辅助数据使用长间隔**
   ```sql
   UPDATE db_sync_config 
   SET priority = 10 
   WHERE table_name IN ('logs', 'temp_data');
   ```

#### 冲突处理

1. **明确数据权威性**
   ```sql
   -- 远程为主
   UPDATE db_sync_config 
   SET conflict_resolution = 'REMOTE_WINS' 
   WHERE table_name = 'products';

   -- 本地为主
   UPDATE db_sync_config 
   SET conflict_resolution = 'LOCAL_WINS' 
   WHERE table_name = 'local_changes';
   ```

2. **重要数据使用手动处理**
   ```sql
   UPDATE db_sync_config 
   SET conflict_resolution = 'MANUAL' 
   WHERE table_name = 'critical_data';
   ```

#### 监控和日志

1. **定期检查同步日志**
   ```sql
   -- 每天检查失败的同步
   SELECT * FROM db_sync_log 
   WHERE status = 'FAILED' 
     AND start_time >= DATE_SUB(NOW(), INTERVAL 1 DAY);
   ```

2. **设置告警机制**
   - 监控同步失败率
   - 监控同步耗时
   - 监控数据一致性

3. **定期清理日志**
   ```sql
   -- 删除30天前的日志
   DELETE FROM db_sync_log 
   WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
   ```

#### 数据安全

1. **定期备份数据库**
   ```bash
   # 备份本地数据库
   docker-compose exec mariadb mysqldump -u root -p tiktok_products_dev > backup.sql

   # 备份远程数据库
   mysqldump -h 192.168.3.17 -P 3307 -u shenwei -p tiktok_products_dev > backup.sql
   ```

2. **测试恢复流程**
   ```bash
   # 恢复到测试环境
   docker-compose exec -T mariadb mysql -u root -p tiktok_products_dev < backup.sql
   ```

3. **使用强密码**
   ```bash
   # 使用随机生成的强密码
   MARIADB_PASSWORD=$(openssl rand -base64 32)
   ```

#### 性能优化

1. **使用增量同步**
   ```bash
   DB_SYNC_TYPE=INCREMENTAL
   ```

2. **合理设置同步间隔**
   ```bash
   # 根据数据变化频率调整
   DB_SYNC_INTERVAL=60
   ```

3. **批量操作**
   ```sql
   -- 批量更新配置
   UPDATE db_sync_config 
   SET sync_enabled = 1 
   WHERE table_name IN ('table1', 'table2', 'table3');
   ```

4. **使用索引优化查询**
   ```sql
   -- 为同步字段添加索引
   CREATE INDEX idx_updated_at ON products(updated_at);
   ```

### 6.7 安全建议

1. **密码管理**: 使用强密码，避免硬编码
2. **网络隔离**: 限制数据库访问IP
3. **数据备份**: 定期备份数据库
4. **日志审计**: 定期检查同步日志
5. **权限控制**: 最小权限原则

### 6.8 维护操作

#### 数据库备份

```bash
# 备份本地MariaDB
docker-compose exec mariadb mysqldump -u root -p tiktok_products_dev > backup.sql

# 备份远程MySQL
mysqldump -h 192.168.3.17 -P 3307 -u shenwei -p tiktok_products_dev > backup.sql
```

#### 数据库恢复

```bash
# 恢复到本地MariaDB
docker-compose exec -T mariadb mysql -u root -p tiktok_products_dev < backup.sql
```

#### 清理同步日志

```sql
-- 删除30天前的日志
DELETE FROM db_sync_log WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

#### 更新配置

修改 `.env` 文件后，需要重启相应服务:

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart web worker
```

### 6.9 版本历史

- v1.0.0 - 初始版本，支持环境切换和基本同步功能
- v1.1.0 - 添加定时任务和冲突解决策略
- v1.2.0 - 添加测试框架和实时监控
- v1.3.0 - 添加自动故障排除和性能优化

### 6.10 支持与反馈

如遇到问题或有改进建议，请：

1. 查看测试报告中的详细错误信息
2. 启用详细输出和实时监控
3. 检查日志文件
4. 联系技术支持团队

---

**文档版本**: 1.0.0  
**最后更新**: 2026-01-07  
**维护者**: TikTok PM Team

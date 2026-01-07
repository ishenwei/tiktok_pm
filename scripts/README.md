# Scripts 工具目录

本目录包含项目中的所有工具脚本，按功能分类组织。

## 目录结构

```
scripts/
├── db_tools/          # 数据库相关工具
│   ├── base.py       # 数据库工具基类
│   ├── check_connection.py  # 数据库连接检查
│   └── clean_database.py    # 数据库清理工具
├── sync_tools/        # 同步相关工具
│   ├── config_manager.py    # 同步配置管理
│   ├── verify_ai_content_items.py  # AI内容项验证
│   ├── verify_table_compatibility.py  # 表兼容性验证
│   └── verify_sync.py       # 数据同步验证
├── test_tools/        # 测试相关工具
│   ├── check_storage.py      # 数据库存储检查
│   └── run_tests.py          # 测试运行器
└── run_full_process.py  # 完整流程自动化脚本
```

## 使用说明

### 数据库工具 (db_tools)

#### 检查数据库连接

```bash
# 检查本地数据库
python scripts/db_tools/check_connection.py --local

# 检查远程数据库
python scripts/db_tools/check_connection.py --remote

# 检查所有数据库
python scripts/db_tools/check_connection.py --all
```

#### 使用数据库基类

```python
from scripts.db_tools.base import DatabaseInfoTool, SyncConfigTool

# 获取数据库信息
DatabaseInfoTool.print_database_info(use_remote=False)

# 获取同步配置
SyncConfigTool.print_sync_config()

# 获取表行数
count = SyncConfigTool.get_row_count('products', use_remote=False)
```

### 同步工具 (sync_tools)

#### 管理同步配置

```bash
# 显示同步配置
python scripts/sync_tools/config_manager.py --show-config

# 显示指定表结构
python scripts/sync_tools/config_manager.py --table-structure products

# 比较本地和远程表结构
python scripts/sync_tools/config_manager.py --compare-structure products

# 显示所有表行数
python scripts/sync_tools/config_manager.py --show-counts
```

#### 验证AI内容项

```bash
# 验证ai_content_items表的数据一致性
python scripts/sync_tools/verify_ai_content_items.py
```

#### 验证表兼容性

```bash
# 验证ai_content_items表的结构兼容性
python scripts/sync_tools/verify_table_compatibility.py
```

#### 验证数据同步

```bash
# 验证数据完整性和服务访问
python scripts/sync_tools/verify_sync.py
```

### 测试工具 (test_tools)

#### 检查数据库存储

```bash
# 检查指定产品的AI内容存储
python scripts/test_tools/check_storage.py --product-id 1731500998159798308
```

#### 运行测试

```bash
# 运行所有测试
python scripts/test_tools/run_tests.py --type all

# 运行单元测试
python scripts/test_tools/run_tests.py --type unit

# 运行集成测试
python scripts/test_tools/run_tests.py --type integration

# 运行数据库同步测试
python scripts/test_tools/run_tests.py --type db_sync

# 运行特定测试
python scripts/test_tools/run_tests.py --type db_sync --test-name test_sync_products

# 启用详细输出
python scripts/test_tools/run_tests.py --type all --verbose

# 启用实时监控和自动修复
python scripts/test_tools/run_tests.py --type db_sync --monitor --auto-fix
```

## 旧临时文件迁移对照表

| 旧文件名 | 新位置 | 说明 |
|---------|--------|------|
| test_db_connection.py | scripts/db_tools/check_connection.py | 数据库连接检查 |
| check_sync_config.py | scripts/sync_tools/config_manager.py | 同步配置管理 |
| check_sync_config_correct.py | scripts/sync_tools/config_manager.py | 已合并 |
| check_sync_config_full.py | scripts/sync_tools/config_manager.py | 已合并 |
| check_sync_config_structure.py | scripts/sync_tools/config_manager.py | 已合并 |
| check_remote_db.py | scripts/db_tools/check_connection.py | 已合并 |
| check_remote_tables.py | scripts/sync_tools/config_manager.py | 已合并 |
| check_db_storage.py | scripts/test_tools/check_storage.py | 数据库存储检查 |
| run_tests.py | scripts/test_tools/run_tests.py | 测试运行器 |
| add_ai_content_items_to_sync.py | mariadb/init/01-init.sql | 已整合到初始化SQL |
| verify_ai_content_items.py | scripts/sync_tools/verify_ai_content_items.py | AI内容项验证 |
| verify_ai_content_items_compatibility.py | scripts/sync_tools/verify_table_compatibility.py | 表兼容性验证 |
| verify_sync.py | scripts/sync_tools/verify_sync.py | 数据同步验证 |
| test_n8n_callback.py | (已保留) | n8n回调测试 |
| logging_config.py | (已保留) | 日志配置 |
| analyze_logs.py | (已保留) | 日志分析工具 |

## 注意事项

1. 所有脚本都需要在项目根目录下运行
2. 数据库连接配置在 `.env` 文件中
3. 远程数据库连接信息硬编码在 `base.py` 中，生产环境建议使用环境变量
4. 运行测试前请确保数据库连接正常

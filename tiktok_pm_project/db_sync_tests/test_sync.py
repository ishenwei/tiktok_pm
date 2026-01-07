import os
import sys
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.conf import settings
from django.db import connection
from .test_framework import BaseTest, TestStatus
from .monitor import DatabaseMonitor, SyncMonitor
from .troubleshooter import Troubleshooter, IssueType, IssueSeverity


class FullSyncTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
        self.test_data = []
        self.remote_db_config = None
        self.local_db_config = None
    
    def setup(self):
        self.logger.info("设置全量同步测试环境")
        
        self.remote_db_config = {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': settings.REMOTE_DB_NAME,
            'USER': settings.REMOTE_DB_USER,
            'PASSWORD': settings.REMOTE_DB_PASSWORD,
            'HOST': settings.REMOTE_DB_HOST,
            'PORT': settings.REMOTE_DB_PORT,
        }
        
        self.local_db_config = {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': settings.LOCAL_DB_NAME,
            'USER': settings.LOCAL_DB_USER,
            'PASSWORD': settings.LOCAL_DB_PASSWORD,
            'HOST': settings.LOCAL_DB_HOST,
            'PORT': settings.LOCAL_DB_PORT,
        }
        
        self._prepare_test_data()
        self._clear_local_test_data()
    
    def _prepare_test_data(self):
        self.logger.info("准备测试数据")
        
        test_records = []
        for i in range(100):
            record = {
                'name': f'test_user_{i}',
                'email': f'test_user_{i}@example.com',
                'status': random.choice(['active', 'inactive', 'pending']),
                'created_at': datetime.now() - timedelta(days=random.randint(0, 365)),
                'updated_at': datetime.now()
            }
            test_records.append(record)
        
        self.test_data = test_records
        self.logger.info(f"准备了 {len(test_records)} 条测试数据")
    
    def _clear_local_test_data(self):
        self.logger.info("清理本地测试数据")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM auth_user WHERE username LIKE 'test_user_%'")
                deleted = cursor.rowcount
                self.logger.info(f"清理了 {deleted} 条本地测试数据")
        except Exception as e:
            self.logger.warning(f"清理本地测试数据失败: {e}")
    
    def execute(self):
        self.logger.info("开始执行全量同步测试")
        
        self._test_full_sync_remote_to_local()
        self._test_full_sync_local_to_remote()
        self._test_full_sync_data_integrity()
        self._test_full_sync_performance()
        
        self.logger.info("全量同步测试完成")
    
    def _test_full_sync_remote_to_local(self):
        self.logger.info("测试远程到本地全量同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.REMOTE_TO_LOCAL
            
            sync_manager = SyncManager(config)
            
            result = sync_manager.sync_all()
            
            self.logger.info(f"同步结果: {result}")
            
            assert result['success'], "全量同步应该成功"
            assert result['sync_type'] == 'full', "同步类型应该是全量"
            assert result['direction'] == 'remote_to_local', "同步方向应该是远程到本地"
            assert result['total_rows'] > 0, "应该同步了数据"
            
            self.logger.info(f"成功同步了 {result['total_rows']} 行数据")
            
        except Exception as e:
            self.logger.error(f"远程到本地全量同步测试失败: {e}")
            raise
    
    def _test_full_sync_local_to_remote(self):
        self.logger.info("测试本地到远程全量同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.LOCAL_TO_REMOTE
            
            sync_manager = SyncManager(config)
            
            result = sync_manager.sync_all()
            
            self.logger.info(f"同步结果: {result}")
            
            assert result['success'], "全量同步应该成功"
            assert result['sync_type'] == 'full', "同步类型应该是全量"
            assert result['direction'] == 'local_to_remote', "同步方向应该是本地到远程"
            
            self.logger.info(f"成功同步了 {result['total_rows']} 行数据")
            
        except Exception as e:
            self.logger.error(f"本地到远程全量同步测试失败: {e}")
            raise
    
    def _test_full_sync_data_integrity(self):
        self.logger.info("测试全量同步数据完整性")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            result = sync_manager.sync_all()
            
            assert result['success'], "全量同步应该成功"
            
            remote_count = self._get_table_count(self.remote_db_config, 'auth_user')
            local_count = self._get_table_count(self.local_db_config, 'auth_user')
            
            self.logger.info(f"远程数据库记录数: {remote_count}, 本地数据库记录数: {local_count}")
            
            assert remote_count == local_count, f"数据不一致: 远程 {remote_count} != 本地 {local_count}"
            
            self.logger.info("数据完整性验证通过")
            
        except Exception as e:
            self.logger.error(f"数据完整性测试失败: {e}")
            raise
    
    def _test_full_sync_performance(self):
        self.logger.info("测试全量同步性能")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.REMOTE_TO_LOCAL
            
            sync_manager = SyncManager(config)
            
            start_time = time.time()
            result = sync_manager.sync_all()
            end_time = time.time()
            
            duration = end_time - start_time
            
            self.logger.info(f"全量同步耗时: {duration:.2f} 秒")
            self.logger.info(f"同步行数: {result['total_rows']}")
            
            if result['total_rows'] > 0:
                rows_per_second = result['total_rows'] / duration
                self.logger.info(f"同步速度: {rows_per_second:.2f} 行/秒")
                
                assert rows_per_second > 10, f"同步速度过慢: {rows_per_second:.2f} 行/秒"
            
            assert duration < 60, f"全量同步耗时过长: {duration:.2f} 秒"
            
        except Exception as e:
            self.logger.error(f"性能测试失败: {e}")
            raise
    
    def _get_table_count(self, db_config: Dict[str, Any], table_name: str) -> int:
        try:
            import mysql.connector
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count
        except Exception as e:
            self.logger.error(f"获取表记录数失败: {e}")
            return 0


class IncrementalSyncTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
        self.initial_data_count = 0
        self.new_data_count = 0
        self.updated_data_count = 0
    
    def setup(self):
        self.logger.info("设置增量同步测试环境")
        
        self._perform_initial_full_sync()
        self._record_initial_data_count()
    
    def _perform_initial_full_sync(self):
        self.logger.info("执行初始全量同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            self.logger.info(f"初始全量同步完成: {result['total_rows']} 行")
            
        except Exception as e:
            self.logger.error(f"初始全量同步失败: {e}")
            raise
    
    def _record_initial_data_count(self):
        self.logger.info("记录初始数据数量")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                self.initial_data_count = cursor.fetchone()[0]
                self.logger.info(f"初始数据数量: {self.initial_data_count}")
        except Exception as e:
            self.logger.error(f"记录初始数据数量失败: {e}")
            raise
    
    def execute(self):
        self.logger.info("开始执行增量同步测试")
        
        self._test_incremental_sync_new_data()
        self._test_incremental_sync_updated_data()
        self._test_incremental_sync_deleted_data()
        self._test_incremental_sync_performance()
        self._test_incremental_sync_log()
        
        self.logger.info("增量同步测试完成")
    
    def _test_incremental_sync_new_data(self):
        self.logger.info("测试增量同步新增数据")
        
        try:
            self._create_new_test_data(10)
            self.new_data_count = 10
            
            time.sleep(2)
            
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            self.logger.info(f"增量同步结果: {result}")
            
            assert result['success'], "增量同步应该成功"
            assert result['sync_type'] == 'incremental', "同步类型应该是增量"
            
            current_count = self._get_current_data_count()
            expected_count = self.initial_data_count + self.new_data_count
            
            self.logger.info(f"当前数据数量: {current_count}, 期望数量: {expected_count}")
            
            assert current_count >= expected_count, f"数据数量不正确: {current_count} < {expected_count}"
            
            self.logger.info("新增数据增量同步测试通过")
            
        except Exception as e:
            self.logger.error(f"新增数据增量同步测试失败: {e}")
            raise
    
    def _test_incremental_sync_updated_data(self):
        self.logger.info("测试增量同步更新数据")
        
        try:
            self._update_test_data(5)
            self.updated_data_count = 5
            
            time.sleep(2)
            
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            self.logger.info(f"增量同步结果: {result}")
            
            assert result['success'], "增量同步应该成功"
            
            self.logger.info("更新数据增量同步测试通过")
            
        except Exception as e:
            self.logger.error(f"更新数据增量同步测试失败: {e}")
            raise
    
    def _test_incremental_sync_deleted_data(self):
        self.logger.info("测试增量同步删除数据")
        
        try:
            deleted_count = self._delete_test_data(3)
            
            time.sleep(2)
            
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            self.logger.info(f"增量同步结果: {result}")
            
            assert result['success'], "增量同步应该成功"
            
            self.logger.info("删除数据增量同步测试通过")
            
        except Exception as e:
            self.logger.error(f"删除数据增量同步测试失败: {e}")
            raise
    
    def _test_incremental_sync_performance(self):
        self.logger.info("测试增量同步性能")
        
        try:
            self._create_new_test_data(50)
            
            time.sleep(2)
            
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            start_time = time.time()
            result = sync_manager.sync_all()
            end_time = time.time()
            
            duration = end_time - start_time
            
            self.logger.info(f"增量同步耗时: {duration:.2f} 秒")
            self.logger.info(f"同步行数: {result['total_rows']}")
            
            if result['total_rows'] > 0:
                rows_per_second = result['total_rows'] / duration
                self.logger.info(f"同步速度: {rows_per_second:.2f} 行/秒")
                
                assert rows_per_second > 50, f"增量同步速度过慢: {rows_per_second:.2f} 行/秒"
            
            assert duration < 30, f"增量同步耗时过长: {duration:.2f} 秒"
            
            self.logger.info("增量同步性能测试通过")
            
        except Exception as e:
            self.logger.error(f"增量同步性能测试失败: {e}")
            raise
    
    def _test_incremental_sync_log(self):
        self.logger.info("测试增量同步日志记录")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            sync_status = sync_manager.get_sync_status()
            
            self.logger.info(f"同步状态: {sync_status}")
            
            assert 'recent_logs' in sync_status, "应该包含最近的同步日志"
            assert 'table_configs' in sync_status, "应该包含表配置信息"
            
            recent_logs = sync_status['recent_logs']
            assert len(recent_logs) > 0, "应该有同步日志记录"
            
            latest_log = recent_logs[0]
            assert latest_log['sync_type'] == 'incremental', "最新日志应该是增量同步"
            
            self.logger.info("增量同步日志记录测试通过")
            
        except Exception as e:
            self.logger.error(f"增量同步日志记录测试失败: {e}")
            raise
    
    def _create_new_test_data(self, count: int):
        self.logger.info(f"创建 {count} 条新测试数据")
        
        try:
            from django.contrib.auth.models import User
            
            for i in range(count):
                username = f'incremental_test_{int(time.time())}_{i}'
                User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='test123456'
                )
            
            self.logger.info(f"成功创建 {count} 条新测试数据")
            
        except Exception as e:
            self.logger.error(f"创建新测试数据失败: {e}")
            raise
    
    def _update_test_data(self, count: int):
        self.logger.info(f"更新 {count} 条测试数据")
        
        try:
            from django.contrib.auth.models import User
            
            users = User.objects.filter(username__startswith='incremental_test_')[:count]
            
            for user in users:
                user.email = f'updated_{user.username}@example.com'
                user.save()
            
            self.logger.info(f"成功更新 {len(users)} 条测试数据")
            
        except Exception as e:
            self.logger.error(f"更新测试数据失败: {e}")
            raise
    
    def _delete_test_data(self, count: int) -> int:
        self.logger.info(f"删除 {count} 条测试数据")
        
        try:
            from django.contrib.auth.models import User
            
            users = User.objects.filter(username__startswith='incremental_test_')[:count]
            deleted_count = users.count()
            users.delete()
            
            self.logger.info(f"成功删除 {deleted_count} 条测试数据")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"删除测试数据失败: {e}")
            raise
    
    def _get_current_data_count(self) -> int:
        try:
            from django.contrib.auth.models import User
            return User.objects.count()
        except Exception as e:
            self.logger.error(f"获取当前数据数量失败: {e}")
            return 0


class BidirectionalSyncTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
    
    def setup(self):
        self.logger.info("设置双向同步测试环境")
    
    def execute(self):
        self.logger.info("开始执行双向同步测试")
        
        self._test_bidirectional_sync_consistency()
        self._test_bidirectional_sync_conflict_resolution()
        self._test_bidirectional_sync_order()
        
        self.logger.info("双向同步测试完成")
    
    def _test_bidirectional_sync_consistency(self):
        self.logger.info("测试双向同步数据一致性")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            assert result['success'], "双向同步应该成功"
            assert result['direction'] == 'both', "同步方向应该是双向"
            
            self.logger.info("双向同步数据一致性测试通过")
            
        except Exception as e:
            self.logger.error(f"双向同步数据一致性测试失败: {e}")
            raise
    
    def _test_bidirectional_sync_conflict_resolution(self):
        self.logger.info("测试双向同步冲突解决")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection, ConflictResolution
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            config.conflict_resolution = ConflictResolution.LAST_WRITE_WINS
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            assert result['success'], "双向同步应该成功"
            
            self.logger.info("双向同步冲突解决测试通过")
            
        except Exception as e:
            self.logger.error(f"双向同步冲突解决测试失败: {e}")
            raise
    
    def _test_bidirectional_sync_order(self):
        self.logger.info("测试双向同步顺序")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            assert result['success'], "双向同步应该成功"
            
            if 'tables' in result:
                for table_result in result['tables']:
                    assert 'remote_to_local' in table_result or 'local_to_remote' in table_result, \
                        f"表 {table_result['table_name']} 应该有同步方向信息"
            
            self.logger.info("双向同步顺序测试通过")
            
        except Exception as e:
            self.logger.error(f"双向同步顺序测试失败: {e}")
            raise


class SyncLogTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
    
    def setup(self):
        self.logger.info("设置同步日志测试环境")
    
    def execute(self):
        self.logger.info("开始执行同步日志测试")
        
        self._test_sync_log_creation()
        self._test_sync_log_update()
        self._test_sync_log_query()
        self._test_sync_log_error_handling()
        
        self.logger.info("同步日志测试完成")
    
    def _test_sync_log_creation(self):
        self.logger.info("测试同步日志创建")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            assert result['success'], "同步应该成功"
            
            sync_status = sync_manager.get_sync_status()
            assert 'recent_logs' in sync_status, "应该有同步日志"
            assert len(sync_status['recent_logs']) > 0, "应该有日志记录"
            
            self.logger.info("同步日志创建测试通过")
            
        except Exception as e:
            self.logger.error(f"同步日志创建测试失败: {e}")
            raise
    
    def _test_sync_log_update(self):
        self.logger.info("测试同步日志更新")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            assert result['success'], "同步应该成功"
            assert 'end_time' in result, "应该有结束时间"
            assert 'duration' in result, "应该有持续时间"
            
            self.logger.info("同步日志更新测试通过")
            
        except Exception as e:
            self.logger.error(f"同步日志更新测试失败: {e}")
            raise
    
    def _test_sync_log_query(self):
        self.logger.info("测试同步日志查询")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            sync_manager.sync_all()
            
            sync_status = sync_manager.get_sync_status()
            
            assert 'recent_logs' in sync_status, "应该有同步日志"
            assert len(sync_status['recent_logs']) > 0, "应该有日志记录"
            
            latest_log = sync_status['recent_logs'][0]
            assert 'sync_type' in latest_log, "日志应该包含同步类型"
            assert 'direction' in latest_log, "日志应该包含同步方向"
            assert 'status' in latest_log, "日志应该包含状态"
            
            self.logger.info("同步日志查询测试通过")
            
        except Exception as e:
            self.logger.error(f"同步日志查询测试失败: {e}")
            raise
    
    def _test_sync_log_error_handling(self):
        self.logger.info("测试同步日志错误处理")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            if not result['success']:
                assert 'errors' in result, "失败的结果应该包含错误信息"
                assert len(result['errors']) > 0, "应该有错误记录"
                
                sync_status = sync_manager.get_sync_status()
                latest_log = sync_status['recent_logs'][0]
                
                assert latest_log['status'] == 'FAILED', "日志状态应该是失败"
                assert 'error_message' in latest_log, "日志应该包含错误消息"
            
            self.logger.info("同步日志错误处理测试通过")
            
        except Exception as e:
            self.logger.error(f"同步日志错误处理测试失败: {e}")
            raise

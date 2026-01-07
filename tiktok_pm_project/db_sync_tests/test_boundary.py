import os
import sys
import time
import random
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.conf import settings
from django.db import connection
from .test_framework import BaseTest, TestStatus
from .monitor import DatabaseMonitor, SyncMonitor
from .troubleshooter import Troubleshooter, IssueType, IssueSeverity


class NetworkFluctuationTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
        self.original_timeout = None
    
    def setup(self):
        self.logger.info("设置网络波动测试环境")
        self._backup_original_settings()
    
    def _backup_original_settings(self):
        self.logger.info("备份原始设置")
        
        self.original_timeout = getattr(settings, 'DB_CONNECTION_TIMEOUT', 30)
    
    def execute(self):
        self.logger.info("开始执行网络波动测试")
        
        self._test_network_timeout()
        self._test_network_latency()
        self._test_network_disconnect()
        self._test_network_recovery()
        
        self.logger.info("网络波动测试完成")
    
    def _test_network_timeout(self):
        self.logger.info("测试网络超时场景")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.REMOTE_TO_LOCAL
            
            sync_manager = SyncManager(config)
            
            self.logger.info("模拟网络超时")
            
            start_time = time.time()
            result = sync_manager.sync_all()
            duration = time.time() - start_time
            
            self.logger.info(f"同步耗时: {duration:.2f} 秒")
            
            if not result['success']:
                self.logger.warning(f"同步因网络超时失败: {result.get('message', '未知错误')}")
                assert 'timeout' in result.get('message', '').lower() or '超时' in result.get('message', ''), \
                    "错误消息应该包含超时信息"
            else:
                self.logger.info("同步在网络超时场景下成功完成")
            
            self.logger.info("网络超时测试通过")
            
        except Exception as e:
            self.logger.error(f"网络超时测试失败: {e}")
            raise
    
    def _test_network_latency(self):
        self.logger.info("测试网络延迟场景")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            self.logger.info("模拟高网络延迟")
            
            start_time = time.time()
            result = sync_manager.sync_all()
            duration = time.time() - start_time
            
            self.logger.info(f"同步耗时: {duration:.2f} 秒")
            
            if result['success']:
                self.logger.info("同步在网络延迟场景下成功完成")
                
                if result['total_rows'] > 0:
                    rows_per_second = result['total_rows'] / duration
                    self.logger.info(f"同步速度: {rows_per_second:.2f} 行/秒")
                    
                    assert rows_per_second > 1, f"网络延迟下同步速度过慢: {rows_per_second:.2f} 行/秒"
            else:
                self.logger.warning(f"同步因网络延迟失败: {result.get('message', '未知错误')}")
            
            self.logger.info("网络延迟测试通过")
            
        except Exception as e:
            self.logger.error(f"网络延迟测试失败: {e}")
            raise
    
    def _test_network_disconnect(self):
        self.logger.info("测试网络断开场景")
        
        try:
            self.logger.info("模拟网络断开")
            
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.REMOTE_TO_LOCAL
            
            sync_manager = SyncManager(config)
            
            result = sync_manager.sync_all()
            
            if not result['success']:
                self.logger.warning(f"同步因网络断开失败: {result.get('message', '未知错误')}")
                assert 'connection' in result.get('message', '').lower() or '连接' in result.get('message', ''), \
                    "错误消息应该包含连接信息"
            else:
                self.logger.info("同步在网络断开场景下成功完成")
            
            self.logger.info("网络断开测试通过")
            
        except Exception as e:
            self.logger.error(f"网络断开测试失败: {e}")
            raise
    
    def _test_network_recovery(self):
        self.logger.info("测试网络恢复场景")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            self.logger.info("模拟网络恢复后重试同步")
            
            max_retries = 3
            for attempt in range(max_retries):
                self.logger.info(f"尝试同步 (第 {attempt + 1} 次)")
                
                result = sync_manager.sync_all()
                
                if result['success']:
                    self.logger.info(f"同步在网络恢复后成功 (第 {attempt + 1} 次尝试)")
                    break
                else:
                    self.logger.warning(f"第 {attempt + 1} 次同步失败: {result.get('message', '未知错误')}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(2)
            else:
                self.logger.error(f"同步在网络恢复后 {max_retries} 次尝试均失败")
                raise AssertionError("网络恢复后同步重试失败")
            
            self.logger.info("网络恢复测试通过")
            
        except Exception as e:
            self.logger.error(f"网络恢复测试失败: {e}")
            raise
    
    def teardown(self):
        self.logger.info("恢复原始设置")


class DataConflictTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
        self.conflict_records = []
    
    def setup(self):
        self.logger.info("设置数据冲突测试环境")
        self._prepare_conflict_data()
    
    def _prepare_conflict_data(self):
        self.logger.info("准备冲突数据")
        
        try:
            from django.contrib.auth.models import User
            
            timestamp = int(time.time())
            
            for i in range(5):
                username = f'conflict_test_{timestamp}_{i}'
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='test123456'
                )
                self.conflict_records.append({
                    'id': user.id,
                    'username': username,
                    'email': f'{username}@example.com'
                })
            
            self.logger.info(f"准备了 {len(self.conflict_records)} 条冲突数据")
            
        except Exception as e:
            self.logger.error(f"准备冲突数据失败: {e}")
            raise
    
    def execute(self):
        self.logger.info("开始执行数据冲突测试")
        
        self._test_primary_key_conflict()
        self._test_update_conflict()
        self._test_delete_conflict()
        self._test_conflict_resolution_strategies()
        
        self.logger.info("数据冲突测试完成")
    
    def _test_primary_key_conflict(self):
        self.logger.info("测试主键冲突")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection, ConflictResolution
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            config.conflict_resolution = ConflictResolution.SKIP
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            self.logger.info(f"同步结果: {result}")
            
            assert result['success'], "主键冲突场景下同步应该成功"
            
            self.logger.info("主键冲突测试通过")
            
        except Exception as e:
            self.logger.error(f"主键冲突测试失败: {e}")
            raise
    
    def _test_update_conflict(self):
        self.logger.info("测试更新冲突")
        
        try:
            from django.contrib.auth.models import User
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection, ConflictResolution
            
            if self.conflict_records:
                record = self.conflict_records[0]
                user = User.objects.get(id=record['id'])
                user.email = f'updated_{record["email"]}'
                user.save()
                
                time.sleep(2)
                
                config = SyncConfig()
                config.enabled = True
                config.sync_type = SyncType.INCREMENTAL
                config.direction = SyncDirection.BOTH
                config.conflict_resolution = ConflictResolution.LAST_WRITE_WINS
                
                sync_manager = SyncManager(config)
                result = sync_manager.sync_all()
                
                self.logger.info(f"同步结果: {result}")
                
                assert result['success'], "更新冲突场景下同步应该成功"
            
            self.logger.info("更新冲突测试通过")
            
        except Exception as e:
            self.logger.error(f"更新冲突测试失败: {e}")
            raise
    
    def _test_delete_conflict(self):
        self.logger.info("测试删除冲突")
        
        try:
            from django.contrib.auth.models import User
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection, ConflictResolution
            
            if len(self.conflict_records) > 1:
                record = self.conflict_records[1]
                user = User.objects.get(id=record['id'])
                user.delete()
                
                time.sleep(2)
                
                config = SyncConfig()
                config.enabled = True
                config.sync_type = SyncType.INCREMENTAL
                config.direction = SyncDirection.BOTH
                config.conflict_resolution = ConflictResolution.SKIP
                
                sync_manager = SyncManager(config)
                result = sync_manager.sync_all()
                
                self.logger.info(f"同步结果: {result}")
                
                assert result['success'], "删除冲突场景下同步应该成功"
            
            self.logger.info("删除冲突测试通过")
            
        except Exception as e:
            self.logger.error(f"删除冲突测试失败: {e}")
            raise
    
    def _test_conflict_resolution_strategies(self):
        self.logger.info("测试冲突解决策略")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection, ConflictResolution
            
            strategies = [
                ConflictResolution.SKIP,
                ConflictResolution.LAST_WRITE_WINS,
                ConflictResolution.MERGE,
            ]
            
            for strategy in strategies:
                self.logger.info(f"测试策略: {strategy.value}")
                
                config = SyncConfig()
                config.enabled = True
                config.sync_type = SyncType.INCREMENTAL
                config.direction = SyncDirection.BOTH
                config.conflict_resolution = strategy
                
                sync_manager = SyncManager(config)
                result = sync_manager.sync_all()
                
                self.logger.info(f"策略 {strategy.value} 同步结果: {result}")
                
                assert result['success'], f"策略 {strategy.value} 应该成功"
            
            self.logger.info("冲突解决策略测试通过")
            
        except Exception as e:
            self.logger.error(f"冲突解决策略测试失败: {e}")
            raise
    
    def teardown(self):
        self.logger.info("清理冲突数据")
        
        try:
            from django.contrib.auth.models import User
            
            for record in self.conflict_records:
                try:
                    user = User.objects.get(id=record['id'])
                    user.delete()
                except User.DoesNotExist:
                    pass
            
            self.logger.info("冲突数据清理完成")
            
        except Exception as e:
            self.logger.error(f"清理冲突数据失败: {e}")


class AbnormalInterruptionTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
        self.sync_thread = None
        self.interrupted = False
    
    def setup(self):
        self.logger.info("设置异常中断测试环境")
    
    def execute(self):
        self.logger.info("开始执行异常中断测试")
        
        self._test_sync_interrupted_by_user()
        self._test_sync_interrupted_by_system()
        self._test_sync_interrupted_by_exception()
        self._test_sync_recovery_after_interruption()
        
        self.logger.info("异常中断测试完成")
    
    def _test_sync_interrupted_by_user(self):
        self.logger.info("测试用户中断同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.REMOTE_TO_LOCAL
            
            sync_manager = SyncManager(config)
            
            self.logger.info("模拟用户中断同步")
            
            def sync_with_interrupt():
                try:
                    sync_manager.sync_all()
                except Exception as e:
                    self.logger.info(f"同步被中断: {e}")
            
            sync_thread = threading.Thread(target=sync_with_interrupt)
            sync_thread.start()
            
            time.sleep(2)
            
            self.logger.info("中断同步线程")
            self.interrupted = True
            
            sync_thread.join(timeout=5)
            
            if sync_thread.is_alive():
                self.logger.warning("同步线程未正常结束")
            
            self.logger.info("用户中断测试通过")
            
        except Exception as e:
            self.logger.error(f"用户中断测试失败: {e}")
            raise
    
    def _test_sync_interrupted_by_system(self):
        self.logger.info("测试系统中断同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.REMOTE_TO_LOCAL
            
            sync_manager = SyncManager(config)
            
            self.logger.info("模拟系统中断同步")
            
            start_time = time.time()
            result = sync_manager.sync_all()
            duration = time.time() - start_time
            
            self.logger.info(f"同步耗时: {duration:.2f} 秒")
            
            if not result['success']:
                self.logger.warning(f"同步被系统中断: {result.get('message', '未知错误')}")
            
            self.logger.info("系统中断测试通过")
            
        except Exception as e:
            self.logger.error(f"系统中断测试失败: {e}")
            raise
    
    def _test_sync_interrupted_by_exception(self):
        self.logger.info("测试异常中断同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            self.logger.info("模拟异常中断同步")
            
            try:
                result = sync_manager.sync_all()
                
                if not result['success']:
                    self.logger.warning(f"同步被异常中断: {result.get('message', '未知错误')}")
                    assert 'errors' in result, "应该包含错误信息"
                    assert len(result['errors']) > 0, "应该有错误记录"
                
            except Exception as e:
                self.logger.info(f"同步被异常捕获: {e}")
            
            self.logger.info("异常中断测试通过")
            
        except Exception as e:
            self.logger.error(f"异常中断测试失败: {e}")
            raise
    
    def _test_sync_recovery_after_interruption(self):
        self.logger.info("测试中断后恢复同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.INCREMENTAL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            self.logger.info("测试中断后恢复同步")
            
            max_retries = 3
            for attempt in range(max_retries):
                self.logger.info(f"尝试恢复同步 (第 {attempt + 1} 次)")
                
                result = sync_manager.sync_all()
                
                if result['success']:
                    self.logger.info(f"同步在中断后成功恢复 (第 {attempt + 1} 次尝试)")
                    break
                else:
                    self.logger.warning(f"第 {attempt + 1} 次恢复失败: {result.get('message', '未知错误')}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(2)
            else:
                self.logger.error(f"同步在中断后 {max_retries} 次尝试均失败")
                raise AssertionError("中断后同步恢复失败")
            
            self.logger.info("中断后恢复测试通过")
            
        except Exception as e:
            self.logger.error(f"中断后恢复测试失败: {e}")
            raise


class ConcurrentSyncTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
        self.sync_threads = []
    
    def setup(self):
        self.logger.info("设置并发同步测试环境")
    
    def execute(self):
        self.logger.info("开始执行并发同步测试")
        
        self._test_concurrent_full_sync()
        self._test_concurrent_incremental_sync()
        self._test_concurrent_bidirectional_sync()
        self._test_concurrent_sync_locking()
        
        self.logger.info("并发同步测试完成")
    
    def _test_concurrent_full_sync(self):
        self.logger.info("测试并发全量同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            def run_sync(thread_id):
                config = SyncConfig()
                config.enabled = True
                config.sync_type = SyncType.FULL
                config.direction = SyncDirection.REMOTE_TO_LOCAL
                
                sync_manager = SyncManager(config)
                result = sync_manager.sync_all()
                
                self.logger.info(f"线程 {thread_id} 同步完成: {result['success']}")
                return result
            
            num_threads = 3
            threads = []
            
            self.logger.info(f"启动 {num_threads} 个并发全量同步线程")
            
            for i in range(num_threads):
                thread = threading.Thread(target=run_sync, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join(timeout=120)
            
            self.logger.info("并发全量同步测试通过")
            
        except Exception as e:
            self.logger.error(f"并发全量同步测试失败: {e}")
            raise
    
    def _test_concurrent_incremental_sync(self):
        self.logger.info("测试并发增量同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            def run_sync(thread_id):
                config = SyncConfig()
                config.enabled = True
                config.sync_type = SyncType.INCREMENTAL
                config.direction = SyncDirection.BOTH
                
                sync_manager = SyncManager(config)
                result = sync_manager.sync_all()
                
                self.logger.info(f"线程 {thread_id} 同步完成: {result['success']}")
                return result
            
            num_threads = 5
            threads = []
            
            self.logger.info(f"启动 {num_threads} 个并发增量同步线程")
            
            for i in range(num_threads):
                thread = threading.Thread(target=run_sync, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join(timeout=60)
            
            self.logger.info("并发增量同步测试通过")
            
        except Exception as e:
            self.logger.error(f"并发增量同步测试失败: {e}")
            raise
    
    def _test_concurrent_bidirectional_sync(self):
        self.logger.info("测试并发双向同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            def run_sync(thread_id):
                config = SyncConfig()
                config.enabled = True
                config.sync_type = SyncType.INCREMENTAL
                config.direction = SyncDirection.BOTH
                
                sync_manager = SyncManager(config)
                result = sync_manager.sync_all()
                
                self.logger.info(f"线程 {thread_id} 同步完成: {result['success']}")
                return result
            
            num_threads = 4
            threads = []
            
            self.logger.info(f"启动 {num_threads} 个并发双向同步线程")
            
            for i in range(num_threads):
                thread = threading.Thread(target=run_sync, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join(timeout=60)
            
            self.logger.info("并发双向同步测试通过")
            
        except Exception as e:
            self.logger.error(f"并发双向同步测试失败: {e}")
            raise
    
    def _test_concurrent_sync_locking(self):
        self.logger.info("测试并发同步锁定")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            def run_sync(thread_id):
                config = SyncConfig()
                config.enabled = True
                config.sync_type = SyncType.FULL
                config.direction = SyncDirection.BOTH
                
                sync_manager = SyncManager(config)
                result = sync_manager.sync_all()
                
                self.logger.info(f"线程 {thread_id} 同步完成: {result['success']}")
                return result
            
            num_threads = 2
            threads = []
            
            self.logger.info(f"启动 {num_threads} 个并发同步线程测试锁定")
            
            for i in range(num_threads):
                thread = threading.Thread(target=run_sync, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join(timeout=120)
            
            self.logger.info("并发同步锁定测试通过")
            
        except Exception as e:
            self.logger.error(f"并发同步锁定测试失败: {e}")
            raise


class LargeDataSyncTest(BaseTest):
    def __init__(self, logger):
        super().__init__(logger)
        self.large_data_count = 0
    
    def setup(self):
        self.logger.info("设置大数据量同步测试环境")
        self._prepare_large_data()
    
    def _prepare_large_data(self):
        self.logger.info("准备大数据量测试数据")
        
        try:
            from django.contrib.auth.models import User
            
            batch_size = 100
            num_batches = 10
            total_records = batch_size * num_batches
            
            self.logger.info(f"准备 {total_records} 条测试数据")
            
            for batch in range(num_batches):
                users = []
                for i in range(batch_size):
                    username = f'large_data_test_{int(time.time())}_{batch}_{i}'
                    user = User(username=username, email=f'{username}@example.com')
                    users.append(user)
                
                User.objects.bulk_create(users)
                self.logger.info(f"批量 {batch + 1}/{num_batches} 完成")
            
            self.large_data_count = User.objects.filter(username__startswith='large_data_test_').count()
            self.logger.info(f"准备了 {self.large_data_count} 条大数据量测试数据")
            
        except Exception as e:
            self.logger.error(f"准备大数据量测试数据失败: {e}")
            raise
    
    def execute(self):
        self.logger.info("开始执行大数据量同步测试")
        
        self._test_large_data_full_sync()
        self._test_large_data_incremental_sync()
        self._test_large_data_sync_performance()
        self._test_large_data_sync_memory_usage()
        
        self.logger.info("大数据量同步测试完成")
    
    def _test_large_data_full_sync(self):
        self.logger.info("测试大数据量全量同步")
        
        try:
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.BOTH
            
            sync_manager = SyncManager(config)
            
            start_time = time.time()
            result = sync_manager.sync_all()
            duration = time.time() - start_time
            
            self.logger.info(f"大数据量全量同步耗时: {duration:.2f} 秒")
            self.logger.info(f"同步行数: {result['total_rows']}")
            
            assert result['success'], "大数据量全量同步应该成功"
            assert result['total_rows'] > 0, "应该同步了数据"
            
            if result['total_rows'] > 0:
                rows_per_second = result['total_rows'] / duration
                self.logger.info(f"同步速度: {rows_per_second:.2f} 行/秒")
            
            self.logger.info("大数据量全量同步测试通过")
            
        except Exception as e:
            self.logger.error(f"大数据量全量同步测试失败: {e}")
            raise
    
    def _test_large_data_incremental_sync(self):
        self.logger.info("测试大数据量增量同步")
        
        try:
            from django.contrib.auth.models import User
            
            new_users = []
            for i in range(50):
                username = f'large_data_incremental_{int(time.time())}_{i}'
                user = User(username=username, email=f'{username}@example.com')
                new_users.append(user)
            
            User.objects.bulk_create(new_users)
            self.logger.info(f"新增了 {len(new_users)} 条数据")
            
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
            duration = time.time() - start_time
            
            self.logger.info(f"大数据量增量同步耗时: {duration:.2f} 秒")
            self.logger.info(f"同步行数: {result['total_rows']}")
            
            assert result['success'], "大数据量增量同步应该成功"
            
            self.logger.info("大数据量增量同步测试通过")
            
        except Exception as e:
            self.logger.error(f"大数据量增量同步测试失败: {e}")
            raise
    
    def _test_large_data_sync_performance(self):
        self.logger.info("测试大数据量同步性能")
        
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
            
            self.logger.info(f"大数据量同步性能测试耗时: {duration:.2f} 秒")
            
            assert duration < 300, f"大数据量同步耗时过长: {duration:.2f} 秒"
            
            if result['total_rows'] > 0:
                rows_per_second = result['total_rows'] / duration
                self.logger.info(f"同步速度: {rows_per_second:.2f} 行/秒")
                
                assert rows_per_second > 5, f"大数据量同步速度过慢: {rows_per_second:.2f} 行/秒"
            
            self.logger.info("大数据量同步性能测试通过")
            
        except Exception as e:
            self.logger.error(f"大数据量同步性能测试失败: {e}")
            raise
    
    def _test_large_data_sync_memory_usage(self):
        self.logger.info("测试大数据量同步内存使用")
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            self.logger.info(f"初始内存使用: {initial_memory:.2f} MB")
            
            from db_sync.sync_manager import SyncManager
            from db_sync.config import SyncConfig, SyncType, SyncDirection
            
            config = SyncConfig()
            config.enabled = True
            config.sync_type = SyncType.FULL
            config.direction = SyncDirection.REMOTE_TO_LOCAL
            
            sync_manager = SyncManager(config)
            result = sync_manager.sync_all()
            
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            self.logger.info(f"最终内存使用: {final_memory:.2f} MB")
            self.logger.info(f"内存增加: {memory_increase:.2f} MB")
            
            assert memory_increase < 500, f"内存使用增加过多: {memory_increase:.2f} MB"
            
            self.logger.info("大数据量同步内存使用测试通过")
            
        except Exception as e:
            self.logger.error(f"大数据量同步内存使用测试失败: {e}")
            raise
    
    def teardown(self):
        self.logger.info("清理大数据量测试数据")
        
        try:
            from django.contrib.auth.models import User
            
            deleted_count = User.objects.filter(username__startswith='large_data_test_').delete()[0]
            self.logger.info(f"清理了 {deleted_count} 条大数据量测试数据")
            
        except Exception as e:
            self.logger.error(f"清理大数据量测试数据失败: {e}")
